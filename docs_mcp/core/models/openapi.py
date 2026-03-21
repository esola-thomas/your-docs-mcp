"""OpenAPI specification data models."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class APIOperation(BaseModel):
    """Individual API endpoint from OpenAPI specification."""

    operation_id: str
    method: str
    path: str
    uri: str
    tag: str | None = None
    summary: str = ""
    description: str = ""
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = Field(default_factory=dict)
    deprecated: bool = False

    @property
    def full_description(self) -> str:
        """Combine summary and description."""
        if self.summary and self.description:
            return f"{self.summary}\n\n{self.description}"
        return self.summary or self.description

    @property
    def required_parameters(self) -> list[dict[str, Any]]:
        """Filter parameters to only required ones."""
        return [p for p in self.parameters if p.get("required", False)]


class OpenAPISpecification(BaseModel):
    """Parsed OpenAPI specification metadata."""

    file_path: Path | str
    version: str = ""
    title: str = ""
    description: str = ""
    base_uri: str = "api://"
    tags: list[Any] = Field(default_factory=list)
    operations: dict[str, Any] = Field(default_factory=dict)
    schemas: dict[str, Any] = Field(default_factory=dict)
    validated: bool = False
    validation_errors: list[str] = Field(default_factory=list)
