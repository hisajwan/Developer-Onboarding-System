"""The Code-review tool: reviews a snippet pasted into chat and replies with categorised feedback.

The review itself is the CodeReviewer's job (the same one the Code review screen uses); this tool
only pulls the code out of the message and turns the result into a chat reply.
"""

import re

from app.domain.models import CodeReview, ToolResult
from app.domain.ports import CodeReviewer

_FENCED = re.compile(r"```[\w+-]*\n(.*?)```", re.DOTALL)


class ReviewCodeTool:
    name = "review_code"
    description = (
        "Reviews a pasted React, TypeScript or JavaScript code snippet: runs ESLint on it and "
        "returns categorised feedback (accessibility, test coverage, style). Use this whenever "
        "the message contains source code to review, critique, check or improve. Do not use it "
        "for questions about the project's documentation."
    )

    def __init__(self, reviewer: CodeReviewer) -> None:
        self._reviewer = reviewer

    async def run(self, input_text: str) -> ToolResult:
        review = await self._reviewer.review(extract_code(input_text))
        return ToolResult(content=format_review(review))


def extract_code(text: str) -> str:
    """The first fenced code block if there is one, else the whole message."""
    match = _FENCED.search(text)
    return (match.group(1) if match else text).strip()


def format_review(review: CodeReview) -> str:
    if review.parse_error:
        return f"{review.summary}\n\nParse error: {review.parse_error}"
    lines = [review.summary]
    for finding in review.findings:
        where = f"line {finding.line}: " if finding.line else ""
        rule = f" ({finding.rule_id})" if finding.rule_id else ""
        lines.append(f"- [{finding.category}] {where}{finding.message}{rule}")
    if not review.findings:
        lines.append("No issues found.")
    return "\n".join(lines)
