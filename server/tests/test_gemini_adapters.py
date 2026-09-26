"""The Gemini adapters, offline: the SDK boundary is replaced by fakes, so no key or network."""

from typing import Any

import pytest
from google.api_core.exceptions import InternalServerError, ResourceExhausted, Unauthenticated
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai._common import GoogleGenerativeAIError
from pydantic import SecretStr

from app.agent.langchain_agent import LangChainAgent
from app.agent.tools.registry import ToolRegistry
from app.core.config import Settings
from app.core.exceptions import ModelProviderError, ModelRateLimitedError
from app.domain.models import ToolResult
from app.domain.ports import Embedder, ImageCaptioner, LLMClient
from app.infrastructure import model_calls
from app.infrastructure.captioning.gemini import GeminiImageCaptioner
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.embeddings.gemini import GeminiEmbedder
from app.infrastructure.gemini.chat import build_gemini_chat
from app.infrastructure.gemini.errors import gemini_errors
from app.infrastructure.llm.chat_client import message_text
from app.infrastructure.llm.gemini import GeminiLLMClient


class ScriptedChat(BaseChatModel):
    """Records the messages it gets and replies with a fixed content (a string or content parts)."""

    reply: Any = "ok"
    received: list = []

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        self.received.append(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=self.reply))])


class FakeEmbeddingsClient:
    def __init__(self) -> None:
        self.document_calls: list[list[str]] = []

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls.append(texts)
        return [[float(len(text))] for text in texts]

    async def aembed_query(self, text: str) -> list[float]:
        return [1.0]


def settings(**overrides) -> Settings:
    return Settings(gemini_api_key=SecretStr("test-key"), _env_file=None, **overrides)


# --- text extraction -------------------------------------------------------------------------


def test_message_text_reads_a_plain_string() -> None:
    assert message_text(AIMessage(content="  Run npm install.  ")) == "Run npm install."


def test_message_text_joins_text_parts_and_skips_the_rest() -> None:
    message = AIMessage(
        content=[
            {"type": "text", "text": "Run "},
            {"type": "thinking", "thinking": "hidden"},
            "npm ",
            {"type": "text", "text": "install."},
        ]
    )
    assert message_text(message) == "Run npm install."


# --- LLM client and captioner -----------------------------------------------------------------


@pytest.mark.anyio
async def test_llm_client_sends_system_and_prompt_and_returns_the_text() -> None:
    chat = ScriptedChat(reply="An answer.", received=[])
    client = GeminiLLMClient(chat)

    assert isinstance(client, LLMClient)
    assert await client.generate("The question", system="Be brief.") == "An answer."
    [[system, human]] = chat.received
    assert isinstance(system, SystemMessage) and system.content == "Be brief."
    assert isinstance(human, HumanMessage) and human.content == "The question"


@pytest.mark.anyio
async def test_llm_client_without_a_system_prompt_sends_only_the_prompt() -> None:
    chat = ScriptedChat(received=[])

    await GeminiLLMClient(chat).generate("Just this")

    [[only]] = chat.received
    assert isinstance(only, HumanMessage)


@pytest.mark.anyio
async def test_captioner_sends_the_image_inline_with_the_instructions() -> None:
    chat = ScriptedChat(reply="A diagram: API -> database.", received=[])
    captioner = GeminiImageCaptioner(chat)

    assert isinstance(captioner, ImageCaptioner)
    assert await captioner.caption(b"\x89PNG", "image/png") == "A diagram: API -> database."
    [[message]] = chat.received
    text_part, image_part = message.content
    assert "diagram" in text_part["text"]
    assert image_part == {"type": "image_url", "image_url": "data:image/png;base64,iVBORw=="}


# --- embedder ---------------------------------------------------------------------------------


def make_embedder(tokens_per_minute: int = 30_000):
    client, sleeps = FakeEmbeddingsClient(), []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    embedder = GeminiEmbedder(
        client, "gemini-embedding-001", tokens_per_minute=tokens_per_minute, sleep=fake_sleep
    )
    return embedder, client, sleeps


def test_embedder_satisfies_the_port() -> None:
    embedder, _, _ = make_embedder()
    assert isinstance(embedder, Embedder)


@pytest.mark.anyio
async def test_a_small_document_is_one_request_with_no_pause() -> None:
    embedder, client, sleeps = make_embedder()

    vectors = await embedder.embed_documents(["a" * 30, "b" * 60])

    assert vectors == [[30.0], [60.0]]
    assert len(client.document_calls) == 1
    assert sleeps == []


@pytest.mark.anyio
async def test_a_large_document_is_split_into_paced_groups_in_order() -> None:
    # Budget = 80% of 100 tokens = 80; each 150-char text estimates at 51 tokens -> one per group.
    embedder, client, sleeps = make_embedder(tokens_per_minute=100)
    texts = ["x" * 150, "y" * 150, "z" * 150]
    before = model_calls.snapshot()

    vectors = await embedder.embed_documents(texts)

    assert client.document_calls == [[texts[0]], [texts[1]], [texts[2]]]
    assert sleeps == [60.0, 60.0]
    assert vectors == [[150.0], [150.0], [150.0]]
    assert model_calls.since(before) == {"gemini:embed:gemini-embedding-001": 3}


