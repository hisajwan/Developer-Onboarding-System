from typing import Protocol, runtime_checkable

from app.domain.models import CodeReview, SnippetLanguage


@runtime_checkable
class CodeReviewer(Protocol):
    """Reviews one pasted snippet: lint findings plus the model's judgement, categorised."""

    async def review(self, code: str, language: SnippetLanguage = "tsx") -> CodeReview: ...
