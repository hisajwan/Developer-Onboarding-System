from datetime import UTC, datetime

import pytest

from app.agent.langchain_agent import LangChainAgent
from app.agent.tools.registry import ToolRegistry
from app.core.config import Settings
from app.domain.models import ChatMessage, ToolResult
from app.domain.ports import Agent
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel


class RecordingTool:
    name = "retrieve_and_answer"
    description = "Answers a question from the docs."

    def __init__(self, result: ToolResult) -> None:
        self._result = result
        self.calls: list[str] = []

    async def run(self, input_text: str) -> ToolResult:
        self.calls.append(input_text)
        return self._result


class FailingTool:
    name = "retrieve_and_answer"
    description = "Answers a question from the docs."

    async def run(self, input_text: str) -> ToolResult:
        raise RuntimeError("provider unavailable")


def make_agent(tool) -> LangChainAgent:
    chat_model = FakeToolCallingChatModel.from_settings(Settings(_env_file=None))
    return LangChainAgent(ToolRegistry([tool]), chat_model)


def test_satisfies_the_agent_port() -> None:
    assert isinstance(make_agent(RecordingTool(ToolResult(content="x"))), Agent)


@pytest.mark.anyio
async def test_the_tools_answer_and_sources_reach_the_reply() -> None:
    tool = RecordingTool(ToolResult(content="Run npm install.", sources=("dev-setup.md",)))
    agent = make_agent(tool)

    reply = await agent.run("How do I set up the dev environment?")

    assert reply.content == "Run npm install."
    assert reply.sources == ("dev-setup.md",)
    assert reply.tools_used == ("retrieve_and_answer",)
    assert tool.calls == ["How do I set up the dev environment?"]


@pytest.mark.anyio
async def test_a_tool_with_no_sources_gives_an_empty_sources_tuple() -> None:
    agent = make_agent(RecordingTool(ToolResult(content="I don't know.")))

    reply = await agent.run("something unrelated")

    assert reply.sources == ()
    assert reply.tools_used == ("retrieve_and_answer",)


@pytest.mark.anyio
async def test_a_tool_error_propagates_instead_of_a_silent_wrong_answer() -> None:
    agent = make_agent(FailingTool())

    with pytest.raises(Exception, match="provider unavailable"):
        await agent.run("How do I set up the dev environment?")


@pytest.mark.anyio
async def test_run_works_with_no_history_passed_at_all() -> None:
    tool = RecordingTool(ToolResult(content="fine"))
    agent = make_agent(tool)

    reply = await agent.run("a question")  # history omitted - the default must not break the prompt

    assert reply.content == "fine"


@pytest.mark.anyio
async def test_past_turns_do_not_confuse_the_fake_model_about_the_current_question() -> None:
    """The fake chat model always answers by routing the *last* human message to a tool - this

    only stays correct once past turns are mixed into the prompt if the current question is still
    found. Real memory (a real model reading the whole transcript) is out of scope for a fake.
    """
    tool = RecordingTool(ToolResult(content="Run npm install."))
    agent = make_agent(tool)
    now = datetime.now(UTC)
    history = [
        ChatMessage(role="user", content="What is this project?", created_at=now),
        ChatMessage(role="assistant", content="It's an onboarding assistant.", created_at=now),
    ]

    reply = await agent.run("How do I set it up?", history)

    assert reply.content == "Run npm install."
    assert tool.calls == ["How do I set it up?"]  # not a historical message
