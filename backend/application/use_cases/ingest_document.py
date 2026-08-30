import hashlib
import re
from dataclasses import dataclass
from domain.ports.document_extractor import DocumentExtractor
from domain.ports.text_chunker import TextChunker
from domain.ports.llm_provider import LLMProvider
from domain.ports.chunk_repository import ChunkRepository

COVERAGE_LINE_RE = re.compile(r"Coverage:\s*([^.]+)\.")
@dataclass
class IngestResult:
    status: str
    chunk_count: int = 0
    error: str | None = None
class IngestDocumentUseCase:
    def __init__(
        self,
        chunker: TextChunker,
        llm_provider: LLMProvider,
        chunk_repository: ChunkRepository,
        embedding_provider_name: str,
    ):
        self._chunker = chunker
        self._llm = llm_provider
        self._chunks_repo = chunk_repository
        self._embedding_provider_name = embedding_provider_name

    def _extract_policy_name(self, candidates, fallback: str) -> str:
        for c in candidates:
            match = COVERAGE_LINE_RE.search(c.content)
            if match:
                return match.group(1).strip()
        return fallback

    def execute(self, document_id, file_path: str, extractor: DocumentExtractor) -> IngestResult:
        try:
            with open(file_path, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()

            if self._chunks_repo.get_document_hash(document_id) == content_hash:
                return IngestResult(status="unchanged")

            extracted = extractor.extract(file_path)
            candidates = self._chunker.chunk(extracted)

            if not candidates:
                self._chunks_repo.mark_failed(document_id, "No chunks produced from extracted text")
                return IngestResult(status="failed", error="No chunks produced")
            import os
            fallback_name = os.path.splitext(os.path.basename(file_path))[0]
            policy_name = self._extract_policy_name(candidates, fallback_name)

            embedding_texts = [
                f"{policy_name} — {c.section}: {c.content}" for c in candidates
            ]
            embeddings = self._llm.embeddings(embedding_texts)

            self._chunks_repo.replace_chunks(document_id, candidates, embeddings, embedding_texts)
            self._chunks_repo.mark_ingested(document_id, content_hash, self._embedding_provider_name)

            return IngestResult(status="ingested", chunk_count=len(candidates))

        except Exception as e:
            self._chunks_repo.mark_failed(document_id, str(e))
            return IngestResult(status="failed", error=str(e))