"""
Document chunking utilities — splits long support docs/articles into
overlapping chunks suitable for embedding and retrieval.
"""

import re
import uuid


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 75,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    chunk_size: approx number of words per chunk
    chunk_overlap: number of words shared between consecutive chunks
    """
    text = clean_text(text)
    words = text.split(" ")

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = end - chunk_overlap

    return chunks


def build_chunk_records(
    title: str,
    content: str,
    category: str | None = None,
    metadata: dict | None = None,
) -> list[dict]:
    """
    Produce Pinecone-ready chunk records with metadata, given a raw document.
    """
    metadata = metadata or {}
    chunks = chunk_text(content)
    records = []
    for i, chunk in enumerate(chunks):
        records.append(
            {
                "id": f"{uuid.uuid4()}",
                "text": chunk,
                "metadata": {
                    "title": title,
                    "category": category or "general",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **metadata,
                },
            }
        )
    return records
