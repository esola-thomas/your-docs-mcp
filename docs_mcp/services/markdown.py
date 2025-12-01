"""Markdown parsing with YAML frontmatter support."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

from docs_mcp.models.document import Document
from docs_mcp.security.path_validator import validate_path
from docs_mcp.services.cache import get_cache
from docs_mcp.utils.logger import audit_log, logger


class MarkdownParseError(Exception):
    """Raised when markdown parsing fails."""

    pass


def parse_markdown_with_metadata(
    file_path: Path,
    doc_root: Path,
    allow_hidden: bool = False,
) -> Document:
    """Parse a markdown file and extract frontmatter metadata.

    Args:
        file_path: Path to markdown file
        doc_root: Documentation root for validation
        allow_hidden: Whether to allow hidden files

    Returns:
        Document object with parsed content and metadata

    Raises:
        MarkdownParseError: If parsing fails
    """
    # Validate path
    try:
        validated_path = validate_path(file_path, doc_root, allow_hidden)
    except Exception as e:
        raise MarkdownParseError(f"Path validation failed: {e}") from e

    # Check cache
    cache = get_cache()
    cache_key = f"markdown:{validated_path}"
    cached = cache.get(cache_key, validated_path)
    if cached:
        return cast(Document, cached)

    # Read file
    try:
        content = validated_path.read_text(encoding="utf-8")
        stats = validated_path.stat()
    except Exception as e:
        audit_log(
            "file_access_error",
            {"path": str(validated_path), "error": str(e)},
        )
        raise MarkdownParseError(f"Failed to read file: {e}") from e

    # Parse frontmatter
    frontmatter, body = _extract_frontmatter(content)

    # Generate URI
    relative_path = validated_path.relative_to(doc_root)
    uri = _generate_uri(relative_path)

    # Extract title
    title = _extract_title(frontmatter, body, validated_path.name)

    # Create document
    document = Document(
        file_path=validated_path,
        relative_path=relative_path,
        uri=uri,
        title=title,
        content=body,
        frontmatter=frontmatter,
        tags=frontmatter.get("tags", []),
        category=frontmatter.get("category"),
        order=frontmatter.get("order", 999),
        parent=frontmatter.get("parent"),
        last_modified=datetime.fromtimestamp(stats.st_mtime),
        size_bytes=stats.st_size,
    )

    # Cache the parsed document
    cache.set(cache_key, document, file_path=validated_path)

    # Audit log file access
    audit_log(
        "file_access",
        {
            "path": str(validated_path),
            "uri": uri,
            "title": title,
            "size": stats.st_size,
        },
    )

    return document


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content.

    Args:
        content: Markdown content

    Returns:
        Tuple of (frontmatter dict, body content)
    """
    # Check for frontmatter delimiters
    if not content.startswith("---"):
        return {}, content

    # Find closing delimiter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    # Parse YAML
    frontmatter_raw = parts[1].strip()
    body = parts[2].strip()

    if not frontmatter_raw:
        return {}, body

    try:
        frontmatter = yaml.safe_load(frontmatter_raw)
        if not isinstance(frontmatter, dict):
            logger.warning(f"Frontmatter is not a dict: {type(frontmatter)}")
            return {}, content
        return frontmatter, body
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML frontmatter: {e}")
        # Gracefully fall back to treating entire content as body
        return {}, content


def _extract_title(frontmatter: dict[str, Any], body: str, filename: str) -> str:
    """Extract title from frontmatter, markdown heading, or filename.

    Args:
        frontmatter: Parsed frontmatter dict
        body: Markdown body content
        filename: Source filename

    Returns:
        Document title
    """
    # Try frontmatter first
    if "title" in frontmatter:
        return str(frontmatter["title"])

    # Try first h1 heading in markdown (not h2, h3, etc.)
    heading_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if heading_match:
        return heading_match.group(1).strip()

    # Fall back to filename without extension
    return Path(filename).stem.replace("-", " ").replace("_", " ").title()


def _generate_uri(relative_path: Path) -> str:
    """Generate URI for a document based on relative path.

    Args:
        relative_path: Path relative to doc root

    Returns:
        URI string (e.g., "docs://guides/security/authentication")
    """
    # Remove file extension
    path_without_ext = relative_path.with_suffix("")

    # Convert to URI format
    parts = path_without_ext.parts
    uri = "docs://" + "/".join(parts)

    return uri


def scan_markdown_files(
    source_path: Path,
    doc_root: Path,
    recursive: bool = True,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    allow_hidden: bool = False,
) -> list[Document]:
    """Scan directory for markdown files and parse them.

    Args:
        source_path: Directory to scan
        doc_root: Documentation root for URI generation
        recursive: Whether to scan subdirectories
        include_patterns: File patterns to include
        exclude_patterns: Patterns to exclude
        allow_hidden: Whether to allow hidden files

    Returns:
        List of parsed Document objects
    """
    if include_patterns is None:
        include_patterns = ["*.md", "*.mdx"]

    if exclude_patterns is None:
        exclude_patterns = ["node_modules", ".git", "_*"]

    documents: list[Document] = []

    # Validate source path
    try:
        validated_path = validate_path(source_path, doc_root, allow_hidden=True)
    except Exception as e:
        logger.error(f"Source path validation failed: {e}")
        return documents

    # Scan for markdown files
    try:
        paths: list[Path] = []
        if recursive:
            for pattern in include_patterns:
                paths.extend(validated_path.rglob(pattern))
        else:
            for pattern in include_patterns:
                paths.extend(validated_path.glob(pattern))

        # Filter out excluded paths
        filtered_paths = []
        for path in paths:
            # Check if any part of the path matches exclude patterns
            should_exclude = False
            for exclude in exclude_patterns:
                for part in path.parts:
                    if re.match(exclude.replace("*", ".*"), part):
                        should_exclude = True
                        break
                if should_exclude:
                    break

            if not should_exclude:
                filtered_paths.append(path)

        logger.info(f"Found {len(filtered_paths)} markdown files in {validated_path}")

        # Parse each file
        for file_path in filtered_paths:
            try:
                doc = parse_markdown_with_metadata(file_path, doc_root, allow_hidden)
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to scan directory {validated_path}: {e}")

    return documents
