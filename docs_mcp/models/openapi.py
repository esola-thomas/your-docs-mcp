"""OpenAPI specification data models."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class APIOperation(BaseModel):
    """Individual endpoint from OpenAPI spec."""

    operation_id: str
    method: str
    path: str
    uri: str
    tag: str | None = None
    summary: str
    description: str = ""
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, dict[str, Any]] = Field(default_factory=dict)
    deprecated: bool = False

    @property
    def full_description(self) -> str:
        """Combines summary and description for AI consumption."""
        if self.description:
            return f"{self.summary}\n\n{self.description}"
        return self.summary

    @property
    def required_parameters(self) -> list[dict[str, Any]]:
        """Filters to only required parameters."""
        return [p for p in self.parameters if p.get("required", False)]


class OpenAPISpecification(BaseModel):
    """API documentation spec defining endpoints and schemas."""

    file_path: Path
    version: str
    title: str
    description: str = ""
    tags: list[dict[str, Any]] = Field(default_factory=list)
    operations: dict[str, APIOperation] = Field(default_factory=dict)
    schemas: dict[str, dict[str, Any]] = Field(default_factory=dict)
    base_uri: str = "api://"
    validated: bool = False
    validation_errors: list[str] = Field(default_factory=list)
