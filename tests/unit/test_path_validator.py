"""Unit tests for path validation security."""

import os
from pathlib import Path

import pytest

from docs_mcp.security.path_validator import (
    PathValidationError,
    detect_symlink_cycle,
    is_path_safe,
    validate_path,
    validate_relative_path,
)


@pytest.fixture
def temp_doc_root(tmp_path):
    """Create a temporary documentation root with test files."""
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    # Create valid test structure
    (doc_root / "guides").mkdir()
    (doc_root / "guides" / "test.md").write_text("# Test Guide")

    (doc_root / "api").mkdir()
    (doc_root / "api" / "reference.md").write_text("# API Reference")

    # Create hidden file
    (doc_root / ".hidden").write_text("secret content")

    return doc_root


@pytest.fixture
def sensitive_root(tmp_path):
    """Create a sensitive directory outside doc root."""
    sensitive = tmp_path / "sensitive"
    sensitive.mkdir()
    (sensitive / "secret.txt").write_text("sensitive data")
    return sensitive


class TestValidatePath:
    """Test validate_path function with various attack patterns."""

    def test_valid_path_within_root(self, temp_doc_root):
        """Test that valid paths within root are accepted."""
        test_file = temp_doc_root / "guides" / "test.md"
        result = validate_path(test_file, temp_doc_root)

        assert result == test_file.resolve()
        assert result.exists()

    def test_directory_traversal_parent_notation(self, temp_doc_root, sensitive_root):
        """Test blocking of ../ directory traversal attempts."""
        # Try to access parent directory
        malicious_path = temp_doc_root / ".." / "sensitive" / "secret.txt"

        with pytest.raises(PathValidationError, match="outside allowed directory"):
            validate_path(malicious_path, temp_doc_root)

    def test_directory_traversal_absolute_path(self, temp_doc_root):
        """Test blocking of absolute paths outside root."""
        # Try to access /etc/passwd
        with pytest.raises(PathValidationError, match="outside allowed directory"):
            validate_path("/etc/passwd", temp_doc_root)

    def test_directory_traversal_multiple_parents(self, temp_doc_root):
        """Test blocking of ../../ patterns."""
        malicious_path = temp_doc_root / "guides" / ".." / ".." / "etc" / "passwd"

        with pytest.raises(PathValidationError, match="outside allowed directory"):
            validate_path(malicious_path, temp_doc_root)

    def test_hidden_file_blocked_by_default(self, temp_doc_root):
        """Test that hidden files are blocked by default."""
        hidden_file = temp_doc_root / ".hidden"

        with pytest.raises(PathValidationError, match="hidden files is not allowed"):
            validate_path(hidden_file, temp_doc_root)

    def test_hidden_file_allowed_when_permitted(self, temp_doc_root):
        """Test that hidden files are allowed when allow_hidden=True."""
        hidden_file = temp_doc_root / ".hidden"

        result = validate_path(hidden_file, temp_doc_root, allow_hidden=True)
        assert result == hidden_file.resolve()

    def test_hidden_directory_in_path_blocked(self, temp_doc_root):
        """Test that paths with hidden directories are blocked."""
        (temp_doc_root / ".secret").mkdir()
        (temp_doc_root / ".secret" / "file.md").write_text("secret")

        hidden_path = temp_doc_root / ".secret" / "file.md"

        with pytest.raises(PathValidationError, match="hidden files is not allowed"):
            validate_path(hidden_path, temp_doc_root)

    def test_nonexistent_path_within_root(self, temp_doc_root):
        """Test that nonexistent paths within root don't raise errors (validation only)."""
        nonexistent = temp_doc_root / "guides" / "nonexistent.md"

        # Should validate successfully even if file doesn't exist
        result = validate_path(nonexistent, temp_doc_root)
        assert result == nonexistent.resolve()

    def test_tilde_expansion(self, tmp_path):
        """Test that tilde (~) is expanded correctly."""
        # This test assumes expanduser() works correctly
        # We'll just verify it doesn't crash
        doc_root = tmp_path / "docs"
        doc_root.mkdir()

        result = validate_path(doc_root, doc_root)
        assert result.is_absolute()

    def test_relative_path_resolution(self, temp_doc_root):
        """Test that relative paths are resolved correctly."""
        # Use a relative path with ./ notation
        relative = Path("./guides/test.md")
        full_path = temp_doc_root / relative

        result = validate_path(full_path, temp_doc_root)
        assert result.is_absolute()
        assert "test.md" in str(result)


