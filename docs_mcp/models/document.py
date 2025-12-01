"""Document and source data models."""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DocumentationSource(BaseModel):
    """Represents a configured location containing documentation files."""

    path: Path
    category: str
    label: str
    recursive: bool = True
    include_patterns: list[str] = Field(default_factory=lambda: ["*.md", "*.mdx"])
    exclude_patterns: list[str] = Field(default_factory=lambda: ["node_modules", ".git", "_*"])
    format_type: str = "markdown"


class Document(BaseModel):
    """Individual markdown file with optional frontmatter metadata."""

    file_path: Path
    relative_path: Path
    uri: str
    title: str
    content: str = ""
    frontmatter: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    order: int = 999
    parent: str | None = None
    last_modified: datetime
    size_bytes: int

    @property
    def breadcrumbs(self) -> list[str]:
        """Generate breadcrumb path from root to document."""
        return list(self.relative_path.parts[:-1])

    def excerpt(self, max_length: int = 200) -> str:
        """Extract first N characters of content, excluding frontmatter.

        Args:
            max_length: Maximum length of excerpt

        Returns:
            Content excerpt
        """
        # Remove frontmatter delimiter if present
        content = self.content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        # Get first paragraph or max_length chars
        paragraphs = content.split("\n\n")
        excerpt = paragraphs[0] if paragraphs else content

        if len(excerpt) > max_length:
            excerpt = excerpt[:max_length].rsplit(" ", 1)[0] + "..."

        return excerpt.strip()
