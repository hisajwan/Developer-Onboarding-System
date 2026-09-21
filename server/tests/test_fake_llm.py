import pytest

from app.core.config import Settings
from app.domain.ports import LLMClient
from app.infrastructure.llm.fake import FakeLLMClient


@pytest.fixture
def llm() -> FakeLLMClient:
    return FakeLLMClient.from_settings(Settings(_env_file=None))


def test_satisfies_the_llm_port(llm: FakeLLMClient) -> None:
    assert isinstance(llm, LLMClient)


@pytest.mark.anyio
async def test_same_prompt_gives_the_same_answer(llm: FakeLLMClient) -> None:
    prompt = "How do I run the app?"

    assert await llm.generate(prompt) == await llm.generate(prompt)


@pytest.mark.anyio
async def test_answer_shows_the_context_it_received(llm: FakeLLMClient) -> None:
    answer = await llm.generate("Context:\nRun npm run dev.\n\nQuestion: how do I start?")

    assert answer.startswith("[fake-llm]")
    assert "Run npm run dev." in answer


@pytest.mark.anyio
async def test_long_prompts_are_cut_and_every_call_is_recorded(llm: FakeLLMClient) -> None:
    answer = await llm.generate("word " * 1000)

    assert len(answer) < 400
    assert llm.calls == ["word " * 1000]
