"""Vector search service using ChromaDB and Sentence Transformers."""

from typing import Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None  # type: ignore
    embedding_functions = None  # type: ignore

from docs_mcp.models.document import Document
from docs_mcp.utils.logger import logger


class VectorStore:
    """Vector database for semantic search."""

    def __init__(self) -> None:
        """Initialize ephemeral vector store."""
        if chromadb is None:
            logger.warning("ChromaDB not installed. Semantic search disabled.")
            self.collection = None
            return

        try:
            self.client = chromadb.Client()
            # Use small, fast model
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self.collection = self.client.create_collection(
                name="documents",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )
            logger.info("Vector store initialized (ephemeral)")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.collection = None

    def add_documents(self, documents: list[Document]) -> None:
        """Index documents in vector store.

        Args:
            documents: List of documents to index
        """
        if not self.collection or not documents:
            return

        try:
            # Prepare data
            ids = [doc.uri for doc in documents]
            documents_text = []
            metadatas = []

            for doc in documents:
                # Combine title and content for embedding
                # We prioritize the first 2000 chars which usually contain the intro/summary
                text = f"{doc.title}\n\n{doc.content[:2000]}"
                documents_text.append(text)

                metadatas.append(
                    {
                        "title": doc.title,
                        "category": doc.category or "uncategorized",
                        "uri": doc.uri,
                    }
                )

            # Add in batches to prevent payload issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end = min(i + batch_size, len(documents))
                self.collection.add(
                    ids=ids[i:end], documents=documents_text[i:end], metadatas=metadatas[i:end]
                )

            logger.info(f"Indexed {len(documents)} documents in vector store")

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


def get_vector_store() -> VectorStore:
    """Get global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
