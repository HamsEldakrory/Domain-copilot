from dataclasses import dataclass
from domain.ports.retriever import Retriever, RetrievedChunk
@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    refused: bool
    refusal_reason: str | None = None
    top_dense_similarity: float = 0.0
class RetrieveChunksUseCase:
    def __init__(
        self,
        dense_retriever: Retriever,
        keyword_retriever: Retriever,
        rrf_k: int = 10,
        similarity_threshold: float = 0.35,
    ):
        self._dense = dense_retriever
        self._keyword = keyword_retriever
        self._rrf_k = rrf_k
        self._similarity_threshold = similarity_threshold

    def execute(self, query: str, policy_version_id: str | None = None, top_k: int = 5) -> RetrievalResult:
        dense_results = self._dense.retrieve(query, policy_version_id, top_k=20)
        keyword_results = self._keyword.retrieve(query, policy_version_id, top_k=20)
        top_dense_similarity = dense_results[0].score if dense_results else 0.0

        if top_dense_similarity < self._similarity_threshold:
            return RetrievalResult(
                chunks=[],
                refused=True,
                refusal_reason="Not enough information in the corpus to answer this question.",
                top_dense_similarity=top_dense_similarity,
            )

        fused_scores: dict[str, float] = {}
        chunks_by_id: dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(dense_results):
            fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0) + 1 / (self._rrf_k + rank + 1)
            chunks_by_id[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(keyword_results):
            fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0) + 1 / (self._rrf_k + rank + 1)
            chunks_by_id.setdefault(chunk.chunk_id, chunk)

        ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)[:top_k]
        result_chunks = []
        for cid in ranked_ids:
            chunk = chunks_by_id[cid]
            chunk.score = fused_scores[cid]
            result_chunks.append(chunk)

        return RetrievalResult(chunks=result_chunks, refused=False, top_dense_similarity=top_dense_similarity)