import pytest

from app.agent.tools.retrieve_and_answer import (
    _SYSTEM_PROMPT,
    NO_MATCH_MESSAGE,
    RetrieveAndAnswerTool,
    files_named_in,
    split_sources,
)
from app.domain.ports import Tool
from app.infrastructure.embeddings.fake import FakeEmbedder
from app.infrastructure.llm.fake import FakeLLMClient
from tests.helpers import InMemoryVectorStore, index_texts

PROJECT_ID = "test-project"  # matches index_texts' own default


@pytest.fixture
def vectors() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def tool(
    embedder: FakeEmbedder, vectors: InMemoryVectorStore, llm: FakeLLMClient
) -> RetrieveAndAnswerTool:
    return RetrieveAndAnswerTool(embedder, vectors, llm, PROJECT_ID, top_k=2)


def test_satisfies_the_tool_port(tool: RetrieveAndAnswerTool) -> None:
    assert isinstance(tool, Tool)
    assert tool.name == "retrieve_and_answer"


@pytest.mark.anyio
async def test_an_empty_store_gives_an_honest_answer_with_no_llm_call(
    tool: RetrieveAndAnswerTool, llm: FakeLLMClient
) -> None:
    result = await tool.run("How do I set up the dev environment?")

    assert result.content == NO_MATCH_MESSAGE
    assert result.sources == ()
    assert llm.calls == []


@pytest.mark.anyio
async def test_a_matching_question_is_answered_and_cites_its_source(
    tool: RetrieveAndAnswerTool, embedder: FakeEmbedder, vectors: InMemoryVectorStore
) -> None:
    await index_texts(vectors, embedder, [("dev-setup.md", "Run npm install then npm run dev.")])

    result = await tool.run("How do I set up the dev environment?")

    assert "npm install" in result.content
    assert result.sources == ("dev-setup.md",)


@pytest.mark.anyio
async def test_sources_are_deduplicated_and_ordered_by_relevance(
    tool: RetrieveAndAnswerTool, embedder: FakeEmbedder, vectors: InMemoryVectorStore
) -> None:
    await index_texts(
        vectors,
        embedder,
        [
            ("setup.md", "dev environment setup npm install", 0),
            ("setup.md", "dev environment setup npm run dev", 1),
            ("billing.md", "quarterly invoice payment terms", 0),
        ],
    )

    result = await tool.run("dev environment setup")

    assert result.sources[0] == "setup.md"
    assert result.sources.count("setup.md") == 1  # deduplicated even though two chunks matched


@pytest.mark.anyio
async def test_only_top_k_chunks_are_sent_as_context(
    embedder: FakeEmbedder, vectors: InMemoryVectorStore, llm: FakeLLMClient
) -> None:
    await index_texts(
        vectors,
        embedder,
        [(f"doc{i}.md", "dev environment setup guide", i) for i in range(5)],
    )
    tool = RetrieveAndAnswerTool(embedder, vectors, llm, PROJECT_ID, top_k=2)

    result = await tool.run("dev environment setup")

    assert len(result.sources) == 2


@pytest.mark.anyio
async def test_image_caption_chunks_are_retrieved_like_text(
    tool: RetrieveAndAnswerTool, embedder: FakeEmbedder, vectors: InMemoryVectorStore
) -> None:
    await index_texts(
        vectors, embedder, [("architecture.pdf", "a diagram of the API and Chroma", 0, True, 3)]
    )

    result = await tool.run("what does the architecture diagram show?")

    assert result.sources == ("architecture.pdf",)


@pytest.mark.anyio
async def test_the_system_prompt_tells_the_model_not_to_guess(
    tool: RetrieveAndAnswerTool,
    embedder: FakeEmbedder,
    vectors: InMemoryVectorStore,
    llm: FakeLLMClient,
) -> None:
    await index_texts(vectors, embedder, [("dev-setup.md", "Run npm install then npm run dev.")])

    await tool.run("How do I set up the dev environment?")

    assert "Question: How do I set up the dev environment?" in llm.calls[0]


class ScriptedLLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.prompts: list[str] = []

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        self.prompts.append(prompt)
        return self._reply


RETRIEVED = ("README.md", "Architecture.pdf", "Competitor Aegis zero knowledge.png")


# --- questions answered by a file's name ------------------------------------------------------

FILES = ["README.md", "CONTRIBUTING.md", "Competitor Aegis zero knowledge architcture.png"]


