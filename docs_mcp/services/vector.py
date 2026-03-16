"""Vector search service using ChromaDB and Sentence Transformers."""

import hashlib
from pathlib import Path
from typing import Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None  # type: ignore
    embedding_functions = None  # type: ignore

from docs_mcp.models.document import Document
from docs_mcp.utils.logger import logger


def _content_hash(title: str, content: str) -> str:
    """Compute SHA-256 hash of embedding text for change detection."""
    text = f"{title}\n\n{content[:2000]}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class VectorStore:
    """Vector database for semantic search."""

    def __init__(
        self,
        persist_directory: str | None = None,
        reindex: bool = False,
    ) -> None:
        """Initialize vector store with optional persistence.

        Args:
            persist_directory: Path for persistent storage. If None, uses ephemeral (in-memory) store.
            reindex: If True, force full rebuild of the vector index.
        """
        if chromadb is None:
            logger.warning("ChromaDB not installed. Semantic search disabled.")
            self.collection = None
            return

        try:
            if persist_directory:
                persist_path = Path(persist_directory).expanduser().resolve()
                persist_path.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=str(persist_path))
                storage_mode = f"persistent ({persist_path})"
            else:
                self.client = chromadb.Client()
                storage_mode = "ephemeral"

            # Use small, fast model
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            if reindex:
                # Delete existing collection to force full rebuild
                try:
                    self.client.delete_collection(name="documents")
                    logger.info("Deleted existing vector collection for reindex")
                except Exception:
                    pass  # Collection may not exist yet

            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )
            logger.info(f"Vector store initialized ({storage_mode})")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.collection = None

    def add_documents(self, documents: list[Document]) -> None:
        """Index documents in vector store, skipping unchanged documents.

        Args:
            documents: List of documents to index
        """
        if not self.collection or not documents:
            return

        try:
            # Build lookup of new documents by id
            new_docs: dict[str, tuple[Document, str, str]] = {}
            for doc in documents:
                text = f"{doc.title}\n\n{doc.content[:2000]}"
                doc_hash = _content_hash(doc.title, doc.content)
                new_docs[doc.uri] = (doc, text, doc_hash)

            new_ids = list(new_docs.keys())

            # Fetch existing hashes from the collection to detect changes
            existing_hashes: dict[str, str] = {}
            try:
                existing = self.collection.get(ids=new_ids, include=["metadatas"])
                if existing and existing["ids"]:
                    for eid, emeta in zip(existing["ids"], existing["metadatas"] or []):
                        if emeta and "content_hash" in emeta:
                            existing_hashes[eid] = emeta["content_hash"]
            except Exception:
                # If get fails (e.g., ids not found), treat all as new
                pass

            # Determine which documents need (re-)embedding
            to_add_ids: list[str] = []
            to_add_texts: list[str] = []
            to_add_metas: list[dict[str, str]] = []
            skipped = 0

            for doc_id, (doc, text, doc_hash) in new_docs.items():
                if doc_id in existing_hashes and existing_hashes[doc_id] == doc_hash:
                    skipped += 1
                    continue

                to_add_ids.append(doc_id)
                to_add_texts.append(text)
                to_add_metas.append(
                    {
                        "title": doc.title,
                        "category": doc.category or "uncategorized",
                        "uri": doc.uri,
                        "content_hash": doc_hash,
                    }
                )

            if not to_add_ids:
                logger.info(
                    f"Vector index up-to-date: all {skipped} documents unchanged"
                )
                return

            # Upsert in batches to handle both new and changed documents
            batch_size = 100
            for i in range(0, len(to_add_ids), batch_size):
                end = min(i + batch_size, len(to_add_ids))
                self.collection.upsert(
                    ids=to_add_ids[i:end],
                    documents=to_add_texts[i:end],
                    metadatas=to_add_metas[i:end],
                )

            logger.info(
                f"Indexed {len(to_add_ids)} documents in vector store "
                f"({skipped} unchanged, skipped)"
            )

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search similar documents.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of results with scores
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query], n_results=limit, include=["metadatas", "distances"]
            )

            # Format results
            formatted_results = []
            if results["ids"] and results["distances"]:
                ids = results["ids"][0]
                distances = results["distances"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []

                for i, uri in enumerate(ids):
                    # Convert cosine distance to similarity score
                    # Cosine distance is 0 to 2 (0 is identical)
                    # We want 1.0 = perfect match
                    dist = distances[i]
                    score = 1.0 - dist if dist < 1.0 else 0.0

                    formatted_results.append(
                        {
                            "uri": uri,
                            "score": score,
                            "metadata": metadatas[i] if len(metadatas) > i else {},
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []


# Global instance
_vector_store: VectorStore | None = None


def get_vector_store(
    persist_directory: str | None = None,
    reindex: bool = False,
) -> VectorStore:
    """Get or create the global vector store instance.

    Args:
        persist_directory: Path for persistent storage (used only on first call).
        reindex: Force full rebuild of vector index (used only on first call).

    Returns:
        The global VectorStore instance.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(
            persist_directory=persist_directory,
            reindex=reindex,
        )
    return _vector_store
