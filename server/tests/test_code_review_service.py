import json

import pytest

from app.domain.models import LintMessage
from app.domain.ports import CodeReviewer
from app.services.code_review_service import CodeReviewService

ALT_TEXT = LintMessage("jsx-a11y/alt-text", "img elements must have an alt prop.", 3, 10, "error")
UNUSED = LintMessage("@typescript-eslint/no-unused-vars", "'x' is unused.", 2, 9, "warning")
PARSE_ERROR = LintMessage(None, "Parsing error: ';' expected.", 1, 6, "error")


class FixedLinter:
    def __init__(self, messages: list[LintMessage]) -> None:
        self._messages = messages
        self.calls: list[tuple[str, str]] = []

    async def lint(self, code: str, filename: str) -> list[LintMessage]:
        self.calls.append((code, filename))
        return self._messages


class FixedLLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.prompts: list[str] = []

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        self.prompts.append(prompt)
        return self._reply


def judgement(summary: str, *findings: dict) -> str:
    return json.dumps({"summary": summary, "findings": list(findings)})


def make(
    messages: list[LintMessage], reply: str
) -> tuple[CodeReviewService, FixedLinter, FixedLLM]:
    linter, llm = FixedLinter(messages), FixedLLM(reply)
    return CodeReviewService(linter, llm), linter, llm


def test_satisfies_the_code_reviewer_port() -> None:
    service, _, _ = make([], judgement("Fine."))
    assert isinstance(service, CodeReviewer)


@pytest.mark.anyio
async def test_lint_findings_are_categorised_by_rule() -> None:
    service, _, _ = make([ALT_TEXT, UNUSED], judgement("Two lint issues."))

    review = await service.review("code")

    assert [(f.category, f.source, f.rule_id, f.line) for f in review.findings] == [
        ("accessibility", "eslint", "jsx-a11y/alt-text", 3),
        ("style", "eslint", "@typescript-eslint/no-unused-vars", 2),
    ]
    assert [f.severity for f in review.findings] == ["error", "warning"]


@pytest.mark.anyio
async def test_the_models_findings_follow_the_lint_findings() -> None:
    reply = judgement(
        "Needs a test and a label.",
        {"category": "test", "message": "No test covers the empty list.", "line": None},
        {"category": "accessibility", "message": "The button has no label.", "line": 4},
    )
    service, _, _ = make([ALT_TEXT], reply)

    review = await service.review("code")

    assert review.judgement_available is True
    assert review.summary == "Needs a test and a label."
    assert [(f.category, f.source, f.severity, f.line) for f in review.findings] == [
        ("accessibility", "eslint", "error", 3),
        ("test", "model", "suggestion", None),
        ("accessibility", "model", "suggestion", 4),
    ]


@pytest.mark.anyio
async def test_clean_code_with_an_empty_judgement_has_no_findings() -> None:
    service, _, _ = make([], judgement("Looks good."))

    review = await service.review("export const Ok = () => <p>ok</p>;")

    assert review.findings == ()
    assert review.judgement_available is True
    assert review.summary == "Looks good."


@pytest.mark.anyio
async def test_a_reply_wrapped_in_a_code_fence_is_still_read() -> None:
    body = judgement("Fine.", {"category": "style", "message": "Rename x."})
    reply = f"```json\n{body}\n```"
    service, _, _ = make([], reply)

    review = await service.review("code")

    assert review.judgement_available is True
    assert [f.message for f in review.findings] == ["Rename x."]


@pytest.mark.anyio
async def test_findings_with_an_unknown_category_or_no_message_are_dropped() -> None:
    reply = judgement(
        "Mixed.",
        {"category": "performance", "message": "Not a category we show."},
        {"category": "style", "message": "   "},
        {"category": "style", "message": "Kept.", "line": -3},
        "not an object",
    )
    service, _, _ = make([], reply)

    review = await service.review("code")

    assert [(f.message, f.line) for f in review.findings] == [("Kept.", None)]


@pytest.mark.anyio
@pytest.mark.parametrize("reply", ["[fake-llm] echo", "{not json}", '{"summary": "no list"}', ""])
async def test_an_unreadable_reply_falls_back_to_lint_findings_only(reply: str) -> None:
    service, _, _ = make([UNUSED], reply)

    review = await service.review("code")

    assert review.judgement_available is False
    assert [f.source for f in review.findings] == ["eslint"]
    assert "ESLint found 1 issue(s)" in review.summary


@pytest.mark.anyio
async def test_a_snippet_that_does_not_parse_is_reported_and_the_model_is_not_asked() -> None:
    service, _, llm = make([PARSE_ERROR], judgement("unused"))

    review = await service.review("const = ;")

    assert review.parse_error == "Parsing error: ';' expected. (line 1)"
    assert review.findings == ()
    assert llm.prompts == []


@pytest.mark.anyio
async def test_the_language_picks_the_lint_filename_and_lint_output_reaches_the_prompt() -> None:
    service, linter, llm = make([ALT_TEXT], judgement("x"))

    await service.review("const a = 1;", "js")

    assert linter.calls == [("const a = 1;", "snippet.js")]
    [prompt] = llm.prompts
    assert "Language: js" in prompt
    assert "line 3: img elements must have an alt prop. (jsx-a11y/alt-text)" in prompt
    assert prompt.endswith("const a = 1;")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "rule", ["react/jsx-no-target-blank", "no-eval", "react/no-danger", "react/jsx-no-script-url"]
)
async def test_security_lint_rules_are_filed_under_security(rule: str) -> None:
    service, _, _ = make([LintMessage(rule, "unsafe", 4, 1, "warning")], judgement("x"))

    [finding] = (await service.review("code")).findings

    assert finding.category == "security"


@pytest.mark.anyio
async def test_the_model_can_raise_a_security_finding() -> None:
    reply = judgement(
        "The password is written to the console.",
        {"category": "security", "message": "Logs the plaintext password.", "line": 14},
    )
    service, _, _ = make([], reply)

    [finding] = (await service.review("code")).findings

    assert (finding.category, finding.source, finding.line) == ("security", "model", 14)
