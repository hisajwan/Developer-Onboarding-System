import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool

from app.core.config import Settings
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel


async def noop(input: str) -> str:  # noqa: A002
    return "unused"


TOOL = StructuredTool.from_function(coroutine=noop, name="a_tool", description="does a thing")


@pytest.fixture
def model() -> FakeToolCallingChatModel:
    return FakeToolCallingChatModel.from_settings(Settings(_env_file=None))


def test_satisfies_the_base_chat_model_interface(model: FakeToolCallingChatModel) -> None:
    assert isinstance(model, BaseChatModel)


def test_the_first_turn_calls_the_first_bound_tool_with_the_users_message(
    model: FakeToolCallingChatModel,
) -> None:
    bound = model.bind_tools([TOOL])

    response = bound.invoke([HumanMessage(content="How do I set up the dev environment?")])

    assert isinstance(response, AIMessage)
    [call] = response.tool_calls
    assert call["name"] == "a_tool"
    assert call["args"] == {"input": "How do I set up the dev environment?"}


def test_once_a_tool_result_comes_back_it_is_returned_as_the_final_answer(
    model: FakeToolCallingChatModel,
) -> None:
    bound = model.bind_tools([TOOL])
    messages = [
        HumanMessage(content="How do I set up the dev environment?"),
        AIMessage(content="", tool_calls=[{"name": "a_tool", "args": {"input": "x"}, "id": "1"}]),
        ToolMessage(content="Run npm install.", tool_call_id="1"),
    ]

    response = bound.invoke(messages)

    assert response.content == "Run npm install."
    assert response.tool_calls == []


def test_calling_it_with_no_tools_bound_is_a_clear_error(model: FakeToolCallingChatModel) -> None:
    bound = model.bind_tools([])

    with pytest.raises(RuntimeError, match="no tools"):
        bound.invoke([HumanMessage(content="hi")])


def test_calling_it_with_no_human_message_is_a_clear_error(model: FakeToolCallingChatModel) -> None:
    bound = model.bind_tools([TOOL])

    with pytest.raises(RuntimeError, match="No user message"):
        bound.invoke([AIMessage(content="only an ai message")])
