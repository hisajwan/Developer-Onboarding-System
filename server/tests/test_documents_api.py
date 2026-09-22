import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.helpers import make_image, make_pdf, make_pdf_with_image

GUIDE = b"# Dev setup\n\nInstall dependencies with npm install, then start with npm run dev."


def upload(client: TestClient, name: str, content: bytes, content_type: str = "text/markdown"):
    return client.post("/api/v1/documents", files={"file": (name, content, content_type)})


def embedded_count(client: TestClient) -> int:
    return client.app.state.container.embedder.texts_embedded


def test_documents_require_login(client: TestClient) -> None:
    assert upload(client, "guide.md", GUIDE).status_code == 401
    assert client.get("/api/v1/documents").status_code == 401


def test_a_markdown_upload_is_indexed_and_listed(auth_client: TestClient) -> None:
    response = upload(auth_client, "guide.md", GUIDE)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "indexed"
    assert body["document"]["filename"] == "guide.md"
    assert body["document"]["chunk_count"] == body["chunks_embedded"] == 1

    listed = auth_client.get("/api/v1/documents").json()["documents"]
    assert [d["filename"] for d in listed] == ["guide.md"]


def test_an_identical_reupload_is_skipped_without_embedding_again(auth_client: TestClient) -> None:
    upload(auth_client, "guide.md", GUIDE)
    embedded_before = embedded_count(auth_client)

    response = upload(auth_client, "guide.md", GUIDE)

    assert response.json()["status"] == "unchanged"
    assert response.json()["chunks_embedded"] == 0
    assert embedded_count(auth_client) == embedded_before
    assert len(auth_client.get("/api/v1/documents").json()["documents"]) == 1


def test_pdf_and_text_files_are_accepted(auth_client: TestClient) -> None:
    pdf = upload(auth_client, "arch.pdf", make_pdf("The API talks to Chroma"), "application/pdf")
    txt = upload(auth_client, "notes.txt", b"plain notes about deployment", "text/plain")

    assert pdf.status_code == txt.status_code == 200
    assert {d["filename"] for d in auth_client.get("/api/v1/documents").json()["documents"]} == {
        "arch.pdf",
        "notes.txt",
    }


def test_a_pdf_with_a_diagram_gets_a_captioned_chunk_for_it(auth_client: TestClient) -> None:
    pdf = make_pdf_with_image(64, 64, text="architecture overview")

    response = upload(auth_client, "architecture.pdf", pdf, "application/pdf")

    body = response.json()
    assert response.status_code == 200
    assert body["document"]["chunk_count"] == 2  # the text plus the diagram's caption
    assert body["chunks_embedded"] == 2

    # Re-uploading the identical PDF must not caption the diagram again.
    again = upload(auth_client, "architecture.pdf", pdf, "application/pdf")
    assert again.json()["status"] == "unchanged"
    assert again.json()["chunks_embedded"] == 0


def test_a_standalone_image_upload_is_indexed_and_cited(auth_client: TestClient) -> None:
    response = upload(auth_client, "diagram.png", make_image(64, 64), "image/png")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "indexed"
    assert body["document"]["chunk_count"] == body["chunks_embedded"] == 1
    assert [d["filename"] for d in auth_client.get("/api/v1/documents").json()["documents"]] == [
        "diagram.png"
    ]


def test_a_standalone_image_that_is_too_small_gets_a_clear_422(auth_client: TestClient) -> None:
    response = upload(auth_client, "icon.png", make_image(10, 10), "image/png")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_document"
    assert "at least" in response.json()["error"]["message"]


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("program.exe", b"MZ", "Unsupported file type"),
        ("empty.md", b"", "empty"),
        ("blank.md", b"   \n ", "No text"),
        ("broken.pdf", b"not a pdf", "could not be read"),
    ],
)
def test_unusable_files_get_a_clear_422(
    auth_client: TestClient, name: str, content: bytes, message: str
) -> None:
    response = upload(auth_client, name, content)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_document"
    assert message in response.json()["error"]["message"]
    assert auth_client.get("/api/v1/documents").json()["documents"] == []


def test_an_oversized_file_gets_a_413(make_client) -> None:
    client = make_client(max_upload_bytes=50)

    response = upload(client, "big.md", b"word " * 100)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "document_too_large"


def test_a_request_without_a_file_is_a_validation_error(auth_client: TestClient) -> None:
    assert auth_client.post("/api/v1/documents").status_code == 422


def test_a_path_in_the_filename_cannot_escape_the_docs_folder(
    auth_client: TestClient, settings: Settings
) -> None:
    response = upload(auth_client, "../../evil.md", GUIDE)

    assert response.json()["document"]["filename"] == "evil.md"
    assert (settings.docs_dir / "evil.md").read_bytes() == GUIDE
    assert not (settings.data_dir.parent / "evil.md").exists()


def test_the_original_file_is_kept_on_disk(auth_client: TestClient, settings: Settings) -> None:
    upload(auth_client, "guide.md", GUIDE)

    assert (settings.docs_dir / "guide.md").read_bytes() == GUIDE


def test_everything_is_still_there_after_a_backend_restart(
    auth_client: TestClient, make_client
) -> None:
    upload(auth_client, "guide.md", GUIDE)

    restarted = make_client()  # a brand new app over the same data folder, like restarting uvicorn

    listed = restarted.get("/api/v1/documents").json()["documents"]
    assert [d["filename"] for d in listed] == ["guide.md"]
    assert asyncio.run(restarted.app.state.container.vector_store.count_documents()) == 1
    again = upload(restarted, "guide.md", GUIDE)
    assert again.json()["status"] == "unchanged"
    assert embedded_count(restarted) == 0  # nothing was re-embedded: the index survived
