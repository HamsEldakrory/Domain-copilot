from pypdf import PdfReader
from domain.ports.document_extractor import DocumentExtractor, ExtractedDocument, ExtractedPage
class PdfExtractor(DocumentExtractor):
    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".pdf"

    def extract(self, file_path: str) -> ExtractedDocument:
        reader = PdfReader(file_path)
        pages = [
            ExtractedPage(page_number=i + 1, text=page.extract_text() or "")
            for i, page in enumerate(reader.pages)
        ]
        return ExtractedDocument(pages=pages)