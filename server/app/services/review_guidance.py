"""Code review that knows the project's own rules: before a review, the project's documents are
searched for coding standards and conventions, and the excerpts go to the reviewer with the code.

Files named like guidelines (CONTRIBUTING, standards, conventions, style guide, …) come first,
since that is where teams write rules down; the rest are the chunks closest to the code. The
reviewer is told to use an excerpt only when it states a rule that applies, so unrelated excerpts
cost tokens but don't produce findings.
"""

import re

from app.domain.models import CodeReview, RetrievedChunk, SnippetLanguage
from app.domain.ports import Embedder, VectorStore
from app.services.code_review_service import CodeReviewService

_GUIDELINE_NAME = re.compile(
    r"contribut|guideline|standard|convention|style|lint|rule|best[\s_-]*practice|"
    r"code[\s_-]*review|checklist",
    re.IGNORECASE,
)
_MAX_EXCERPTS = 4
_GUIDELINE_FILES = 2
_CHUNKS_PER_GUIDELINE_FILE = 2
_CODE_CHARS_IN_QUERY = 1500


class ReviewGuidance:
    def __init__(self, embedder: Embedder, vectors: VectorStore) -> None:
        self._embedder = embedder
        self._vectors = vectors

    async def find(self, project_id: str, code: str) -> tuple[RetrievedChunk, ...]:
        """Up to four excerpts of the project's documents that may set rules for this code.
        A project with no documents costs no embedding call."""
        sources = await self._vectors.sources(project_id)
        if not sources:
            return ()
        picked: list[RetrievedChunk] = []
        for source in guideline_files(sources)[:_GUIDELINE_FILES]:
            picked += await self._vectors.chunks_for_source(
                project_id, source, _CHUNKS_PER_GUIDELINE_FILE
            )
        query = (
            "Coding standards, conventions and review rules that apply to this code:\n"
            + code[:_CODE_CHARS_IN_QUERY]
        )
        embedding = await self._embedder.embed_query(query)
        seen = {(r.chunk.source, r.chunk.index, r.chunk.is_image_caption) for r in picked}
        for hit in await self._vectors.search(project_id, embedding, top_k=_MAX_EXCERPTS):
            key = (hit.chunk.source, hit.chunk.index, hit.chunk.is_image_caption)
            if key not in seen:
                picked.append(hit)
                seen.add(key)
        return tuple(picked[:_MAX_EXCERPTS])


def guideline_files(sources: list[str]) -> list[str]:
    """The file names that look like where a team writes its rules down."""
    return [source for source in sources if _GUIDELINE_NAME.search(source.rsplit(".", 1)[0])]


class ProjectCodeReviewer:
    """The `CodeReviewer` for one project: the shared review, checked against that project's
    own documents. Used by both the Code review screen and the chat's review tool."""

    def __init__(
        self, reviewer: CodeReviewService, guidance: ReviewGuidance, project_id: str
    ) -> None:
        self._reviewer = reviewer
        self._guidance = guidance
        self._project_id = project_id

    async def review(self, code: str, language: SnippetLanguage = "tsx") -> CodeReview:
        excerpts = await self._guidance.find(self._project_id, code)
        return await self._reviewer.review(code, language, guidance=excerpts)
