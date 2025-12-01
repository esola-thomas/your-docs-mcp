"""Path validation to prevent directory traversal attacks."""

from pathlib import Path

from docs_mcp.utils.logger import audit_log, logger


class PathValidationError(Exception):
    """Raised when a path fails validation."""

    pass


def validate_path(
    requested_path: str | Path,
    allowed_root: str | Path,
    allow_hidden: bool = False,
) -> Path:
    """Validate that a requested path is safe and within allowed directory.

    Args:
        requested_path: The path to validate
        allowed_root: The root directory that paths must be within
        allow_hidden: Whether to allow hidden files (starting with '.')

    Returns:
        Resolved absolute path if valid

    Raises:
        PathValidationError: If path is invalid or outside allowed root
    """
    try:
        # Convert to Path objects and resolve
        requested = Path(requested_path).expanduser().resolve()
        root = Path(allowed_root).expanduser().resolve()

        # Check if path is within allowed root
        try:
            requested.relative_to(root)
        except ValueError:
            audit_log(
                "path_violation",
                {
                    "requested": str(requested_path),
                    "resolved": str(requested),
                    "allowed_root": str(root),
                    "reason": "outside_allowed_directory",
                },
            )
            raise PathValidationError(f"Path is outside allowed directory: {requested_path}")

        # Check for hidden files/directories unless explicitly allowed
        if not allow_hidden:
            for part in requested.parts:
                if part.startswith(".") and part not in (".", ".."):
                    audit_log(
                        "path_violation",
                        {
                            "requested": str(requested_path),
                            "resolved": str(requested),
                            "reason": "hidden_file",
                        },
                    )
                    raise PathValidationError(
                        f"Access to hidden files is not allowed: {requested_path}"
                    )

        # Check that path exists (optional - caller can handle)
        if not requested.exists():
            logger.debug(f"Path does not exist (but passed validation): {requested}")

        # Log successful validation for audit
        audit_log(
            "path_validated",
            {
                "requested": str(requested_path),
                "resolved": str(requested),
                "allowed_root": str(root),
            },
        )

        return requested

    except PathValidationError:
        raise
    except Exception as e:
        audit_log(
            "path_violation",
            {
                "requested": str(requested_path),
                "reason": "validation_error",
                "error": str(e),
            },
        )
        raise PathValidationError(f"Invalid path: {e}") from e


def validate_relative_path(
    relative_path: str,
    allowed_root: str | Path,
    allow_hidden: bool = False,
) -> Path:
    """Validate a relative path and resolve it against allowed root.

    Args:
        relative_path: Relative path string
        allowed_root: Root directory to resolve against
        allow_hidden: Whether to allow hidden files

    Returns:
        Resolved absolute path if valid

    Raises:
        PathValidationError: If path is invalid
    """
    root = Path(allowed_root).expanduser().resolve()
    full_path = root / relative_path
    return validate_path(full_path, root, allow_hidden)


def is_path_safe(
    requested_path: str | Path,
    allowed_root: str | Path,
    allow_hidden: bool = False,
) -> bool:
    """Check if a path is safe without raising exceptions.

    Args:
        requested_path: The path to check
        allowed_root: The root directory that paths must be within
        allow_hidden: Whether to allow hidden files

    Returns:
        True if path is safe, False otherwise
    """
    try:
        validate_path(requested_path, allowed_root, allow_hidden)
        return True
    except PathValidationError:
        return False


def detect_symlink_cycle(path: Path, max_depth: int = 20) -> Path | None:
    """Detect circular symlinks in a path.

    Args:
        path: Path to check
        max_depth: Maximum depth to follow symlinks

    Returns:
        The path where the cycle was detected, or None if no cycle found
    """
    visited = set()
    current = path
    depth = 0

    while current.is_symlink() and depth < max_depth:
        if current in visited:
            audit_log(
                "symlink_cycle_detected",
                {"path": str(path), "cycle_at": str(current)},
            )
            return current

        visited.add(current)
        current = current.readlink()
        depth += 1

    if depth >= max_depth:
        audit_log(
            "symlink_depth_exceeded",
            {"path": str(path), "max_depth": max_depth},
        )
        return current

    return None
