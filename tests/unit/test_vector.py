"""Unit tests for vector search service with persistence."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from docs_mcp.models.document import Document
from docs_mcp.services.vector import VectorStore, _content_hash, get_vector_store


def _make_doc(uri: str = "docs://test", title: str = "Test", content: str = "Content") -> Document:
    """Helper to create a Document for testing."""
    return Document(
        uri=uri,
        title=title,
        content=content,
        category="test",
        file_path=Path("/tmp/test.md"),
        relative_path=Path("test.md"),
        last_modified=datetime(2025, 1, 1),
        size_bytes=100,
    )


class TestContentHash:
    """Test _content_hash helper."""

    def test_deterministic(self):
        """Same inputs produce the same hash."""
        h1 = _content_hash("Title", "Content")
        h2 = _content_hash("Title", "Content")
        assert h1 == h2

    def test_different_title_different_hash(self):
        """Different title produces a different hash."""
        h1 = _content_hash("Title A", "Content")
        h2 = _content_hash("Title B", "Content")
        assert h1 != h2

    def test_different_content_different_hash(self):
        """Different content produces a different hash."""
        h1 = _content_hash("Title", "Content A")
        h2 = _content_hash("Title", "Content B")
        assert h1 != h2

    def test_truncates_content_at_2000(self):
        """Hash only considers first 2000 chars of content."""
        base = "x" * 2000
        h1 = _content_hash("T", base + "AAAA")
        h2 = _content_hash("T", base + "BBBB")
        assert h1 == h2


class TestVectorStoreInit:
    """Test VectorStore initialization modes."""

    @patch("docs_mcp.services.vector.chromadb", None)
    def test_no_chromadb_installed(self):
        """When chromadb is not installed, collection is None."""
        store = VectorStore()
        assert store.collection is None

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_ephemeral_when_no_persist_dir(self, mock_ef, mock_chromadb):
        """When persist_directory is None, uses ephemeral Client."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore(persist_directory=None)

        mock_chromadb.Client.assert_called_once()
        mock_chromadb.PersistentClient.assert_not_called()
        assert store.collection == mock_collection

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_persistent_when_persist_dir_set(self, mock_ef, mock_chromadb, tmp_path):
        """When persist_directory is set, uses PersistentClient."""
        persist_dir = str(tmp_path / "vectordb")
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore(persist_directory=persist_dir)

        mock_chromadb.PersistentClient.assert_called_once()
        mock_chromadb.Client.assert_not_called()
        assert store.collection == mock_collection

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_persist_dir_created_if_missing(self, mock_ef, mock_chromadb, tmp_path):
        """Persistence directory is created if it does not exist."""
        persist_dir = tmp_path / "new_dir" / "vectordb"
        assert not persist_dir.exists()

        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = MagicMock()

        VectorStore(persist_directory=str(persist_dir))

        assert persist_dir.exists()

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_reindex_deletes_collection(self, mock_ef, mock_chromadb):
        """When reindex=True, the existing collection is deleted first."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_client.get_or_create_collection.return_value = MagicMock()

        VectorStore(persist_directory=None, reindex=True)

        mock_client.delete_collection.assert_called_once_with(name="documents")

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_reindex_false_does_not_delete(self, mock_ef, mock_chromadb):
        """When reindex=False, the collection is not deleted."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_client.get_or_create_collection.return_value = MagicMock()

        VectorStore(persist_directory=None, reindex=False)

        mock_client.delete_collection.assert_not_called()

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_uses_get_or_create_collection(self, mock_ef, mock_chromadb):
        """Uses get_or_create_collection for idempotent init."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_client.get_or_create_collection.return_value = MagicMock()

        VectorStore()

        mock_client.get_or_create_collection.assert_called_once()


class TestAddDocumentsSkipsUnchanged:
    """Test that add_documents only re-embeds changed documents."""

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_skips_unchanged_documents(self, mock_ef, mock_chromadb):
        """Documents with matching content_hash are skipped."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        doc = _make_doc(uri="docs://a", title="A", content="Content A")
        expected_hash = _content_hash("A", "Content A")

        # Simulate existing doc with matching hash
        mock_collection.get.return_value = {
            "ids": ["docs://a"],
            "metadatas": [{"content_hash": expected_hash}],
        }

        store = VectorStore()
        store.add_documents([doc])

        # No upsert should be called since doc is unchanged
        mock_collection.upsert.assert_not_called()

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_reembeds_changed_documents(self, mock_ef, mock_chromadb):
        """Documents with different content_hash are re-embedded."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        doc = _make_doc(uri="docs://a", title="A", content="New Content")

        # Simulate existing doc with old hash
        mock_collection.get.return_value = {
            "ids": ["docs://a"],
            "metadatas": [{"content_hash": "old_hash_value"}],
        }

        store = VectorStore()
        store.add_documents([doc])

        mock_collection.upsert.assert_called_once()
        call_kwargs = mock_collection.upsert.call_args
        assert "docs://a" in call_kwargs.kwargs.get("ids", call_kwargs[1].get("ids", []))

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_embeds_new_documents(self, mock_ef, mock_chromadb):
        """New documents (no existing entry) are embedded."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        doc = _make_doc(uri="docs://new", title="New", content="New Content")

        # No existing docs
        mock_collection.get.return_value = {"ids": [], "metadatas": []}

        store = VectorStore()
        store.add_documents([doc])

        mock_collection.upsert.assert_called_once()

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_stores_content_hash_in_metadata(self, mock_ef, mock_chromadb):
        """Upserted documents include content_hash in metadata."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        doc = _make_doc(uri="docs://x", title="X", content="Content X")
        expected_hash = _content_hash("X", "Content X")

        mock_collection.get.return_value = {"ids": [], "metadatas": []}

        store = VectorStore()
        store.add_documents([doc])

        call_args = mock_collection.upsert.call_args
        metadatas = call_args.kwargs.get("metadatas", call_args[1].get("metadatas", []))
        assert metadatas[0]["content_hash"] == expected_hash

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_mixed_changed_and_unchanged(self, mock_ef, mock_chromadb):
        """Only changed docs are upserted when some are unchanged."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        doc_a = _make_doc(uri="docs://a", title="A", content="Content A")
        doc_b = _make_doc(uri="docs://b", title="B", content="Changed B")
        hash_a = _content_hash("A", "Content A")

        mock_collection.get.return_value = {
            "ids": ["docs://a", "docs://b"],
            "metadatas": [
                {"content_hash": hash_a},  # unchanged
                {"content_hash": "old_hash"},  # changed
            ],
        }

        store = VectorStore()
        store.add_documents([doc_a, doc_b])

        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args
        ids = call_args.kwargs.get("ids", call_args[1].get("ids", []))
        assert "docs://b" in ids
        assert "docs://a" not in ids

    @patch("docs_mcp.services.vector.chromadb")
    @patch("docs_mcp.services.vector.embedding_functions")
    def test_empty_documents_list(self, mock_ef, mock_chromadb):
        """Empty document list is handled gracefully."""
        mock_client = MagicMock()
        mock_chromadb.Client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore()
        store.add_documents([])

        mock_collection.get.assert_not_called()
        mock_collection.upsert.assert_not_called()


