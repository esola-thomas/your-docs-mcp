"""Unit tests for vector search service."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from docs_mcp.models.document import Document


def _make_document(uri: str, title: str, content: str, category: str = "guides") -> Document:
    """Helper to create a Document for testing."""
    return Document(
        uri=uri,
        title=title,
        content=content,
        category=category,
        tags=[],
        file_path=Path(f"/docs/{uri.replace('docs://', '')}.md"),
        relative_path=Path(f"{uri.replace('docs://', '')}.md"),
        size_bytes=len(content),
        last_modified=datetime.now(timezone.utc),
    )


class TestVectorStoreNoChromaDB:
    """Test VectorStore when ChromaDB is not installed (graceful degradation)."""

    def test_init_without_chromadb_sets_collection_none(self):
        """VectorStore initialises with collection=None when ChromaDB is missing."""
        # Temporarily hide chromadb from the module
        with patch.dict(sys.modules, {"chromadb": None, "chromadb.utils": None,
                                      "chromadb.utils.embedding_functions": None}):
            # Force re-import of vector module with chromadb absent
            import importlib
            import docs_mcp.services.vector as vec_mod
            importlib.reload(vec_mod)

            store = vec_mod.VectorStore()
            assert store.collection is None

            # Restore module to its original state
            importlib.reload(vec_mod)


class TestVectorStoreWithChromaDBPresent:
    """Test VectorStore.__init__ when ChromaDB IS importable (mocked)."""

    def test_init_with_chromadb_available(self):
        """VectorStore sets collection when ChromaDB client succeeds."""
        import importlib
        import docs_mcp.services.vector as vec_mod

        mock_chromadb = MagicMock()
        mock_ef = MagicMock()
        mock_client = MagicMock()
        mock_collection = MagicMock()

        mock_chromadb.Client.return_value = mock_client
        mock_client.create_collection.return_value = mock_collection

        mock_ef_module = MagicMock()
        mock_ef_module.SentenceTransformerEmbeddingFunction.return_value = mock_ef

        # Inject mocked chromadb into the module so the __init__ code path runs
        original_chromadb = vec_mod.chromadb
        original_ef = vec_mod.embedding_functions
        vec_mod.chromadb = mock_chromadb
        vec_mod.embedding_functions = mock_ef_module

        try:
            store = vec_mod.VectorStore()
            assert store.collection is mock_collection
            mock_chromadb.Client.assert_called_once()
            mock_client.create_collection.assert_called_once()
        finally:
            vec_mod.chromadb = original_chromadb
            vec_mod.embedding_functions = original_ef

    def test_init_with_chromadb_client_exception(self):
        """VectorStore sets collection=None when ChromaDB client raises."""
        import docs_mcp.services.vector as vec_mod

        mock_chromadb = MagicMock()
        mock_chromadb.Client.side_effect = RuntimeError("DB init failed")

        mock_ef_module = MagicMock()

        original_chromadb = vec_mod.chromadb
        original_ef = vec_mod.embedding_functions
        vec_mod.chromadb = mock_chromadb
        vec_mod.embedding_functions = mock_ef_module

        try:
            store = vec_mod.VectorStore()
            assert store.collection is None
        finally:
            vec_mod.chromadb = original_chromadb
            vec_mod.embedding_functions = original_ef

    def test_add_documents_no_op_without_chromadb(self):
        """add_documents is a no-op when collection is None."""
        from docs_mcp.services.vector import VectorStore

        store = VectorStore.__new__(VectorStore)
        store.collection = None

        doc = _make_document("docs://test/doc", "Test Doc", "Some content")
        # Should not raise
        store.add_documents([doc])

    def test_add_documents_empty_list_no_op(self):
        """add_documents is a no-op for empty document list."""
        from docs_mcp.services.vector import VectorStore

        store = VectorStore.__new__(VectorStore)
        store.collection = MagicMock()

        store.add_documents([])
        store.collection.add.assert_not_called()

    def test_search_returns_empty_without_collection(self):
        """search returns [] when collection is None."""
        from docs_mcp.services.vector import VectorStore

        store = VectorStore.__new__(VectorStore)
        store.collection = None

        results = store.search("anything")
        assert results == []


class TestVectorStoreWithMockedChromaDB:
    """Test VectorStore with a fully mocked ChromaDB backend."""

    @pytest.fixture
    def mock_collection(self):
        """Return a MagicMock acting as a ChromaDB collection."""
        return MagicMock()

    @pytest.fixture
    def store(self, mock_collection):
        """Create a VectorStore with its collection replaced by a mock."""
        from docs_mcp.services.vector import VectorStore

        s = VectorStore.__new__(VectorStore)
        s.collection = mock_collection
        return s

    @pytest.fixture
    def sample_docs(self):
        return [
            _make_document("docs://guides/intro", "Intro Guide", "Introduction content", "guides"),
            _make_document("docs://api/auth", "Auth API", "Authentication details", "api"),
        ]

    # ------------------------------------------------------------------
    # add_documents
    # ------------------------------------------------------------------

    def test_add_documents_calls_collection_add(self, store, mock_collection, sample_docs):
        """add_documents should call collection.add once for a small batch."""
        store.add_documents(sample_docs)

        assert mock_collection.add.call_count == 1
        call_kwargs = mock_collection.add.call_args[1]
        assert len(call_kwargs["ids"]) == 2

    def test_add_documents_batches_correctly(self, store, mock_collection):
        """add_documents batches 100 docs per call."""
        docs = [
            _make_document(f"docs://cat/doc{i}", f"Doc {i}", f"Content {i}")
            for i in range(250)
        ]
        store.add_documents(docs)

        # 250 docs → 3 batches: 100, 100, 50
        assert mock_collection.add.call_count == 3

    def test_add_documents_uses_title_and_content(self, store, mock_collection):
        """add_documents combines title and content for embeddings."""
        doc = _make_document("docs://x/y", "My Title", "My content here")
        store.add_documents([doc])

        docs_text = mock_collection.add.call_args[1]["documents"]
        assert "My Title" in docs_text[0]
        assert "My content here" in docs_text[0]

    def test_add_documents_truncates_long_content(self, store, mock_collection):
        """add_documents only uses the first 2000 chars of content."""
        long_content = "x" * 5000
        doc = _make_document("docs://x/y", "Title", long_content)
        store.add_documents([doc])

        docs_text = mock_collection.add.call_args[1]["documents"]
        # The embedded text should not exceed title + 2000 content chars (plus separator)
        assert len(docs_text[0]) <= len("Title") + 2 + 2000

    def test_add_documents_builds_correct_metadata(self, store, mock_collection, sample_docs):
        """add_documents stores correct metadata for each document."""
        store.add_documents(sample_docs)

        metadatas = mock_collection.add.call_args[1]["metadatas"]
        assert metadatas[0]["title"] == "Intro Guide"
        assert metadatas[0]["category"] == "guides"
        assert metadatas[0]["uri"] == "docs://guides/intro"

    def test_add_documents_uses_uri_as_id(self, store, mock_collection, sample_docs):
        """add_documents uses document URI as collection ID."""
        store.add_documents(sample_docs)

        ids = mock_collection.add.call_args[1]["ids"]
        assert "docs://guides/intro" in ids
        assert "docs://api/auth" in ids

    def test_add_documents_falls_back_to_uncategorized(self, store, mock_collection):
        """add_documents uses 'uncategorized' when document category is None."""
        doc = _make_document("docs://x/y", "Title", "Content", category=None)
        doc = doc.model_copy(update={"category": None})
        store.add_documents([doc])

        metadatas = mock_collection.add.call_args[1]["metadatas"]
        assert metadatas[0]["category"] == "uncategorized"

    def test_add_documents_handles_collection_exception(self, store, mock_collection, sample_docs):
        """add_documents logs and swallows collection errors."""
        mock_collection.add.side_effect = RuntimeError("DB error")
        # Should not raise
        store.add_documents(sample_docs)

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    def test_search_returns_results(self, store, mock_collection):
        """search returns formatted results from collection.query."""
        mock_collection.query.return_value = {
            "ids": [["docs://guides/intro", "docs://api/auth"]],
            "distances": [[0.1, 0.5]],
            "metadatas": [[
                {"title": "Intro", "category": "guides", "uri": "docs://guides/intro"},
                {"title": "Auth", "category": "api", "uri": "docs://api/auth"},
            ]],
        }

        results = store.search("intro guide", limit=5)

        assert len(results) == 2
        assert results[0]["uri"] == "docs://guides/intro"
        assert results[0]["score"] == pytest.approx(0.9)
        assert results[1]["uri"] == "docs://api/auth"
        assert results[1]["score"] == pytest.approx(0.5)

    def test_search_clamps_score_to_zero_for_large_distance(self, store, mock_collection):
        """search clamps score to 0.0 when cosine distance >= 1.0."""
        mock_collection.query.return_value = {
            "ids": [["docs://x/y"]],
            "distances": [[1.5]],
            "metadatas": [[{"title": "T", "category": "c", "uri": "docs://x/y"}]],
        }

        results = store.search("query")
        assert results[0]["score"] == 0.0

    def test_search_returns_empty_on_no_ids(self, store, mock_collection):
        """search returns [] when query returns empty ids."""
        mock_collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
        }

        results = store.search("nothing")
        assert results == []

    def test_search_handles_missing_metadata(self, store, mock_collection):
        """search returns empty metadata dict when metadatas list is shorter."""
        mock_collection.query.return_value = {
            "ids": [["docs://x/y"]],
            "distances": [[0.2]],
            "metadatas": [[]],  # Empty metadatas
        }

        results = store.search("query")
        assert results[0]["metadata"] == {}

    def test_search_passes_limit_to_query(self, store, mock_collection):
        """search forwards the limit parameter to collection.query."""
        mock_collection.query.return_value = {
            "ids": [[]], "distances": [[]], "metadatas": [[]]
        }
        store.search("query", limit=7)

        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["n_results"] == 7

    def test_search_handles_query_exception(self, store, mock_collection):
        """search logs and returns [] on collection.query exception."""
        mock_collection.query.side_effect = RuntimeError("Query failed")
        results = store.search("query")
        assert results == []


class TestGetVectorStore:
    """Test the get_vector_store singleton factory."""

    def test_get_vector_store_returns_instance(self):
        """get_vector_store returns a VectorStore instance."""
        import docs_mcp.services.vector as vec_mod

        # Reset the global singleton for a clean test
        original = vec_mod._vector_store
        vec_mod._vector_store = None

        try:
            store = vec_mod.get_vector_store()
            assert isinstance(store, vec_mod.VectorStore)
        finally:
            vec_mod._vector_store = original

    def test_get_vector_store_returns_same_instance(self):
        """get_vector_store returns the same singleton on repeated calls."""
        import docs_mcp.services.vector as vec_mod

        original = vec_mod._vector_store
        vec_mod._vector_store = None

        try:
            store1 = vec_mod.get_vector_store()
            store2 = vec_mod.get_vector_store()
            assert store1 is store2
        finally:
            vec_mod._vector_store = original
