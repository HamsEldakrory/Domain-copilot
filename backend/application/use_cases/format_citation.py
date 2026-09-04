from domain.ports.retriever import RetrievedChunk


def format_citation(chunk: RetrievedChunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "document": chunk.document_filename,
        "policy_version": chunk.policy_version_label,
        "section": chunk.section,
        "clause": chunk.clause,
        "page": chunk.page_number,
        "excerpt": chunk.content[:300],
    }