@pytest.mark.anyio
async def test_embedder_errors_become_app_errors() -> None:
    class Failing(FakeEmbeddingsClient):
        async def aembed_query(self, text: str) -> list[float]:
            cause = ResourceExhausted("quota")
            raise GoogleGenerativeAIError("Error embedding content: 429 quota") from cause

    embedder = GeminiEmbedder(Failing(), "m", tokens_per_minute=30_000)

    with pytest.raises(ModelRateLimitedError):
        await embedder.embed_query("q")


# --- error translation ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raised", "expected", "text"),
    [
        (ResourceExhausted("quota exceeded"), ModelRateLimitedError, "rate limit"),
        (Unauthenticated("bad key"), ModelProviderError, "GEMINI_API_KEY"),
        (InternalServerError("boom"), ModelProviderError, "boom"),
        (
            GoogleGenerativeAIError("Invalid argument provided to Gemini: 400 API key not valid"),
            ModelProviderError,
            "GEMINI_API_KEY",
        ),
    ],
)
def test_gemini_failures_become_the_apps_own_errors(
    raised: Exception, expected: type, text: str
) -> None:
    with pytest.raises(expected, match=text), gemini_errors("testing"):
        raise raised


def test_other_errors_pass_through_untouched() -> None:
    with pytest.raises(ValueError), gemini_errors("testing"):
        raise ValueError("not from Google")


# --- the real chat model classes, with the SDK call replaced ---------------------------------


def patch_sdk(monkeypatch, behaviour) -> list[str]:
    """Replace the SDK's network call; `behaviour(model)` returns a reply or raises."""
    calls: list[str] = []

    async def fake_agenerate(self, messages, *args, **kwargs):
        calls.append(self.model)
        reply = behaviour(self.model)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply))])

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_agenerate", fake_agenerate)
    return calls


@pytest.mark.anyio
async def test_the_fallback_model_answers_when_the_main_one_is_rate_limited(monkeypatch) -> None:
    def behaviour(model: str) -> str:
        if model.endswith("gemini-3.5-flash-lite"):
            raise ResourceExhausted("daily quota")
        return "from the fallback"

    calls = patch_sdk(monkeypatch, behaviour)
    client = GeminiLLMClient(build_gemini_chat(settings()))
    before = model_calls.snapshot()

    assert await client.generate("q") == "from the fallback"
    assert [c.split("/")[-1] for c in calls] == ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    # Both attempts are counted: the rate-limited one still used quota.
    counted = {key.split("/")[-1]: n for key, n in model_calls.since(before).items()}
    assert counted == {"gemini-3.5-flash-lite": 1, "gemini-3.1-flash-lite": 1}


@pytest.mark.anyio
async def test_other_failures_do_not_use_the_fallback(monkeypatch) -> None:
    def behaviour(model: str) -> str:
        raise Unauthenticated("bad key")

    calls = patch_sdk(monkeypatch, behaviour)
    client = GeminiLLMClient(build_gemini_chat(settings()))

    with pytest.raises(ModelProviderError, match="GEMINI_API_KEY"):
        await client.generate("q")
    assert len(calls) == 1


@pytest.mark.anyio
async def test_both_models_rate_limited_is_a_clear_429(monkeypatch) -> None:
    patch_sdk(monkeypatch, lambda model: (_ for _ in ()).throw(ResourceExhausted("quota")))
    client = GeminiLLMClient(build_gemini_chat(settings()))

    with pytest.raises(ModelRateLimitedError):
        await client.generate("q")


@pytest.mark.anyio
async def test_no_fallback_model_means_one_attempt(monkeypatch) -> None:
    calls = patch_sdk(monkeypatch, lambda model: "main only")
    client = GeminiLLMClient(build_gemini_chat(settings(gemini_fallback_model=None)))

    assert await client.generate("q") == "main only"
    assert len(calls) == 1


# --- the agent with a fallback-wrapped model --------------------------------------------------


class EchoTool:
    name = "retrieve_and_answer"
    description = "Answers questions."

    async def run(self, input_text: str) -> ToolResult:
        return ToolResult(content=f"answer to: {input_text}", sources=("a.md",))


@pytest.mark.anyio
async def test_the_agent_works_with_a_model_wrapped_in_fallbacks() -> None:
    wrapped = FakeToolCallingChatModel().with_fallbacks([FakeToolCallingChatModel()])
    agent = LangChainAgent(ToolRegistry([EchoTool()]), wrapped)

    reply = await agent.run("How do I start?")

    assert reply.content == "answer to: How do I start?"
    assert reply.sources == ("a.md",)
