"""
Pinecone vector store wrapper — handles index creation, upsert (ingest),
and similarity-search (retrieval) for the RAG pipeline.
"""

from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embeddings import get_embedding_service

logger = get_logger(__name__)


class VectorStore:
    """Wraps a Pinecone index for upsert/query operations used by the RAG pipeline."""

    def __init__(self):
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.embedder = get_embedding_service()
        self._ensure_index()
        self.index = self.client.Index(self.index_name)

    def _ensure_index(self) -> None:
        """Create the Pinecone index if it doesn't already exist."""
        existing = [idx["name"] for idx in self.client.list_indexes()]
        if self.index_name not in existing:
            logger.info("creating_pinecone_index", index=self.index_name)
            self.client.create_index(
                name=self.index_name,
                dimension=settings.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
            )

    def upsert_chunks(self, records: list[dict], namespace: str = "support-kb") -> int:
        """
        Embed and upsert a list of chunk records.
        Each record must have: id, text, metadata.
        """
        texts = [r["text"] for r in records]
        vectors = self.embedder.embed_batch(texts)

        upserts = [
            {
                "id": r["id"],
                "values": vec,
                "metadata": {**r["metadata"], "text": r["text"]},
            }
            for r, vec in zip(records, vectors)
        ]

        self.index.upsert(vectors=upserts, namespace=namespace)
        logger.info("upserted_chunks", count=len(upserts), namespace=namespace)
        return len(upserts)

    def query(
        self,
        query_text: str,
        top_k: int | None = None,
        namespace: str = "support-kb",
        category_filter: str | None = None,
    ) -> list[dict]:
        """
        Embed a query and run similarity search against Pinecone.
        Returns list of {text, score, source, metadata}.
        """
        top_k = top_k or settings.max_retrieval_docs
        query_vector = self.embedder.embed_text(query_text)

        filter_dict = (
            {"category": {"$eq": category_filter}} if category_filter else None
        )

        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            filter=filter_dict,
        )

        matches = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            matches.append(
                {
                    "text": metadata.get("text", ""),
                    "score": match.get("score", 0.0),
                    "source": metadata.get("title", "unknown"),
                    "metadata": metadata,
                }
            )

        # Filter out low-confidence matches
        filtered = [m for m in matches if m["score"] >= settings.similarity_threshold]
        logger.info(
            "retrieval_complete",
            query=query_text[:80],
            total_matches=len(matches),
            kept=len(filtered),
        )
        return filtered or matches[:2]  # fallback: return top 2 even if below threshold


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()
