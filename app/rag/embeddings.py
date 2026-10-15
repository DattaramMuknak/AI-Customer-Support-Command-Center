"""
Embedding service — wraps a sentence-transformers model to convert text into
dense vectors for semantic search in Pinecone.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Thin wrapper around a local sentence-transformers model."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model
        logger.info("loading_embedding_model", model=self.model_name)
        self.model = SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> list[float]:
        """Embed a single string into a dense vector."""
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings efficiently in a single batch."""
        vectors = self.model.encode(
            texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False
        )
        return vectors.tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Cached singleton — avoids reloading the model on every request."""
    return EmbeddingService()
