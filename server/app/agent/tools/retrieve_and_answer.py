"""The Ask-mode tool: answers a question from the indexed docs, citing the sources it used."""

from app.domain.models import ToolResult
from app.domain.ports import Embedder, LLMClient, VectorStore

_SYSTEM_PROMPT = (
    "Answer the question using only the context below, which comes from the project's own "
    "documentation. If the context does not contain the answer, say plainly that you don't have "
    "that information instead of guessing. Do not use outside knowledge."
)

NO_MATCH_MESSAGE = "I couldn't find anything about that in the indexed docs."


class RetrieveAndAnswerTool:
    name = "retrieve_and_answer"
    description = (
        "Answers a question about this project's own documentation and codebase notes by "
        "searching the indexed docs and citing the source file(s) it used. Use this for any "
        "question that asks to explain, find, or clarify something about the project. Do not "
        "use this to review, lint or critique a pasted code snippet."
    )

    def __init__(
        self,
        embedder: Embedder,
        vectors: VectorStore,
        llm: LLMClient,
        project_id: str,
        *,
        top_k: int,
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._llm = llm
        self._project_id = project_id
        self._top_k = top_k

    async def run(self, input_text: str) -> ToolResult:
        question = input_text.strip()
        query_embedding = await self._embedder.embed_query(question)
        retrieved = await self._vectors.search(self._project_id, query_embedding, top_k=self._top_k)
        if not retrieved:
            return ToolResult(content=NO_MATCH_MESSAGE)

        sources = tuple(dict.fromkeys(result.chunk.source for result in retrieved))
        context = "\n\n".join(
            f"From {result.chunk.source}:\n{result.chunk.text}" for result in retrieved
        )
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        answer = await self._llm.generate(prompt, system=_SYSTEM_PROMPT)
        return ToolResult(content=answer, sources=sources)
