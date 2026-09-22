from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    # Part of every chunk id and index signature, so switching models never reuses old vectors.
    model_name: str

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...
