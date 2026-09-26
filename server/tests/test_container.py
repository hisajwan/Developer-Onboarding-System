import threading
from pathlib import Path

from app.api.container import Container
from app.core.config import Settings


def test_shared_objects_are_built_once_and_reused(tmp_path: Path) -> None:
    container = Container(Settings(data_dir=tmp_path / "data", _env_file=None))

    assert container.ingestion_service is container.ingestion_service
    assert container.ingestion_service is not None


def test_simultaneous_first_requests_on_a_fresh_data_folder_share_one_vector_store(
    tmp_path: Path,
) -> None:
    """The bug this guards against: two threads each creating a Chroma client on a brand-new folder
    at the same moment made one of them fail ("Could not connect to tenant default_tenant")."""
    container = Container(Settings(data_dir=tmp_path / "fresh", _env_file=None))
    start = threading.Barrier(8)
    results, errors = [], []

    def first_request() -> None:
        start.wait()
        try:
            results.append(container.ingestion_service)
        except Exception as exc:  # noqa: BLE001 - the test reports any failure
            errors.append(exc)

    threads = [threading.Thread(target=first_request) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len({id(service) for service in results}) == 1
