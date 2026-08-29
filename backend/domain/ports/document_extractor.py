from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ExtractedPage:
    page_number: int
    text: str

@dataclass
class ExtractedDocument:
    pages: list[ExtractedPage]

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)

class DocumentExtractor(ABC):
    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        raise NotImplementedError
    @abstractmethod
    def extract(self, file_path: str) -> ExtractedDocument:
        raise NotImplementedError