class TestGetVectorStore:
    """Test get_vector_store factory function."""

    def setup_method(self):
        """Reset the global singleton before each test."""
        import docs_mcp.services.vector as mod

        mod._vector_store = None

    @patch("docs_mcp.services.vector.chromadb", None)
    def test_returns_vector_store_instance(self):
        """Factory returns a VectorStore instance."""
        store = get_vector_store()
        assert isinstance(store, VectorStore)

    @patch("docs_mcp.services.vector.chromadb", None)
    def test_returns_singleton(self):
        """Subsequent calls return the same instance."""
        store1 = get_vector_store()
        store2 = get_vector_store()
        assert store1 is store2

    @patch("docs_mcp.services.vector.chromadb", None)
    def test_passes_persist_directory(self):
        """persist_directory is passed to VectorStore on first call."""
        with patch("docs_mcp.services.vector.VectorStore") as mock_vs:
            mock_vs.return_value = MagicMock()
            get_vector_store(persist_directory="/tmp/test_vdb", reindex=True)
            mock_vs.assert_called_once_with(
                persist_directory="/tmp/test_vdb",
                reindex=True,
            )


class TestConfigIntegration:
    """Test config fields for vector persistence."""

    def test_default_vector_persist_dir(self):
        """Default persist dir is ~/.your-docs-mcp/vectordb."""
        from docs_mcp.config import ServerConfig

        config = ServerConfig()
        assert config.vector_persist_dir is not None
        assert str(config.vector_persist_dir) == "~/.your-docs-mcp/vectordb"

    def test_custom_vector_persist_dir_from_env(self, tmp_path, monkeypatch):
        """Persist dir can be configured via env var."""
        from docs_mcp.config import ServerConfig

        custom_path = str(tmp_path / "custom_vdb")
        monkeypatch.setenv("MCP_DOCS_VECTOR_PERSIST_DIR", custom_path)
        config = ServerConfig()
        assert str(config.vector_persist_dir) == custom_path

    def test_reindex_default_false(self):
        """Reindex defaults to False."""
        from docs_mcp.config import ServerConfig

        config = ServerConfig()
        assert config.reindex is False

    def test_reindex_from_env(self, monkeypatch):
        """Reindex can be set via env var."""
        from docs_mcp.config import ServerConfig

        monkeypatch.setenv("MCP_DOCS_REINDEX", "true")
        config = ServerConfig()
        assert config.reindex is True


class TestReindexCliFlag:
    """Test --reindex CLI flag."""

    def test_reindex_flag_sets_config(self, tmp_path, monkeypatch):
        """--reindex CLI flag sets config.reindex to True."""
        from docs_mcp.__main__ import _validate_config_and_setup

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        monkeypatch.setenv("DOCS_ROOT", str(docs_dir))
        monkeypatch.setattr("sys.argv", ["test", "--reindex"])

        config = _validate_config_and_setup()
        assert config.reindex is True

    def test_no_reindex_flag_keeps_default(self, tmp_path, monkeypatch):
        """Without --reindex flag, config.reindex stays False."""
        from docs_mcp.__main__ import _validate_config_and_setup

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        monkeypatch.setenv("DOCS_ROOT", str(docs_dir))
        monkeypatch.setattr("sys.argv", ["test"])

        config = _validate_config_and_setup()
        assert config.reindex is False
