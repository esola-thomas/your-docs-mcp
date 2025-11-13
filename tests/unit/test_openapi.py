"""Unit tests for OpenAPI models."""

from pathlib import Path

import pytest

from hierarchical_docs_mcp.models.openapi import APIOperation, OpenAPISpecification


class TestAPIOperation:
    """Test APIOperation model."""

    @pytest.fixture
    def basic_operation(self):
        """Create a basic API operation."""
        return APIOperation(
            operation_id="get_user",
            method="GET",
            path="/users/{user_id}",
            uri="api://users/get_user",
            summary="Get user by ID",
        )

    @pytest.fixture
    def detailed_operation(self):
        """Create a detailed API operation with all fields."""
        return APIOperation(
            operation_id="create_user",
            method="POST",
            path="/users",
            uri="api://users/create_user",
            tag="users",
            summary="Create a new user",
            description="Creates a new user in the system with the provided details.",
            parameters=[
                {"name": "api_key", "in": "header", "required": True, "type": "string"},
                {"name": "format", "in": "query", "required": False, "type": "string"},
            ],
            request_body={
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                },
            },
            responses={
                "201": {"description": "User created successfully"},
                "400": {"description": "Invalid input"},
            },
            deprecated=False,
        )

    def test_operation_creation(self, basic_operation):
        """Test creating an API operation with basic fields."""
        assert basic_operation.operation_id == "get_user"
        assert basic_operation.method == "GET"
        assert basic_operation.path == "/users/{user_id}"
        assert basic_operation.uri == "api://users/get_user"
        assert basic_operation.summary == "Get user by ID"
        assert basic_operation.description == ""
        assert basic_operation.tag is None
        assert basic_operation.parameters == []
        assert basic_operation.request_body is None
        assert basic_operation.responses == {}
        assert basic_operation.deprecated is False

    def test_operation_with_all_fields(self, detailed_operation):
        """Test creating an API operation with all fields."""
        assert detailed_operation.operation_id == "create_user"
        assert detailed_operation.method == "POST"
        assert detailed_operation.tag == "users"
        assert detailed_operation.description != ""
        assert len(detailed_operation.parameters) == 2
        assert detailed_operation.request_body is not None
        assert len(detailed_operation.responses) == 2

    def test_full_description_with_both_summary_and_description(self, detailed_operation):
        """Test full_description property combines summary and description."""
        expected = (
            "Create a new user\n\nCreates a new user in the system with the provided details."
        )
        assert detailed_operation.full_description == expected

    def test_full_description_with_only_summary(self, basic_operation):
        """Test full_description property returns only summary when description is empty."""
        assert basic_operation.full_description == "Get user by ID"

    def test_full_description_with_description(self):
        """Test full_description with explicit description."""
        op = APIOperation(
            operation_id="test",
            method="GET",
            path="/test",
            uri="api://test",
            summary="Test summary",
            description="Test description",
        )
        assert op.full_description == "Test summary\n\nTest description"

    def test_required_parameters_filters_correctly(self, detailed_operation):
        """Test required_parameters property filters only required params."""
        required = detailed_operation.required_parameters
        assert len(required) == 1
        assert required[0]["name"] == "api_key"
        assert required[0]["required"] is True

    def test_required_parameters_empty_when_none_required(self, basic_operation):
        """Test required_parameters returns empty list when no required params."""
        assert basic_operation.required_parameters == []

    def test_operation_with_mixed_required_parameters(self):
        """Test filtering required parameters from mixed list."""
        op = APIOperation(
            operation_id="test",
            method="POST",
            path="/test",
            uri="api://test",
            summary="Test",
            parameters=[
                {"name": "required1", "required": True},
                {"name": "optional1", "required": False},
                {"name": "required2", "required": True},
                {"name": "optional2"},  # No required field, defaults to False
            ],
        )
        required = op.required_parameters
        assert len(required) == 2
        assert all(p["required"] for p in required)

    def test_deprecated_operation(self):
        """Test creating a deprecated operation."""
        op = APIOperation(
            operation_id="old_endpoint",
            method="GET",
            path="/old",
            uri="api://old",
            summary="Deprecated endpoint",
            deprecated=True,
        )
        assert op.deprecated is True


