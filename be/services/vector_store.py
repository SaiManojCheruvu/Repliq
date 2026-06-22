import hashlib
import os
import uuid
from typing import Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from chromadb.config import Settings
from logger import get_logger

logger = get_logger("repliq.vector_store")

# ── Embedding function ────────────────────────────────────────────────────────
# By default we use sentence-transformers (all-MiniLM-L6-v2) for real semantic
# search.  If the package is absent (e.g. in a minimal CI environment) we fall
# back to a deterministic hash-based embedding that keeps all tests passing
# without any network downloads.

def _build_embedding_function() -> EmbeddingFunction:
    """
    Return the best available embedding function:
      1. sentence-transformers  (real semantic similarity, preferred)
      2. hash-based fallback    (deterministic, no downloads, test-safe)
    """
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        logger.info("Using SentenceTransformer embedding function")
        return ef
    except ImportError:
        logger.warning(
            "sentence-transformers not installed — using hash embedding fallback. "
            "Run: pip install sentence-transformers"
        )
        return _HashEmbeddingFunction()


class _HashEmbeddingFunction(EmbeddingFunction):
    """
    Deterministic 128-dim embedding built from SHA-256 of the text.
    Suitable for tests and CI where no model download is possible.
    NOT suitable for semantic similarity in production.
    """
    DIM = 128

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
            # Tile to 128 floats in [-1, 1]
            repeated = (digest * (self.DIM // 32 + 1))[: self.DIM]
            vec = [(b / 127.5) - 1.0 for b in repeated]
            embeddings.append(vec)
        return embeddings


_EMBEDDING_FN: Optional[EmbeddingFunction] = None


def _get_embedding_fn() -> EmbeddingFunction:
    global _EMBEDDING_FN
    if _EMBEDDING_FN is None:
        _EMBEDDING_FN = _build_embedding_function()
    return _EMBEDDING_FN

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")

_client: Optional[chromadb.ClientAPI] = None


def _get_client() -> chromadb.ClientAPI:
    """Return (or lazily create) the persistent ChromaDB client."""
    global _client
    if _client is None:
        logger.info("Initialising ChromaDB at path: %s", CHROMA_PATH)
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client



def _collection_name(business_id: str) -> str:
    """Each business gets its own ChromaDB collection, fully isolated."""
    # ChromaDB collection names must be 3-63 chars, alphanumeric + hyphens.
    return f"kb-{business_id}"


def _get_or_create_collection(business_id: str) -> chromadb.Collection:
    client = _get_client()
    name = _collection_name(business_id)
    collection = client.get_or_create_collection(
        name=name,
        embedding_function=_get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )
    logger.debug("Using collection '%s' (%d docs)", name, collection.count())
    return collection



CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # overlap between consecutive chunks


def _split_into_chunks(text: str) -> list[str]:
    """
    Split a long text into overlapping chunks of ~CHUNK_SIZE characters.
    Splitting is done on whitespace boundaries to avoid cutting words.
    """
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1  # +1 for the space

        if current_len >= CHUNK_SIZE:
            chunks.append(" ".join(current))
            # Keep the last N characters worth of words as overlap
            overlap_words: list[str] = []
            overlap_len = 0
            for w in reversed(current):
                overlap_len += len(w) + 1
                overlap_words.insert(0, w)
                if overlap_len >= CHUNK_OVERLAP:
                    break
            current = overlap_words
            current_len = sum(len(w) + 1 for w in current)

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if c.strip()]


def store_chunks(
    business_id: str,
    text: str,
    source_name: str,
    source_type: str,
) -> int:
    """
    Split *text* into chunks and upsert them into the business's collection.

    Args:
        business_id:  The business's unique identifier (e.g. "foodhub").
        text:         Full extracted text from the parser (parse_file output).
        source_name:  Original filename or label (e.g. "menu.pdf").
        source_type:  "pdf" | "csv" | "xlsx" | "text"

    Returns:
        Number of chunks stored.
    """
    chunks = _split_into_chunks(text)
    if not chunks:
        logger.warning("No chunks produced for %s / %s", business_id, source_name)
        return 0

    collection = _get_or_create_collection(business_id)

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "business_id": business_id,
            "source_name": source_name,
            "source_type": source_type,
            "chunk_index": i,
        }
        for i, _ in enumerate(chunks)
    ]

    collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
    logger.info(
        "Stored %d chunks for business=%s source=%s",
        len(chunks),
        business_id,
        source_name,
    )
    return len(chunks)


def query_chunks(
    business_id: str,
    query: str,
    n_results: int = 5,
) -> list[str]:
    """
    Retrieve the most relevant KB chunks for a given customer query.

    Used by the chat handler to inject context into the LLM prompt (RAG).

    Args:
        business_id:  The business to search within.
        query:        The customer's message.
        n_results:    How many chunks to return (default 5).

    Returns:
        List of text chunks, most relevant first.
        Returns [] if the collection is empty or no results found.
    """
    collection = _get_or_create_collection(business_id)

    if collection.count() == 0:
        logger.debug("Collection empty for business=%s, skipping query", business_id)
        return []

    # Cap n_results at what's actually available
    safe_n = min(n_results, collection.count())

    results = collection.query(
        query_texts=[query],
        n_results=safe_n,
        include=["documents"],
    )

    # results["documents"] is a list-of-lists (one per query_text)
    docs: list[str] = results["documents"][0] if results["documents"] else []
    logger.info(
        "query_chunks: business=%s, query=%r, returned=%d chunks",
        business_id,
        query[:60],
        len(docs),
    )
    return docs


def list_chunks(business_id: str) -> list[dict]:
    """
    Return metadata for all stored KB documents for the admin UI.

    Returns a deduplicated list of source documents with their chunk counts.
    """
    collection = _get_or_create_collection(business_id)

    if collection.count() == 0:
        return []

    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas") or []

    # Deduplicate by source_name, aggregating chunk counts
    sources: dict[str, dict] = {}
    for meta in metadatas:
        name = meta.get("source_name", "unknown")
        if name not in sources:
            sources[name] = {
                "source_name": name,
                "source_type": meta.get("source_type", "unknown"),
                "chunk_count": 0,
            }
        sources[name]["chunk_count"] += 1

    return list(sources.values())


def delete_chunks(business_id: str) -> bool:
    """
    Delete the entire KB collection for a business (hard reset).

    Returns True if the collection existed and was deleted, False if it
    did not exist.
    """
    client = _get_client()
    name = _collection_name(business_id)
    try:
        client.delete_collection(name)
        logger.info("Deleted KB collection for business=%s", business_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not delete collection %s: %s", name, exc)
        return False