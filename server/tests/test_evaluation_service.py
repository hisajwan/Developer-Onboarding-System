from collections.abc import Sequence

import pytest

from app.core.exceptions import ModelRateLimitedError
from app.domain.models import AgentReply, ChatMessage, CodeReview, ReviewFinding
from app.services.evaluation_service import EvaluationService, QuestionCase, SnippetCase


class Counter:
    """Stands in for the model-call tally: each agent or reviewer call adds one chat call."""

    def __init__(self) -> None:
        self.calls: dict[str, int] = {}

    def add(self, key: str) -> None:
        self.calls[key] = self.calls.get(key, 0) + 1

    def snapshot(self) -> dict[str, int]:
        return dict(self.calls)


class ScriptedAgent:
    def __init__(self, counter: Counter, reply: AgentReply | Exception) -> None:
        self._counter = counter
        self._reply = reply
        self.histories: list[Sequence[ChatMessage]] = []

    async def run(self, message: str, history: Sequence[ChatMessage] = ()) -> AgentReply:
        self.histories.append(history)
        self._counter.add("gemini:chat:m")
        self._counter.add("gemini:embed:e")
        if isinstance(self._reply, Exception):
            raise self._reply
        return self._reply


class ScriptedReviewer:
    def __init__(self, counter: Counter, review: CodeReview) -> None:
        self._counter = counter
        self._review = review

    async def review(self, code: str, language: str = "tsx") -> CodeReview:
        self._counter.add("gemini:chat:m")
        return self._review


def ticking_timer():
    ticks = iter([10.0, 12.5, 20.0, 21.0])
    return lambda: next(ticks)


def finding(category: str, source: str) -> ReviewFinding:
    return ReviewFinding(category=category, message="m", severity="warning", source=source)


def make_service(agent_reply: AgentReply | Exception, review: CodeReview | None = None):
    counter = Counter()
    agent = ScriptedAgent(counter, agent_reply)
    empty = CodeReview(findings=(), summary="ok", judgement_available=True)
    reviewer = ScriptedReviewer(counter, review or empty)
    service = EvaluationService(
        agent, reviewer, call_snapshot=counter.snapshot, timer=ticking_timer()
    )
    return service, agent


@pytest.mark.anyio
async def test_a_question_records_answer_retrieval_citations_time_and_calls() -> None:
    reply = AgentReply(
        content="Run npm install.",
        sources=("setup.md",),
        tools_used=("retrieve_and_answer",),
        retrieved=("setup.md", "README.md"),
    )
    service, agent = make_service(reply)

    result = await service.ask(QuestionCase("q1", "How to set up?", ("SETUP.md",)))

    assert agent.histories == [()]  # no chat history: each case stands alone
    assert (result.retrieval_hit, result.citation_hit) == (True, True)
    assert result.to_row() == {
        "id": "q1",
        "question": "How to set up?",
        "answer": "Run npm install.",
        "tools_used": "retrieve_and_answer",
        "retrieved_sources": "setup.md | README.md",
        "cited_sources": "setup.md",
        "expected_sources": "SETUP.md",
        "retrieval_hit": "yes",
        "citation_hit": "yes",
        "seconds": 2.5,
        "model_calls": 2,
        "call_detail": "gemini:chat:m=1; gemini:embed:e=1",
        "error": "",
    }


@pytest.mark.anyio
async def test_a_question_with_no_expected_sources_has_no_hit_value() -> None:
    service, _ = make_service(AgentReply(content="The docs don't cover it."))

    row = (await service.ask(QuestionCase("q2", "Payments?"))).to_row()

    assert (row["retrieval_hit"], row["citation_hit"]) == ("", "")


@pytest.mark.anyio
async def test_a_provider_failure_is_recorded_and_does_not_stop_the_run() -> None:
    service, _ = make_service(ModelRateLimitedError("quota reached"))

    result = await service.ask(QuestionCase("q1", "Anything?", ("a.md",)))

    assert result.error == "quota reached"
    assert result.retrieval_hit is False
    assert result.cost.total_calls == 2  # the failed attempt still used quota


@pytest.mark.anyio
async def test_a_snippet_records_findings_by_source_and_expected_categories_found() -> None:
    review = CodeReview(
        findings=(
            finding("accessibility", "eslint"),
            finding("accessibility", "eslint"),
            finding("test", "model"),
        ),
        summary="Missing alt text.",
        judgement_available=True,
    )
    service, _ = make_service(AgentReply(content=""), review)

    case = SnippetCase("s1", "<img />", "tsx", ("accessibility", "security"))
    result = await service.review(case)

    row = result.to_row()
    assert (row["eslint_findings"], row["model_findings"]) == (2, 1)
    assert row["categories"] == "accessibility | test"
    assert row["expected_categories_found"] == 1
    assert (row["kind"], row["judgement_available"], row["model_calls"]) == ("snippet", "yes", 1)
