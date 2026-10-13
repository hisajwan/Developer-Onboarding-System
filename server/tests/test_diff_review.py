import json

import pytest
from fastapi.testclient import TestClient

from app.domain.models import LintMessage
from app.infrastructure.chat_models.fake import looks_like_code
from app.review.diff import looks_like_diff, parse_diff
from app.services.code_review_service import CodeReviewService
from tests.conftest import requires_linter

DIFF = """diff --git a/src/Card.tsx b/src/Card.tsx
index 1111111..2222222 100644
--- a/src/Card.tsx
+++ b/src/Card.tsx
@@ -10,5 +10,6 @@
 export function Card({ src }: { src: string }) {
-  return <img src={src} alt="card" />;
+  const unused = 1;
+  return <img src={src} />;
 }
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,1 +1,2 @@
 # Title
+More text
"""


# --- parsing ----------------------------------------------------------------------------------


def test_a_unified_diff_is_recognised_and_plain_code_is_not() -> None:
    assert looks_like_diff(DIFF)
    assert not looks_like_diff("const a = 1;\nreturn <img />;")


def test_hunks_rebuild_the_new_code_with_new_file_line_numbers() -> None:
    card, readme = parse_diff(DIFF)

    assert (card.path, card.language, readme.language) == ("src/Card.tsx", "tsx", None)
    [hunk] = card.hunks
    assert hunk.code_lines == [
        "export function Card({ src }: { src: string }) {",
        "  const unused = 1;",
        "  return <img src={src} />;",
        "}",
    ]
    assert hunk.new_line_numbers == [10, 11, 12, 13]
    assert [hunk.added_line(n) for n in (1, 2, 3, 4)] == [None, 11, 12, None]


def test_a_deleted_file_is_ignored() -> None:
    deleted = "diff --git a/x.ts b/x.ts\n--- a/x.ts\n+++ /dev/null\n@@ -1,1 +0,0 @@\n-old\n"
    assert parse_diff(deleted) == []


def test_the_fake_router_treats_a_diff_as_code() -> None:
    assert looks_like_code("@@ -1,2 +1,3 @@\n context\n+added")


# --- the service's diff path -------------------------------------------------------------------


class ScriptedLinter:
    """Returns the given messages for every hunk, recording what it was asked to lint."""

    def __init__(self, messages: list[LintMessage]) -> None:
        self._messages = messages
        self.calls: list[tuple[str, str]] = []

    async def lint(self, code: str, filename: str) -> list[LintMessage]:
        self.calls.append((code, filename))
        return self._messages


class ScriptedLLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.prompts: list[tuple[str, str | None]] = []

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        self.prompts.append((prompt, system))
        return self._reply


@pytest.mark.anyio
async def test_only_lint_findings_on_added_lines_are_kept_and_mapped_to_the_new_file() -> None:
    linter = ScriptedLinter([
        LintMessage("@typescript-eslint/no-unused-vars", "'unused' is unused.", 2, 9, "warning"),
        LintMessage("jsx-a11y/alt-text", "img needs alt.", 3, 10, "error"),
        LintMessage("eqeqeq", "on an unchanged line", 1, 1, "warning"),
    ])
    reply = json.dumps({"summary": "Alt text removed.", "findings": [
        {"category": "test", "message": "No test for Card.", "line": 12, "file": "src/Card.tsx"}
    ]})
    llm = ScriptedLLM(reply)

    review = await CodeReviewService(linter, llm).review(DIFF)

    assert review.kind == "diff"
    assert [(f.source, f.file, f.line, f.rule_id) for f in review.findings] == [
        ("eslint", "src/Card.tsx", 11, "@typescript-eslint/no-unused-vars"),
        ("eslint", "src/Card.tsx", 12, "jsx-a11y/alt-text"),
        ("model", "src/Card.tsx", 12, None),
    ]
    assert linter.calls[0][1] == "snippet.tsx"  # README.md was not linted
    assert review.notes == ("Skipped README.md: not a JavaScript or TypeScript file.",)
    [(prompt, system)] = llm.prompts
    assert "Unified diff:" in prompt and "src/Card.tsx:12: img needs alt." in prompt
    assert "Review only the added or changed lines" in system


@pytest.mark.anyio
async def test_a_fragment_eslint_cannot_parse_is_left_to_the_model_and_noted() -> None:
    linter = ScriptedLinter([LintMessage(None, "Parsing error: '}' expected.", 3, 1, "error")])
    llm = ScriptedLLM(json.dumps({"summary": "Fine.", "findings": []}))

    review = await CodeReviewService(linter, llm).review(DIFF)

    assert review.findings == ()
    assert review.parse_error is None
    assert any("could not parse on its own" in note for note in review.notes)
    assert len(llm.prompts) == 1  # the model still reviewed the diff


@pytest.mark.anyio
async def test_a_diff_with_no_js_or_ts_changes_is_not_reviewed() -> None:
    only_readme = DIFF[DIFF.index("diff --git a/README.md"):]
    llm = ScriptedLLM("unused")

    review = await CodeReviewService(ScriptedLinter([]), llm).review(only_readme)

    assert review.parse_error == "No .js, .jsx, .ts or .tsx file is changed in this diff."
    assert llm.prompts == []


# --- end to end with the real ESLint helper ---------------------------------------------------


@requires_linter
def test_a_pasted_diff_is_reviewed_through_the_api(
    auth_client: TestClient, project_id: str
) -> None:
    body = auth_client.post(f"/api/v1/projects/{project_id}/reviews", json={"code": DIFF}).json()

    assert body["kind"] == "diff"
    rules = {(f["rule_id"], f["file"], f["line"]) for f in body["findings"]}
    assert ("jsx-a11y/alt-text", "src/Card.tsx", 12) in rules
    assert ("@typescript-eslint/no-unused-vars", "src/Card.tsx", 11) in rules
    assert "Skipped README.md: not a JavaScript or TypeScript file." in body["notes"]
