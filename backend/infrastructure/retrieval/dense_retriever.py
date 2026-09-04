from pgvector.django import CosineDistance

from domain.ports.llm_provider import LLMProvider
from domain.ports.retriever import RetrievedChunk, Retriever
from infrastructure.persistence.models import DocumentChunk


class DenseRetriever(Retriever):
    def __init__(self, llm_provider: LLMProvider):
        self._llm = llm_provider

    def retrieve(self, query, policy_version_id=None, top_k=10):
        query_embedding = self._llm.embeddings([query])[0]
        qs = DocumentChunk.objects.select_related("document__policy_version")
        if policy_version_id:
            qs = qs.filter(document__policy_version_id=policy_version_id)
        qs = qs.annotate(
            distance=CosineDistance("embedding", query_embedding)
        ).order_by("distance")[:top_k]

        results = []
        for chunk in qs:
            similarity = 1 - chunk.distance
            results.append(
                RetrievedChunk(
                    chunk_id=str(chunk.id),
                    content=chunk.content,
                    section=chunk.section,
                    clause=chunk.clause,
                    page_number=chunk.page_number,
                    document_filename=chunk.document.filename,
                    policy_version_id=str(chunk.document.policy_version_id),
                    policy_version_label=chunk.document.policy_version.version,
                    score=similarity,
                )
            )
        return results