import pytest

from app.agent.tools.review_code import ReviewCodeTool, extract_code, format_review
from app.domain.models import CodeReview, ReviewFinding
from app.domain.ports import Tool

FINDING = ReviewFinding(
    category="accessibility",
    message="img elements must have an alt prop.",
    severity="error",
    source="eslint",
    line=3,
    rule_id="jsx-a11y/alt-text",
)


class FixedReviewer:
    def __init__(self, review: CodeReview) -> None:
        self._review = review
        self.calls: list[str] = []

    async def review(self, code: str, language: str = "tsx") -> CodeReview:
        self.calls.append(code)
        return self._review


def test_satisfies_the_tool_port() -> None:
    assert isinstance(ReviewCodeTool(FixedReviewer(CodeReview((), "", False))), Tool)


def test_extract_code_takes_the_first_fenced_block() -> None:
    text = "Can you review this?\n```tsx\nconst a = 1;\n```\nand this\n```\nlater\n```"
    assert extract_code(text) == "const a = 1;"


def test_extract_code_uses_the_whole_message_without_a_fence() -> None:
    assert extract_code("  const a = 1;\n") == "const a = 1;"


def test_format_lists_each_finding_with_category_line_and_rule() -> None:
    text = format_review(CodeReview((FINDING,), "One issue.", True))

    assert text == (
        "One issue.\n- [accessibility] line 3: img elements must have an alt prop. "
        "(jsx-a11y/alt-text)"
    )


def test_format_says_so_when_there_is_nothing_to_report() -> None:
    assert format_review(CodeReview((), "Looks good.", True)) == "Looks good.\nNo issues found."


def test_format_reports_a_parse_error() -> None:
    review = CodeReview((), "Could not be parsed.", False, parse_error="';' expected. (line 1)")
    assert format_review(review) == "Could not be parsed.\n\nParse error: ';' expected. (line 1)"


@pytest.mark.anyio
async def test_run_reviews_the_extracted_code_and_has_no_sources() -> None:
    reviewer = FixedReviewer(CodeReview((FINDING,), "One issue.", True))

    result = await ReviewCodeTool(reviewer).run("Review:\n```\n<img src={a} />\n```")

    assert reviewer.calls == ["<img src={a} />"]
    assert "[accessibility]" in result.content
    assert result.sources == ()
