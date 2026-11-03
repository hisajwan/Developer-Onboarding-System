import json

import pytest

from app.domain.models import LintMessage
from app.infrastructure.embeddings.fake import FakeEmbedder
from app.services.code_review_service import CodeReviewService
from app.services.review_guidance import ProjectCodeReviewer, ReviewGuidance, guideline_files
from tests.helpers import InMemoryVectorStore, index_texts

PROJECT = "test-project"  # index_texts' default
CODE = "export function Save() {\n  return <button onClick={save}>Save</button>;\n}"
RULES = "All buttons must use our <Button> component from ui/Button, never a raw <button>."


class CountingEmbedder(FakeEmbedder):
    def __init__(self) -> None:
        super().__init__()
        self.queries: list[str] = []

    async def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return await super().embed_query(text)


class NoLint:
    async def lint(self, code: str, filename: str) -> list[LintMessage]:
        return []


class ScriptedLLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.prompts: list[str] = []

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        self.prompts.append(prompt)
        return self._reply


def test_guideline_files_are_recognised_by_name() -> None:
    names = ["README.md", "CONTRIBUTING.md", "coding-standards.pdf", "Style Guide.md", "api.md"]

    assert guideline_files(names) == ["CONTRIBUTING.md", "coding-standards.pdf", "Style Guide.md"]


@pytest.mark.anyio
async def test_a_project_without_documents_costs_no_embedding_call() -> None:
    embedder = CountingEmbedder()
    guidance = ReviewGuidance(embedder, InMemoryVectorStore())

    assert await guidance.find(PROJECT, CODE) == ()
    assert embedder.queries == []


@pytest.mark.anyio
async def test_guideline_files_come_first_then_the_closest_chunks() -> None:
    embedder, vectors = CountingEmbedder(), InMemoryVectorStore()
    await index_texts(
        vectors,
        embedder,
        [
            ("README.md", "Run npm install then npm run dev."),
            ("CONTRIBUTING.md", RULES),
            ("notes.md", "Save button styling and button components."),
        ],
    )

    excerpts = await ReviewGuidance(embedder, vectors).find(PROJECT, CODE)

    assert excerpts[0].chunk.source == "CONTRIBUTING.md"
    assert len({(e.chunk.source, e.chunk.index) for e in excerpts}) == len(excerpts)  # no repeats
    assert len(excerpts) <= 4
    assert embedder.queries[-1].startswith("Coding standards, conventions and review rules")


@pytest.mark.anyio
async def test_a_finding_based_on_a_project_rule_names_the_document() -> None:
    embedder, vectors = CountingEmbedder(), InMemoryVectorStore()
    await index_texts(vectors, embedder, [("CONTRIBUTING.md", RULES)])
    reply = json.dumps({"summary": "Uses a raw button.", "findings": [
        {"category": "style", "message": "Use <Button> from ui/Button.", "line": 2,
         "reference": "CONTRIBUTING.md"},
        {"category": "test", "message": "No test for Save.", "line": None,
         "reference": "invented.md"},
    ]})
    llm = ScriptedLLM(reply)
    reviewer = ProjectCodeReviewer(
        CodeReviewService(NoLint(), llm), ReviewGuidance(embedder, vectors), PROJECT
    )

    review = await reviewer.review(CODE)

    [prompt] = llm.prompts
    assert prompt.startswith("Project document excerpts")
    assert f"File: CONTRIBUTING.md\n{RULES}" in prompt
    assert review.consulted == ("CONTRIBUTING.md",)
    assert [(f.message, f.reference) for f in review.findings] == [
        ("Use <Button> from ui/Button.", "CONTRIBUTING.md"),
        ("No test for Save.", None),  # a document that wasn't given can't be cited
    ]


@pytest.mark.anyio
async def test_without_guidance_the_prompt_is_unchanged() -> None:
    llm = ScriptedLLM(json.dumps({"summary": "Fine.", "findings": []}))

    review = await CodeReviewService(NoLint(), llm).review(CODE)

    assert llm.prompts[0].startswith("Language: tsx")
    assert review.consulted == ()