class TestOpenAPISpecification:
    """Test OpenAPISpecification model."""

    @pytest.fixture
    def basic_spec(self, tmp_path):
        """Create a basic OpenAPI specification."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")
        return OpenAPISpecification(
            file_path=spec_file,
            version="3.0.0",
            title="Test API",
        )

    @pytest.fixture
    def detailed_spec(self, tmp_path):
        """Create a detailed OpenAPI specification."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        operation = APIOperation(
            operation_id="get_users",
            method="GET",
            path="/users",
            uri="api://users/get_users",
            summary="List all users",
        )

        return OpenAPISpecification(
            file_path=spec_file,
            version="3.0.0",
            title="User Management API",
            description="API for managing user accounts",
            tags=[
                {"name": "users", "description": "User management endpoints"},
                {"name": "auth", "description": "Authentication endpoints"},
            ],
            operations={"get_users": operation},
            schemas={
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                }
            },
            base_uri="api://v1/",
            validated=True,
        )

    def test_spec_creation(self, basic_spec, tmp_path):
        """Test creating an OpenAPI specification with basic fields."""
        assert basic_spec.file_path == tmp_path / "openapi.yaml"
        assert basic_spec.version == "3.0.0"
        assert basic_spec.title == "Test API"
        assert basic_spec.description == ""
        assert basic_spec.tags == []
        assert basic_spec.operations == {}
        assert basic_spec.schemas == {}
        assert basic_spec.base_uri == "api://"
        assert basic_spec.validated is False
        assert basic_spec.validation_errors == []

    def test_spec_with_all_fields(self, detailed_spec):
        """Test creating an OpenAPI specification with all fields."""
        assert detailed_spec.title == "User Management API"
        assert detailed_spec.description == "API for managing user accounts"
        assert len(detailed_spec.tags) == 2
        assert len(detailed_spec.operations) == 1
        assert "get_users" in detailed_spec.operations
        assert len(detailed_spec.schemas) == 1
        assert "User" in detailed_spec.schemas
        assert detailed_spec.base_uri == "api://v1/"
        assert detailed_spec.validated is True

    def test_spec_with_validation_errors(self, tmp_path):
        """Test specification with validation errors."""
        spec_file = tmp_path / "invalid.yaml"
        spec_file.write_text("invalid")

        spec = OpenAPISpecification(
            file_path=spec_file,
            version="3.0.0",
            title="Invalid API",
            validated=False,
            validation_errors=[
                "Missing required field: paths",
                "Invalid schema format",
            ],
        )

        assert spec.validated is False
        assert len(spec.validation_errors) == 2
        assert "Missing required field" in spec.validation_errors[0]

    def test_spec_operations_dictionary(self, detailed_spec):
        """Test operations are stored as dictionary."""
        operations = detailed_spec.operations
        assert isinstance(operations, dict)
        assert "get_users" in operations
        operation = operations["get_users"]
        assert isinstance(operation, APIOperation)
        assert operation.method == "GET"

    def test_spec_schemas_dictionary(self, detailed_spec):
        """Test schemas are stored as dictionary."""
        schemas = detailed_spec.schemas
        assert isinstance(schemas, dict)
        assert "User" in schemas
        user_schema = schemas["User"]
        assert user_schema["type"] == "object"
        assert "properties" in user_schema

    def test_spec_tags_list(self, detailed_spec):
        """Test tags are stored as list of dictionaries."""
        tags = detailed_spec.tags
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, dict) for tag in tags)
        assert tags[0]["name"] == "users"
        assert tags[1]["name"] == "auth"

    def test_spec_with_path_object(self, tmp_path):
        """Test specification with Path object for file_path."""
        spec_file = tmp_path / "api.yaml"
        spec_file.write_text("openapi: 3.0.0")

        spec = OpenAPISpecification(
            file_path=spec_file,
            version="3.0.0",
            title="Test API",
        )

        assert isinstance(spec.file_path, Path)
        assert spec.file_path.name == "api.yaml"

    def test_spec_with_multiple_operations(self, tmp_path):
        """Test specification with multiple operations."""
        spec_file = tmp_path / "api.yaml"
        spec_file.write_text("openapi: 3.0.0")

        operations = {
            "get_users": APIOperation(
                operation_id="get_users",
                method="GET",
                path="/users",
                uri="api://users/get_users",
                summary="List users",
            ),
            "create_user": APIOperation(
                operation_id="create_user",
                method="POST",
                path="/users",
                uri="api://users/create_user",
                summary="Create user",
            ),
            "delete_user": APIOperation(
                operation_id="delete_user",
                method="DELETE",
                path="/users/{id}",
                uri="api://users/delete_user",
                summary="Delete user",
            ),
        }

        spec = OpenAPISpecification(
            file_path=spec_file,
            version="3.0.0",
            title="Test API",
            operations=operations,
        )

        assert len(spec.operations) == 3
        assert all(key in spec.operations for key in ["get_users", "create_user", "delete_user"])

    def test_spec_empty_operations_and_schemas(self, basic_spec):
        """Test specification with empty operations and schemas."""
        assert len(basic_spec.operations) == 0
        assert len(basic_spec.schemas) == 0
        assert basic_spec.operations == {}
        assert basic_spec.schemas == {}

    def test_spec_custom_base_uri(self, tmp_path):
        """Test specification with custom base URI."""
        spec_file = tmp_path / "api.yaml"
        spec_file.write_text("openapi: 3.0.0")

        spec = OpenAPISpecification(
            file_path=spec_file,
            version="3.0.0",
            title="Test API",
            base_uri="api://v2/custom/",
        )

        assert spec.base_uri == "api://v2/custom/"
