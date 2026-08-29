from domain.ports.chunk_repository import ChunkRepository
from infrastructure.persistence.models import Document, DocumentChunk

class DjangoChunkRepository(ChunkRepository):
    def get_document_hash(self, document_id):
        try:
            return Document.objects.get(id=document_id).content_hash
        except Document.DoesNotExist:
            return None
        
    def replace_chunks(self, document_id, chunk_candidates, embeddings):
        DocumentChunk.objects.filter(document_id=document_id).delete()
        objs = [
            DocumentChunk(
                document_id=document_id,
                page_number=c.page_number,
                section=c.section or "",
                clause=c.clause or "",
                content=c.content,
                embedding=emb,
            )
            for c, emb in zip(chunk_candidates, embeddings)
        ]
        DocumentChunk.objects.bulk_create(objs)

    def mark_ingested(self, document_id, content_hash, embedding_provider):
        Document.objects.filter(id=document_id).update(
            status="ingested",
            content_hash=content_hash,
            error_message="",
            embedding_provider=embedding_provider,
        )
    def mark_failed(self, document_id, error_message):
        Document.objects.filter(id=document_id).update(
            status="failed", error_message=error_message[:1000]
        )