from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from domain.ports.retriever import RetrievedChunk, Retriever
from infrastructure.persistence.models import DocumentChunk


class KeywordRetriever(Retriever):
    def retrieve(self, query, policy_version_id=None, top_k=10):
        qs = DocumentChunk.objects.select_related("document__policy_version")
        if policy_version_id:
            qs = qs.filter(document__policy_version_id=policy_version_id)
        search_query = SearchQuery(query)
        qs = qs.annotate(
            rank=SearchRank(SearchVector("search_content"), search_query)
        ).filter(rank__gt=0).order_by("-rank")[:top_k]
        results = []
        for chunk in qs:
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
                    score=float(chunk.rank),
                )
            )
        return results