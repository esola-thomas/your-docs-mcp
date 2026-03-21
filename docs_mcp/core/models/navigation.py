"""Navigation and search data models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Category(BaseModel):
    """Logical grouping of documentation at any hierarchy level."""

    name: str
    label: str
    uri: str
    parent_uri: str | None = None
    depth: int
    child_categories: list[str] = Field(default_factory=list)
    child_documents: list[str] = Field(default_factory=list)
    document_count: int = 0
    source_category: str

    @property
    def breadcrumbs(self) -> list[dict[str, str]]:
        """Generate breadcrumb navigation to this category."""
        if not self.uri.startswith("docs://"):
            return []

        path = self.uri.replace("docs://", "")
        if not path:
            return []

        parts = path.split("/")
        return [
            {"name": part, "uri": f"docs://{'/'.join(parts[: i + 1])}"}
            for i, part in enumerate(parts)
        ]

    @property
    def is_root(self) -> bool:
        """Check if this is a root category."""
        return self.depth == 0


class SearchResult(BaseModel):
    """Match from a search query."""

    document_uri: str
    title: str
    excerpt: str
    breadcrumbs: list[str]
    category: str
    relevance_score: float
    match_type: Literal["full_text", "metadata", "title", "semantic"]
    highlighted_excerpt: str = ""

    @property
    def breadcrumb_string(self) -> str:
        """Human-readable breadcrumb path."""
        return " > ".join(self.breadcrumbs)


class NavigationContext(BaseModel):
    """Current position in documentation hierarchy."""

    current_uri: str
    current_type: Literal["root", "category", "document"]
    parent_uri: str | None = None
    breadcrumbs: list[dict[str, str]] = Field(default_factory=list)
    children: list[dict[str, Any]] = Field(default_factory=list)
    sibling_count: int = 0
    navigation_options: dict[str, str] = Field(default_factory=dict)

    @property
    def can_navigate_up(self) -> bool:
        """Whether parent navigation is possible."""
        return self.parent_uri is not None

    @property
    def can_navigate_down(self) -> bool:
        """Whether child navigation is possible."""
        return len(self.children) > 0
