"""Reviews one pasted React/TypeScript snippet: ESLint first, then the model's judgement.

The model adds what lint rules can't see (missing tests, leaked secrets, accessibility semantics).
If its reply isn't the JSON asked for, the review falls back to the ESLint findings and says so.
"""

import json
from typing import get_args

from app.domain.models import (
    CodeReview,
    LintMessage,
    ReviewCategory,
    ReviewFinding,
    SnippetLanguage,
)
from app.domain.ports import CodeLinter, LLMClient

_CATEGORIES: tuple[str, ...] = get_args(ReviewCategory)

# ESLint rules whose findings are security problems; everything else outside jsx-a11y is style.
_SECURITY_RULES = frozenset(
    {
        "no-eval",
        "no-implied-eval",
        "no-new-func",
        "no-script-url",
        "react/no-danger",
        "react/jsx-no-script-url",
        "react/jsx-no-target-blank",
    }
)

_SYSTEM_PROMPT = "\n".join(
    [
        "You review a single React / TypeScript / JavaScript snippet for a developer.",
        "",
        "- The snippet is standalone: imports, helper functions, types and APIs it uses may be "
        "defined elsewhere in the project. Never report something only because it is not defined "
        "or imported in the snippet.",
        "- ESLint has already run; its findings are listed and shown to the user. Do not restate "
        "them. But if an ESLint finding hides a more serious problem than its message says (for "
        "example a generic console statement that logs a password or token), add your own finding "
        "on that line explaining the real impact.",
        "- Otherwise add only issues ESLint cannot detect, in four categories: 'accessibility' "
        "(semantics, labels, keyboard use, ARIA, announcing errors), 'security' (leaking secrets "
        "or personal data, unsafe HTML, injection, insecure storage or transport, weak "
        "validation), 'test' (behaviour that lacks tests, only for code with real logic) and "
        "'style' (readability, naming, error handling, React idioms).",
        "- Every issue must point at something actually in the snippet. If the code is fine, "
        "return no findings: never invent issues to fill the list.",
        "- The summary is one sentence that reflects the most serious finding, and does not call "
        "a security problem minor.",
        "",
        "Reply with JSON only, no prose and no code fences, exactly in this shape: "
        '{"summary": "<one sentence>", "findings": [{"category": '
        '"accessibility|security|test|style", "message": "<what and why, one or two sentences>", '
        '"line": <line number or null>}]}',
    ]
)


class CodeReviewService:
    def __init__(self, linter: CodeLinter, llm: LLMClient) -> None:
        self._linter = linter
        self._llm = llm

    async def review(self, code: str, language: SnippetLanguage = "tsx") -> CodeReview:
        messages = await self._linter.lint(code, f"snippet.{language}")

        parse_error = next((m for m in messages if m.rule_id is None), None)
        if parse_error is not None:
            where = f" (line {parse_error.line})" if parse_error.line else ""
            return CodeReview(
                findings=(),
                summary="The snippet could not be parsed, so it was not reviewed.",
                judgement_available=False,
                parse_error=f"{parse_error.message}{where}",
            )

        lint_findings = tuple(_from_lint(message) for message in messages)
        reply = await self._llm.generate(_prompt(code, language, messages), system=_SYSTEM_PROMPT)
        judgement = _parse_judgement(reply)
        if judgement is None:
            return CodeReview(
                findings=lint_findings,
                summary=_lint_only_summary(len(lint_findings)),
                judgement_available=False,
            )

        summary, model_findings = judgement
        return CodeReview(
            findings=lint_findings + model_findings,
            summary=summary,
            judgement_available=True,
        )


def _from_lint(message: LintMessage) -> ReviewFinding:
    rule = message.rule_id or ""
    category: ReviewCategory
    if rule.startswith("jsx-a11y/"):
        category = "accessibility"
    elif rule in _SECURITY_RULES:
        category = "security"
    else:
        category = "style"
    return ReviewFinding(
        category=category,
        message=message.message,
        severity=message.severity,
        source="eslint",
        line=message.line,
        rule_id=message.rule_id,
    )


def _prompt(code: str, language: str, messages: list[LintMessage]) -> str:
    if messages:
        lint = "\n".join(f"- line {m.line}: {m.message} ({m.rule_id})" for m in messages)
    else:
        lint = "- none"
    return f"Language: {language}\n\nESLint findings:\n{lint}\n\nSnippet:\n{code}"


def _parse_judgement(reply: str) -> tuple[str, tuple[ReviewFinding, ...]] | None:
    """The model's summary and findings, or None if the reply isn't the JSON asked for."""
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(reply[start : end + 1])
    except ValueError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return None

    findings = []
    for item in data["findings"]:
        if not isinstance(item, dict):
            continue
        category, message = item.get("category"), item.get("message")
        if category not in _CATEGORIES or not isinstance(message, str) or not message.strip():
            continue
        line = item.get("line")
        findings.append(
            ReviewFinding(
                category=category,
                message=message.strip(),
                severity="suggestion",
                source="model",
                line=line if isinstance(line, int) and line > 0 else None,
            )
        )

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = "No issues found." if not findings else f"{len(findings)} suggestion(s)."
    return summary.strip(), tuple(findings)


def _lint_only_summary(count: int) -> str:
    if count == 0:
        return "ESLint found no issues. The model's review was not available."
    return f"ESLint found {count} issue(s). The model's review was not available."
