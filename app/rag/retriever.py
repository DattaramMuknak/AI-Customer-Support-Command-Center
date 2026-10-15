"""
Retriever service — the main entry point the agents call to get relevant
knowledge-base context for a user query.
"""

from app.core.logging import get_logger
from app.rag.vector_store import get_vector_store
from app.schemas.schemas import RetrievedChunk

logger = get_logger(__name__)


class Retriever:
    def __init__(self):
        self.store = get_vector_store()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category_filter: str | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve top-k relevant chunks for a query from the knowledge base."""
        raw_matches = self.store.query(
            query, top_k=top_k, category_filter=category_filter
        )
        return [
            RetrievedChunk(
                text=m["text"],
                score=m["score"],
                source=m["source"],
                metadata=m["metadata"],
            )
            for m in raw_matches
        ]

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks into a context block for the LLM prompt."""
        if not chunks:
            return "No relevant knowledge base articles were found."

        blocks = []
        for i, c in enumerate(chunks, 1):
            blocks.append(
                f"[Source {i}: {c.source} | relevance={c.score:.2f}]\n{c.text}"
            )
        return "\n\n".join(blocks)


_retriever_instance: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance
