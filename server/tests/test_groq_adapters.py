import httpx
import pytest
from google.api_core.exceptions import ResourceExhausted
from groq import APIConnectionError, AuthenticationError, RateLimitError
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.agent.langchain_agent import LangChainAgent
from app.agent.tools.registry import ToolRegistry
from app.core.config import Settings
from app.core.exceptions import ModelProviderError, ModelRateLimitedError
from app.domain.models import ToolResult
from app.domain.ports import LLMClient
from app.infrastructure import model_calls
from app.infrastructure.chat_models.registry import create_chat_model
from app.infrastructure.groq.errors import groq_errors
from app.infrastructure.llm.fallback import FallbackLLMClient
from app.infrastructure.llm.groq import GroqLLMClient
from app.infrastructure.llm.registry import create_llm_client

_REQUEST = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def status_error(cls: type, status: int, message: str) -> Exception:
    return cls(message, response=httpx.Response(status, request=_REQUEST), body=None)


def settings(**overrides) -> Settings:
    base = {"groq_api_key": SecretStr("k"), "gemini_api_key": SecretStr("k"), "_env_file": None}
    return Settings(**{**base, **overrides})


def reply(text: str) -> ChatResult:
    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


# --- error translation ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raised", "expected", "text"),
    [
        (status_error(RateLimitError, 429, "slow down"), ModelRateLimitedError, "rate limit"),
        (status_error(AuthenticationError, 401, "bad key"), ModelProviderError, "GROQ_API_KEY"),
        (APIConnectionError(request=_REQUEST), ModelProviderError, "Groq failed"),
    ],
)
def test_groq_failures_become_the_apps_own_errors(
    raised: Exception, expected: type, text: str
) -> None:
    with pytest.raises(expected, match=text), groq_errors("testing"):
        raise raised


# --- the real chat model class, with the SDK call replaced ------------------------------------


@pytest.mark.anyio
async def test_the_groq_client_sends_the_prompt_and_counts_the_call(monkeypatch) -> None:
    seen: list[list] = []

    async def fake_agenerate(self, messages, *args, **kwargs):
        seen.append(messages)
        return reply("from groq")

    monkeypatch.setattr(ChatGroq, "_agenerate", fake_agenerate)
    client = GroqLLMClient.from_settings(settings(groq_model="m-1"))
    before = model_calls.snapshot()

    assert isinstance(client, LLMClient)
    assert await client.generate("q", system="be brief") == "from groq"
    assert [m.content for m in seen[0]] == ["be brief", "q"]
    assert model_calls.since(before) == {"groq:chat:m-1": 1}


# --- switching provider on rate limits ---------------------------------------------------------


def gemini_always_rate_limited(monkeypatch) -> None:
    async def fake_agenerate(self, messages, *args, **kwargs):
        raise ResourceExhausted("daily quota")

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_agenerate", fake_agenerate)


def groq_answers(monkeypatch, text: str = "from groq") -> None:
    async def fake_agenerate(self, messages, *args, **kwargs):
        return reply(text)

    monkeypatch.setattr(ChatGroq, "_agenerate", fake_agenerate)


@pytest.mark.anyio
async def test_text_generation_moves_to_groq_when_both_gemini_models_are_rate_limited(
    monkeypatch,
) -> None:
    gemini_always_rate_limited(monkeypatch)
    groq_answers(monkeypatch)
    client = create_llm_client(settings(llm_provider="gemini", llm_fallback_provider="groq"))
    before = model_calls.snapshot()

    assert await client.generate("q") == "from groq"
    kinds = sorted(key.split(":")[0] for key in model_calls.since(before))
    assert kinds == ["gemini", "gemini", "groq"]  # main, Gemini fallback, then Groq


@pytest.mark.anyio
async def test_other_failures_do_not_switch_provider() -> None:
    class Failing:
        async def generate(self, prompt: str, *, system: str | None = None) -> str:
            raise ModelProviderError("bad request")

    class Backup:
        called = False

        async def generate(self, prompt: str, *, system: str | None = None) -> str:
            Backup.called = True
            return "backup"

    with pytest.raises(ModelProviderError):
        await FallbackLLMClient(Failing(), Backup()).generate("q")
    assert not Backup.called


class EchoTool:
    name = "retrieve_and_answer"
    description = "Answers questions about the project."

    async def run(self, input_text: str) -> ToolResult:
        return ToolResult(content=f"answer to {input_text}")


@pytest.mark.anyio
async def test_the_agent_moves_to_groq_when_gemini_is_rate_limited(monkeypatch) -> None:
    gemini_always_rate_limited(monkeypatch)

    async def groq_calls_the_tool(self, messages, *args, **kwargs):
        call = {"name": "retrieve_and_answer", "args": {"input": "setup"}, "id": "c1"}
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[call]))]
        )

    monkeypatch.setattr(ChatGroq, "_agenerate", groq_calls_the_tool)
    chat_model = create_chat_model(settings(llm_provider="gemini", llm_fallback_provider="groq"))
    agent = LangChainAgent(ToolRegistry([EchoTool()]), chat_model)

    result = await agent.run("How do I set up?")

    assert result.content == "answer to setup"
    assert result.tools_used == ("retrieve_and_answer",)
