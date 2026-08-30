import re
from domain.ports.text_chunker import TextChunker, ChunkCandidate
from infrastructure.ingestion.text_cleaner import clean_text
HEADING_RE = re.compile(r"^\s*(\d+)\.\s+([A-Z][^.]{2,60})$")
class NumberedHeadingChunker(TextChunker):
    def chunk(self, extracted_document) -> list[ChunkCandidate]:
        chunks = []
        current_section_num = None
        current_section_title = None
        clause_counter = 0
        for page in extracted_document.pages:
            text = clean_text(page.text)
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue

                heading_match = HEADING_RE.match(line)
                if heading_match:
                    current_section_num = heading_match.group(1)
                    current_section_title = f"{current_section_num}. {heading_match.group(2).strip()}"
                    clause_counter = 0
                    continue

                if current_section_title is None:
                    continue

                clause_counter += 1
                chunks.append(
                    ChunkCandidate(
                        content=line,
                        section=current_section_title,
                        clause=f"{current_section_num}.{clause_counter}",
                        page_number=page.page_number,
                    )
                )

        return chunks