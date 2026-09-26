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
        "returns categorised feedback (accessibility, security, test coverage, style). Use this "
        "whenever "
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
    """The review as Markdown: the summary, then one bullet per finding."""
    if review.parse_error:
        return f"{review.summary}\n\n**Parse error:** {review.parse_error}"
    if not review.findings:
        lines = [review.summary, "", "No issues found."]
    else:
        lines = [review.summary, ""]
        for finding in review.findings:
            place = f"`{finding.file}` " if finding.file else ""
            where = f"{place}line {finding.line}: " if finding.line else place
            rule = f" (`{finding.rule_id}`)" if finding.rule_id else ""
            lines.append(f"- **{finding.category}** · {where}{finding.message}{rule}")
    if review.notes:
        lines += ["", *(f"_Note: {note}_" for note in review.notes)]
    return "\n".join(lines)
