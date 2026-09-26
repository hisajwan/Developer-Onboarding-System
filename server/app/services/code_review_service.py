"""Reviews one pasted React/TypeScript snippet or unified diff: ESLint first, then the model.

The model adds what lint rules can't see (missing tests, leaked secrets, accessibility semantics).
If its reply isn't the JSON asked for, the review falls back to the ESLint findings and says so.
"""

import json
from dataclasses import replace
from typing import get_args

from app.domain.models import (
    CodeReview,
    LintMessage,
    ReviewCategory,
    ReviewFinding,
    SnippetLanguage,
)
from app.domain.ports import CodeLinter, LLMClient
from app.review.diff import looks_like_diff, parse_diff

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

_DIFF_SYSTEM_PROMPT = "\n".join(
    [
        _SYSTEM_PROMPT,
        "",
        "The input is a unified diff. Review only the added or changed lines (those starting "
        "with '+'); use unchanged lines only as context and never report removed lines. Give "
        '"line" as the line number in the new version of the file (from the @@ hunk headers) '
        'and add "file": "<path>" to every finding.',
    ]
)


class CodeReviewService:
    def __init__(self, linter: CodeLinter, llm: LLMClient) -> None:
        self._linter = linter
        self._llm = llm

    async def review(self, code: str, language: SnippetLanguage = "tsx") -> CodeReview:
        if looks_like_diff(code):
            return await self._review_diff(code)
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

    async def _review_diff(self, diff: str) -> CodeReview:
        """Lint each changed hunk as rebuilt new code, keep findings on added lines only, then ask
        the model to review the diff itself. A hunk that is only a fragment (ESLint can't parse
        it on its own) is left to the model and noted."""
        files = parse_diff(diff)
        notes = [f"Skipped {f.path}: not a JavaScript or TypeScript file." for f in files
                 if not f.language]
        reviewable = [f for f in files if f.language]
        if not reviewable:
            return CodeReview(
                findings=(),
                summary="The diff has no JavaScript or TypeScript changes to review.",
                judgement_available=False,
                parse_error="No .js, .jsx, .ts or .tsx file is changed in this diff.",
                kind="diff",
                notes=tuple(notes),
            )

        lint_findings: list[ReviewFinding] = []
        for file in reviewable:
            for hunk in file.hunks:
                messages = await self._linter.lint(hunk.code, f"snippet.{file.language}")
                if any(m.rule_id is None for m in messages):
                    notes.append(
                        f"{file.path} from line {hunk.new_start}: a partial fragment ESLint "
                        "could not parse on its own, so only the model reviewed it."
                    )
                    continue
                for message in messages:
                    new_line = hunk.added_line(message.line or 0)
                    if new_line is not None:
                        lint_findings.append(
                            replace(_from_lint(message), line=new_line, file=file.path)
                        )

        lint_list = "\n".join(
            f"- {f.file}:{f.line}: {f.message} ({f.rule_id})" for f in lint_findings
        ) or "- none"
        prompt = f"Unified diff:\n{diff}\n\nESLint findings on added lines:\n{lint_list}"
        judgement = _parse_judgement(
            await self._llm.generate(prompt, system=_DIFF_SYSTEM_PROMPT)
        )
        if judgement is None:
            return CodeReview(
                findings=tuple(lint_findings),
                summary=_lint_only_summary(len(lint_findings)),
                judgement_available=False,
                kind="diff",
                notes=tuple(notes),
            )
        summary, model_findings = judgement
        return CodeReview(
            findings=tuple(lint_findings) + model_findings,
            summary=summary,
            judgement_available=True,
            kind="diff",
            notes=tuple(notes),
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
        line, file = item.get("line"), item.get("file")
        findings.append(
            ReviewFinding(
                category=category,
                message=message.strip(),
                severity="suggestion",
                source="model",
                line=line if isinstance(line, int) and line > 0 else None,
                file=file.strip() if isinstance(file, str) and file.strip() else None,
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
