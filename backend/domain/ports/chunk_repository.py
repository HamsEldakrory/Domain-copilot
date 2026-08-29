from abc import ABC, abstractmethod

class ChunkRepository(ABC):
    @abstractmethod
    def get_document_hash(self, document_id) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def replace_chunks(self, document_id, chunk_candidates, embeddings) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_ingested(self, document_id, content_hash: str, embedding_provider: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_failed(self, document_id, error_message: str) -> None:
        raise NotImplementedError