import re

from domain.ports.text_chunker import ChunkCandidate, TextChunker
from infrastructure.ingestion.text_cleaner import clean_text

HEADING_RE = re.compile(r"^\s*(\d+)\.\s+([A-Z][^.]{2,60})$")
class NumberedHeadingChunker(TextChunker):
    def chunk(self, extracted_document) -> list[ChunkCandidate]:
        chunks = []
        current_section_num = None
        current_section_title = None
        clause_counter = 0
        current_paragraph = []

        for page in extracted_document.pages:
            text = clean_text(page.text)
            for line in text.split("\n"):
                line = line.strip()

                heading_match = HEADING_RE.match(line)
                if heading_match:
                    if current_paragraph and current_section_title:
                        clause_counter += 1
                        chunks.append(ChunkCandidate(
                            content=" ".join(current_paragraph),
                            section=current_section_title,
                            clause=f"{current_section_num}.{clause_counter}",
                            page_number=page.page_number
                        ))
                    current_paragraph = []
                    current_section_num = heading_match.group(1)
                    current_section_title = f"{current_section_num}. {heading_match.group(2).strip()}"
                    clause_counter = 0
                    continue

                if not line:
                    if current_paragraph and current_section_title:
                        clause_counter += 1
                        chunks.append(ChunkCandidate(
                            content=" ".join(current_paragraph),
                            section=current_section_title,
                            clause=f"{current_section_num}.{clause_counter}",
                            page_number=page.page_number
                        ))
                        current_paragraph = []
                    continue

                if current_section_title is None:
                    continue

                current_paragraph.append(line)

        # Catch remaining paragraph
        if current_paragraph and current_section_title:
            clause_counter += 1
            chunks.append(ChunkCandidate(
                content=" ".join(current_paragraph),
                section=current_section_title,
                clause=f"{current_section_num}.{clause_counter}",
                page_number=extracted_document.pages[-1].page_number
            ))

        return chunks