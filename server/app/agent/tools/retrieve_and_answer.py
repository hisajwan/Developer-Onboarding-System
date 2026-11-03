"""The Ask-mode tool: answers a question from the indexed docs, citing the sources it used.

The model is asked to end its answer with a `SOURCES:` line naming only the files it actually
used; the tool strips that line and cites exactly those (so an "I don't know" cites nothing). If a
model forgets the line, every retrieved file is cited, as before.
"""

import re

from app.domain.models import RetrievedChunk, ToolResult
from app.domain.ports import Embedder, LLMClient, VectorStore

_SYSTEM_PROMPT = "\n".join(
    [
        "You answer a developer's question about their project using only the excerpts below, "
        "which come from the project's own documents. Do not use outside knowledge.",
        "",
        "- Each excerpt is labelled with its file name, and the project's file names are listed. "
        "A file's name is evidence in itself: a file called \"Competitor Aegis architecture\" "
        "means the documents say Aegis is a competitor, so \"Who is the competitor?\" is answered "
        "\"Aegis\", citing that file. Use file names this way even when the excerpt's text does "
        "not repeat them. When a file name answers the question, give that answer directly and "
        "confidently (\"The competitor is Aegis, according to `Competitor Aegis architecture`.\"); "
        "do not also say the documents don't cover it, and don't hedge with \"indicates\" or "
        "\"suggests\".",
        "- Answer in your own words. Summarise; do not copy whole documents, quote only short key "
        "parts.",
        "- When facts come from different files, say which file each comes from. Never merge facts "
        "about different products or systems (for example a competitor's design and this "
        "project's) into one description.",
        "- If neither the excerpts nor the file names answer the question, say plainly that the "
        "documents don't cover it. Do not guess.",
        "- Format with Markdown where it helps: short paragraphs, bullet lists, `code` for "
        "identifiers. Refer to files by name; never mention excerpt numbers like [1].",
        "- End with one final line, exactly: SOURCES: followed by the file names you actually "
        "used, comma-separated, or SOURCES: none if you used none.",
    ]
)

# A final "SOURCES: a.md, b.pdf" line, tolerating Markdown decoration such as "**Sources:**".
_SOURCES_LINE = re.compile(r"^[ \t>*_`#-]*sources\W*:(?P<names>.*)$", re.IGNORECASE | re.MULTILINE)
_NAME_EDGES = re.compile(r"^[\s`'\"*_\[\]()]+|[\s`'\"*_\[\]()]+$")

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

        all_sources = await self._vectors.sources(self._project_id)
        retrieved = await self._add_files_named_in(question, all_sources, retrieved)
        retrieved_sources = tuple(dict.fromkeys(result.chunk.source for result in retrieved))
        context = "\n\n".join(_excerpt(n, result) for n, result in enumerate(retrieved, start=1))
        prompt = (
            f"Project files: {', '.join(all_sources)}\n\n"
            f"Excerpts:\n\n{context}\n\nQuestion: {question}"
        )
        reply = await self._llm.generate(prompt, system=_SYSTEM_PROMPT)
        answer, sources = split_sources(reply, retrieved_sources)
        return ToolResult(content=answer, sources=sources, retrieved=retrieved_sources)

    async def _add_files_named_in(
        self, question: str, all_sources: list[str], retrieved: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        """Search goes by the meaning of a chunk's text, so a file whose *name* answers the
        question ("Competitor Aegis ...") can rank below unrelated text. Files whose names share
        a word with the question are added to the excerpts if search missed them."""
        found = {result.chunk.source for result in retrieved}
        extra: list[RetrievedChunk] = []
        for source in files_named_in(question, all_sources)[:_MAX_NAMED_FILES]:
            if source not in found:
                extra += await self._vectors.chunks_for_source(
                    self._project_id, source, _CHUNKS_PER_NAMED_FILE
                )
        return retrieved + extra


# Words too common to say anything about which file a question means.
_STOPWORDS = frozenset({
    "about", "after", "also", "another", "before", "does", "doing", "from", "have", "into",
    "just", "like", "more", "most", "much", "only", "other", "over", "same", "some", "such",
    "than", "that", "their", "them", "then", "there", "these", "they", "this", "those", "very",
    "what", "when", "where", "which", "while", "will", "with", "would", "your",
    "project", "projects", "document", "documents", "file", "files",
    "explain", "describe", "tell", "show", "give", "list",
})
_WORD = re.compile(r"[a-z0-9]+")
_MAX_NAMED_FILES = 3
_CHUNKS_PER_NAMED_FILE = 2


def files_named_in(question: str, sources: list[str]) -> list[str]:
    """The sources whose file name shares a meaningful word (4+ letters, not a stopword) with the
    question, ignoring case, extension and a plural "s"."""
    wanted = _keywords(question)
    if not wanted:
        return []
    return [source for source in sources if wanted & _keywords(source.rsplit(".", 1)[0])]


def _keywords(text: str) -> set[str]:
    words = {word for word in _WORD.findall(text.lower()) if len(word) >= 4}
    return {word.removesuffix("s") for word in words - _STOPWORDS}


def _excerpt(number: int, result: RetrievedChunk) -> str:
    chunk = result.chunk
    kind = "image description" if chunk.is_image_caption else "text"
    page = f", page {chunk.page}" if chunk.page else ""
    return f"[{number}] File: {chunk.source} ({kind}{page})\n{chunk.text}"


def split_sources(reply: str, retrieved: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    """The answer without its SOURCES line, and the retrieved files that line names.

    Names the model made up are dropped (only retrieved files can be cited). No SOURCES line at all
    means every retrieved file is cited; "none" means no citation.
    """
    matches = list(_SOURCES_LINE.finditer(reply))
    if not matches:
        return reply.strip(), retrieved
    last = matches[-1]
    answer = (reply[: last.start()] + reply[last.end() :]).strip()
    named = {_normalise(name) for name in last.group("names").split(",")}
    return answer, tuple(source for source in retrieved if _normalise(source) in named)


def _normalise(name: str) -> str:
    return _NAME_EDGES.sub("", name).lower()