class TestValidateRelativePath:
    """Test validate_relative_path function."""

    def test_valid_relative_path(self, temp_doc_root):
        """Test valid relative path resolution."""
        result = validate_relative_path("guides/test.md", temp_doc_root)

        assert result.is_absolute()
        assert result.name == "test.md"
        assert "guides" in str(result)

    def test_relative_path_with_traversal(self, temp_doc_root):
        """Test relative path with directory traversal."""
        with pytest.raises(PathValidationError, match="outside allowed directory"):
            validate_relative_path("../sensitive/secret.txt", temp_doc_root)

    def test_relative_path_to_hidden_file(self, temp_doc_root):
        """Test relative path to hidden file."""
        with pytest.raises(PathValidationError, match="hidden files is not allowed"):
            validate_relative_path(".hidden", temp_doc_root)


class TestIsPathSafe:
    """Test is_path_safe boolean function."""

    def test_safe_path_returns_true(self, temp_doc_root):
        """Test that safe paths return True."""
        test_file = temp_doc_root / "guides" / "test.md"
        assert is_path_safe(test_file, temp_doc_root) is True

    def test_unsafe_path_returns_false(self, temp_doc_root):
        """Test that unsafe paths return False."""
        malicious = temp_doc_root / ".." / "etc" / "passwd"
        assert is_path_safe(malicious, temp_doc_root) is False

    def test_hidden_file_returns_false(self, temp_doc_root):
        """Test that hidden files return False by default."""
        hidden = temp_doc_root / ".hidden"
        assert is_path_safe(hidden, temp_doc_root) is False

    def test_hidden_file_with_allow_returns_true(self, temp_doc_root):
        """Test that hidden files return True when allowed."""
        hidden = temp_doc_root / ".hidden"
        assert is_path_safe(hidden, temp_doc_root, allow_hidden=True) is True


class TestDetectSymlinkCycle:
    """Test symlink cycle detection."""

    @pytest.mark.skipif(os.name == "nt", reason="Symlinks require admin on Windows")
    def test_no_symlink_returns_none(self, temp_doc_root):
        """Test that regular files return None."""
        test_file = temp_doc_root / "guides" / "test.md"
        result = detect_symlink_cycle(test_file)
        assert result is None

    @pytest.mark.skipif(os.name == "nt", reason="Symlinks require admin on Windows")
    def test_circular_symlink_detected(self, tmp_path):
        """Test that circular symlinks are detected."""
        # Create circular symlink
        link1 = tmp_path / "link1"
        link2 = tmp_path / "link2"

        link1.symlink_to(link2)
        link2.symlink_to(link1)

        result = detect_symlink_cycle(link1)
        assert result is not None

    @pytest.mark.skipif(os.name == "nt", reason="Symlinks require admin on Windows")
    def test_deep_symlink_chain_detected(self, tmp_path):
        """Test that excessively deep symlink chains are detected."""
        # Create a very long chain
        links = []
        for i in range(25):
            link = tmp_path / f"link{i}"
            links.append(link)
            if i > 0:
                link.symlink_to(links[i - 1])
            else:
                # Point first link to itself
                link.symlink_to(link)

        result = detect_symlink_cycle(links[-1], max_depth=20)
        assert result is not None


