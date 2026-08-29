from abc import ABC, abstractmethod
from dataclasses import dataclass
@dataclass
class ChunkCandidate:
    content: str
    section: str | None
    clause: str | None
    page_number: int | None

class TextChunker(ABC):
    @abstractmethod
    def chunk(self, extracted_document) -> list[ChunkCandidate]:
        raise NotImplementedError