@pytest.mark.parametrize(
    ("question", "named"),
    [
        ("Who is the competitor?", ["Competitor Aegis zero knowledge architcture.png"]),
        ("Which competitors are mentioned?", ["Competitor Aegis zero knowledge architcture.png"]),
        ("What does the readme say?", ["README.md"]),
        ("What is in this project's documents?", []),  # only stopwords
        ("How do I set up?", []),
    ],
)
def test_files_named_in_matches_meaningful_words_of_the_file_name(
    question: str, named: list[str]
) -> None:
    assert files_named_in(question, FILES) == named


@pytest.mark.anyio
async def test_a_file_whose_name_answers_the_question_is_added_when_search_misses_it(
    embedder: FakeEmbedder, vectors: InMemoryVectorStore
) -> None:
    await index_texts(
        vectors,
        embedder,
        [
            ("README.md", "Who builds this and who is it for: the Ente team, for everyone."),
            ("Competitor Aegis zero knowledge architcture.png", "Browser derives keys with PBKDF2.",
             0, True, 1),
        ],
    )
    llm = ScriptedLLM("Aegis.\nSOURCES: Competitor Aegis zero knowledge architcture.png")
    tool = RetrieveAndAnswerTool(embedder, vectors, llm, PROJECT_ID, top_k=1)

    result = await tool.run("Who is the competitor?")

    [prompt] = llm.prompts
    assert prompt.startswith(
        "Project files: Competitor Aegis zero knowledge architcture.png, README.md"
    )
    assert "File: Competitor Aegis zero knowledge architcture.png (image description" in prompt
    assert result.retrieved == ("README.md", "Competitor Aegis zero knowledge architcture.png")
    assert result.sources == ("Competitor Aegis zero knowledge architcture.png",)


def test_the_prompt_treats_a_file_name_as_evidence() -> None:
    assert '"Who is the competitor?" is answered "Aegis"' in _SYSTEM_PROMPT
    # Answered directly, not "the documents don't cover it, but the file name indicates ...".
    assert "do not also say the documents don't cover it" in _SYSTEM_PROMPT


@pytest.mark.parametrize(
    ("reply", "answer", "sources"),
    [
        ("Ente is X.\n\nSOURCES: README.md", "Ente is X.", ("README.md",)),
        ("The docs don't cover it.\nSOURCES: none", "The docs don't cover it.", ()),
        (
            "A.\n**Sources:** `Architecture.pdf`, Competitor Aegis zero knowledge.png",
            "A.",
            ("Architecture.pdf", "Competitor Aegis zero knowledge.png"),
        ),
        ("B.\nsources: [readme.md], invented.md", "B.", ("README.md",)),
        ("No sources line at all.", "No sources line at all.", RETRIEVED),
    ],
)
def test_split_sources_cites_only_the_retrieved_files_the_model_names(
    reply: str, answer: str, sources: tuple[str, ...]
) -> None:
    assert split_sources(reply, RETRIEVED) == (answer, sources)


@pytest.mark.anyio
async def test_a_dont_know_answer_cites_nothing(
    embedder: FakeEmbedder, vectors: InMemoryVectorStore
) -> None:
    await index_texts(vectors, embedder, [("README.md", "Ente stores photos.")])
    llm = ScriptedLLM("The documents don't say who the competitor is.\nSOURCES: none")
    tool = RetrieveAndAnswerTool(embedder, vectors, llm, PROJECT_ID, top_k=2)

    result = await tool.run("Who is the competitor?")

    assert result.content == "The documents don't say who the competitor is."
    assert result.sources == ()
    assert result.retrieved == ("README.md",)  # retrieved, just not cited


@pytest.mark.anyio
async def test_each_excerpt_is_labelled_with_its_file_kind_and_page(
    embedder: FakeEmbedder, vectors: InMemoryVectorStore
) -> None:
    await index_texts(
        vectors,
        embedder,
        [("Competitor Aegis.png", "A diagram of a client and a server.", 0, True, 1)],
    )
    llm = ScriptedLLM("Answer.\nSOURCES: Competitor Aegis.png")
    tool = RetrieveAndAnswerTool(embedder, vectors, llm, PROJECT_ID, top_k=2)

    result = await tool.run("What does the diagram show?")

    [prompt] = llm.prompts
    assert "[1] File: Competitor Aegis.png (image description, page 1)" in prompt
    assert result.sources == ("Competitor Aegis.png",)