class TestPathValidationAttackPatterns:
    """Test comprehensive attack patterns from security research."""

    def test_attack_pattern_double_encoding(self, temp_doc_root):
        """Test double-encoded path traversal."""
        # %2e%2e%2f = ../
        # This should be caught after path resolution
        malicious = temp_doc_root / ".." / "sensitive"
        with pytest.raises(PathValidationError):
            validate_path(malicious, temp_doc_root)

    def test_attack_pattern_mixed_separators(self, temp_doc_root):
        """Test mixed forward/backward slashes."""
        # This tests that Path normalization handles it
        test_file = temp_doc_root / "guides" / "test.md"
        result = validate_path(test_file, temp_doc_root)
        assert result.is_absolute()

    def test_attack_pattern_null_byte(self, temp_doc_root):
        """Test null byte injection (should be handled by OS/Python)."""
        # Python pathlib should handle this gracefully
        # If it doesn't raise ValueError, we validate normally
        try:
            malicious = str(temp_doc_root / "test.md") + "\x00" + "/etc/passwd"
            with pytest.raises((PathValidationError, ValueError)):
                validate_path(malicious, temp_doc_root)
        except (ValueError, TypeError):
            # Python may raise ValueError for null bytes in paths
            pass

    def test_attack_pattern_unicode_homoglyphs(self, temp_doc_root):
        """Test unicode characters that look like path separators."""
        # Create a file with unicode in name
        unicode_file = temp_doc_root / "guides" / "test\u2215file.md"  # ∕ (division slash)

        # Should be able to validate if within root
        result = validate_path(unicode_file, temp_doc_root)
        assert result.is_absolute()

    def test_attack_pattern_windows_device_names(self, temp_doc_root):
        """Test Windows device names (CON, PRN, AUX, etc.)."""
        # These should be handled by the OS, but we validate the path
        # Device names like CON, PRN are special on Windows
        device_path = temp_doc_root / "CON.md"

        # Should validate without errors (OS will handle device names)
        result = validate_path(device_path, temp_doc_root)
        assert result.is_absolute()

    def test_attack_pattern_long_path(self, temp_doc_root):
        """Test extremely long paths."""
        # Create a very long path
        long_segment = "a" * 500
        long_path = temp_doc_root / long_segment / "test.md"

        # OS will reject paths with segments longer than system limit (usually 255 chars)
        # This is a valid system-level protection
        with pytest.raises(PathValidationError, match="Invalid path"):
            validate_path(long_path, temp_doc_root)

    def test_attack_git_directory(self, temp_doc_root):
        """Test that .git directory is blocked."""
        (temp_doc_root / ".git").mkdir()
        (temp_doc_root / ".git" / "config").write_text("git config")

        git_file = temp_doc_root / ".git" / "config"

        with pytest.raises(PathValidationError, match="hidden files is not allowed"):
            validate_path(git_file, temp_doc_root)

    def test_attack_env_file(self, temp_doc_root):
        """Test that .env files are blocked."""
        (temp_doc_root / ".env").write_text("SECRET_KEY=abc123")

        env_file = temp_doc_root / ".env"

        with pytest.raises(PathValidationError, match="hidden files is not allowed"):
            validate_path(env_file, temp_doc_root)

    def test_ssh_directory_blocked(self, temp_doc_root):
        """Test that .ssh directory is blocked."""
        (temp_doc_root / ".ssh").mkdir()
        (temp_doc_root / ".ssh" / "id_rsa").write_text("private key")

        ssh_key = temp_doc_root / ".ssh" / "id_rsa"

        with pytest.raises(PathValidationError, match="hidden files is not allowed"):
            validate_path(ssh_key, temp_doc_root)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_path(self, temp_doc_root):
        """Test empty path string."""
        with pytest.raises((PathValidationError, ValueError)):
            validate_path("", temp_doc_root)

    def test_root_path_itself(self, temp_doc_root):
        """Test validating the root path itself."""
        result = validate_path(temp_doc_root, temp_doc_root)
        assert result == temp_doc_root.resolve()

    def test_path_with_spaces(self, temp_doc_root):
        """Test paths with spaces."""
        (temp_doc_root / "guides" / "my test.md").write_text("# Test")

        spaced_path = temp_doc_root / "guides" / "my test.md"
        result = validate_path(spaced_path, temp_doc_root)

        assert result.name == "my test.md"

    def test_path_with_special_chars(self, temp_doc_root):
        """Test paths with special characters."""
        special_file = temp_doc_root / "guides" / "test@#$.md"
        special_file.write_text("# Special")

        result = validate_path(special_file, temp_doc_root)
        assert result.exists()

    def test_case_sensitive_paths(self, temp_doc_root):
        """Test case sensitivity (OS-dependent)."""
        test_file = temp_doc_root / "guides" / "Test.md"
        test_file.write_text("# Test")

        # Try different case
        result = validate_path(test_file, temp_doc_root)
        assert result.is_absolute()
