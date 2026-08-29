from dataclasses import dataclass
from domain.ports.retriever import Retriever, RetrievedChunk

REFUSAL_THRESHOLD = 0.025  # top fused score below this -> not enough evidence
@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    refused: bool
    refusal_reason: str | None = None

class RetrieveChunksUseCase:
    
    def __init__(self, dense_retriever: Retriever, keyword_retriever: Retriever, rrf_k: int = 60):
        self._dense = dense_retriever
        self._keyword = keyword_retriever
        self._rrf_k = rrf_k

    def execute(self, query: str, policy_version_id: str | None = None, top_k: int = 5) -> RetrievalResult:
        dense_results = self._dense.retrieve(query, policy_version_id, top_k=20)
        keyword_results = self._keyword.retrieve(query, policy_version_id, top_k=20)
        fused_scores: dict[str, float] = {}
        chunks_by_id: dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(dense_results):
            fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0) + 1 / (self._rrf_k + rank + 1)
            chunks_by_id[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(keyword_results):
            fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0) + 1 / (self._rrf_k + rank + 1)
            chunks_by_id.setdefault(chunk.chunk_id, chunk)

        ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)[:top_k]

        if not ranked_ids or fused_scores[ranked_ids[0]] < REFUSAL_THRESHOLD:
            return RetrievalResult(
                chunks=[],
                refused=True,
                refusal_reason="Not enough information in the corpus to answer this question.",
            )

        result_chunks = []
        for cid in ranked_ids:
            chunk = chunks_by_id[cid]
            chunk.score = fused_scores[cid]  # replace individual score with fused score
            result_chunks.append(chunk)

        return RetrievalResult(chunks=result_chunks, refused=False)