from pydantic import BaseModel, Field

from app.domain.models import (
    CodeReview,
    ReviewCategory,
    ReviewFinding,
    ReviewSeverity,
    ReviewSource,
    SnippetLanguage,
)


class ReviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20_000)
    language: SnippetLanguage = "tsx"


class ReviewFindingResponse(BaseModel):
    category: ReviewCategory
    message: str
    severity: ReviewSeverity
    source: ReviewSource
    line: int | None
    rule_id: str | None

    @classmethod
    def from_domain(cls, finding: ReviewFinding) -> "ReviewFindingResponse":
        return cls(
            category=finding.category,
            message=finding.message,
            severity=finding.severity,
            source=finding.source,
            line=finding.line,
            rule_id=finding.rule_id,
        )


class ReviewResponse(BaseModel):
    findings: list[ReviewFindingResponse]
    summary: str
    judgement_available: bool
    parse_error: str | None

    @classmethod
    def from_domain(cls, review: CodeReview) -> "ReviewResponse":
        return cls(
            findings=[ReviewFindingResponse.from_domain(f) for f in review.findings],
            summary=review.summary,
            judgement_available=review.judgement_available,
            parse_error=review.parse_error,
        )
