"""
Knowledge Base routes — admin-only endpoints to ingest documents into
the Pinecone vector store for RAG retrieval.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin
from app.db.models import User
from app.rag.chunking import build_chunk_records
from app.rag.vector_store import get_vector_store
from app.schemas.schemas import KBDocumentIn, KBIngestResponse

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.post("/ingest", response_model=KBIngestResponse)
def ingest_document(
    payload: KBDocumentIn,
    _admin: User = Depends(get_current_admin),
):
    """Chunk a document, embed it, and upsert into Pinecone. Admin-only."""
    store = get_vector_store()
    records = build_chunk_records(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        metadata=payload.metadata,
    )
    count = store.upsert_chunks(records)
    return KBIngestResponse(
        chunks_ingested=count, document_ids=[r["id"] for r in records]
    )


@router.post("/ingest-bulk", response_model=KBIngestResponse)
def ingest_bulk(
    payloads: list[KBDocumentIn],
    _admin: User = Depends(get_current_admin),
):
    """Ingest multiple documents in a single call."""
    store = get_vector_store()
    all_records = []
    for doc in payloads:
        all_records.extend(
            build_chunk_records(
                title=doc.title,
                content=doc.content,
                category=doc.category,
                metadata=doc.metadata,
            )
        )
    count = store.upsert_chunks(all_records)
    return KBIngestResponse(
        chunks_ingested=count, document_ids=[r["id"] for r in all_records]
    )
