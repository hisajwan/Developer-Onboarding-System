"""Runs a fixed set of questions and code snippets and records what the system did with each, for
measuring retrieval, citation and review quality. Used by `scripts/evaluate.py`.

Each case runs on its own: questions get no chat history, and nothing is written to chat history
or the activity log, so an evaluation run doesn't change the project it measures.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.core.exceptions import AppError
from app.domain.models import SnippetLanguage
from app.domain.ports import Agent, CodeReviewer

CallSnapshot = Callable[[], dict[str, int]]


@dataclass(frozen=True, slots=True)
class QuestionCase:
    id: str
    question: str
    # Files a correct answer should draw on; empty when the docs don't cover the question.
    expected_sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SnippetCase:
    id: str
    code: str
    language: SnippetLanguage = "tsx"
    # Review categories a good review should raise, e.g. ("accessibility", "test").
    expected_categories: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Cost:
    seconds: float
    model_calls: dict[str, int]

    @property
    def total_calls(self) -> int:
        return sum(self.model_calls.values())

    def to_row(self) -> dict[str, object]:
        detail = "; ".join(f"{key}={n}" for key, n in sorted(self.model_calls.items()))
        return {"seconds": self.seconds, "model_calls": self.total_calls, "call_detail": detail}


@dataclass(frozen=True, slots=True)
class QuestionResult:
    case: QuestionCase
    cost: Cost
    answer: str = ""
    tools_used: tuple[str, ...] = ()
    retrieved: tuple[str, ...] = ()
    cited: tuple[str, ...] = ()
    error: str | None = None

    @property
    def retrieval_hit(self) -> bool | None:
        """Any expected file among the retrieved ones; None when nothing is expected."""
        return _any_of(self.case.expected_sources, self.retrieved)

    @property
    def citation_hit(self) -> bool | None:
        return _any_of(self.case.expected_sources, self.cited)

    def to_row(self) -> dict[str, object]:
        return {
            "id": self.case.id,
            "question": self.case.question,
            "answer": self.answer,
            "tools_used": _join(self.tools_used),
            "retrieved_sources": _join(self.retrieved),
            "cited_sources": _join(self.cited),
            "expected_sources": _join(self.case.expected_sources),
            "retrieval_hit": _flag(self.retrieval_hit),
            "citation_hit": _flag(self.citation_hit),
            **self.cost.to_row(),
            "error": self.error or "",
        }


@dataclass(frozen=True, slots=True)
class SnippetResult:
    case: SnippetCase
    cost: Cost
    kind: str = ""
    summary: str = ""
    eslint_findings: int = 0
    model_findings: int = 0
    categories: tuple[str, ...] = ()
    judgement_available: bool = False
    parse_error: str | None = None
    error: str | None = None

    @property
    def expected_categories_found(self) -> int:
        return len(set(self.case.expected_categories) & set(self.categories))

    def to_row(self) -> dict[str, object]:
        return {
            "id": self.case.id,
            "language": self.case.language,
            "kind": self.kind,
            "summary": self.summary,
            "eslint_findings": self.eslint_findings,
            "model_findings": self.model_findings,
            "categories": _join(self.categories),
            "expected_categories": _join(self.case.expected_categories),
            "expected_categories_found": self.expected_categories_found,
            "judgement_available": _flag(self.judgement_available),
            "parse_error": self.parse_error or "",
            **self.cost.to_row(),
            "error": self.error or "",
        }


class EvaluationService:
    def __init__(
        self,
        agent: Agent,
        reviewer: CodeReviewer,
        *,
        call_snapshot: CallSnapshot,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._agent = agent
        self._reviewer = reviewer
        self._call_snapshot = call_snapshot
        self._timer = timer

    async def ask(self, case: QuestionCase) -> QuestionResult:
        start, before = self._timer(), self._call_snapshot()
        try:
            reply = await self._agent.run(case.question)
        except AppError as exc:
            return QuestionResult(case, self._cost(start, before), error=exc.message)
        return QuestionResult(
            case,
            self._cost(start, before),
            answer=reply.content,
            tools_used=reply.tools_used,
            retrieved=reply.retrieved,
            cited=reply.sources,
        )

    async def review(self, case: SnippetCase) -> SnippetResult:
        start, before = self._timer(), self._call_snapshot()
        try:
            review = await self._reviewer.review(case.code, case.language)
        except AppError as exc:
            return SnippetResult(case, self._cost(start, before), error=exc.message)
        findings = review.findings
        return SnippetResult(
            case,
            self._cost(start, before),
            kind=review.kind,
            summary=review.summary,
            eslint_findings=sum(f.source == "eslint" for f in findings),
            model_findings=sum(f.source == "model" for f in findings),
            categories=tuple(sorted({f.category for f in findings})),
            judgement_available=review.judgement_available,
            parse_error=review.parse_error,
        )

    def _cost(self, start: float, before: dict[str, int]) -> Cost:
        after = self._call_snapshot()
        calls = {k: n - before.get(k, 0) for k, n in after.items() if n > before.get(k, 0)}
        return Cost(seconds=round(self._timer() - start, 3), model_calls=calls)


def _join(items: Sequence[str]) -> str:
    return " | ".join(items)


def _flag(value: bool | None) -> str:
    return "" if value is None else "yes" if value else "no"


def _any_of(expected: Sequence[str], found: Sequence[str]) -> bool | None:
    if not expected:
        return None
    wanted = {name.lower() for name in expected}
    return any(name.lower() in wanted for name in found)
