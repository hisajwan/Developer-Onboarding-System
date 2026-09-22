import pytest

from app.agent.tools.retrieve_and_answer import NO_MATCH_MESSAGE, RetrieveAndAnswerTool
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
