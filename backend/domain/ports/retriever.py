from abc import ABC, abstractmethod
from dataclasses import dataclass
@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    section: str
    clause: str
    page_number: int | None
    document_filename: str
    policy_version_id: str
    policy_version_label: str
    score: float

class Retriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: str,
        policy_version_id: str | None = None,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        raise NotImplementedError