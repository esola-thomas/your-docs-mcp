"""Query and content sanitization to prevent injection attacks."""

import re

from docs_mcp.utils.logger import audit_log, logger


class SanitizationError(Exception):
    """Raised when sanitization fails or input is invalid."""

    pass


# Patterns that could indicate injection attempts
SUSPICIOUS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"on\w+\s*=",  # Event handlers like onclick=
    r"eval\s*\(",
    r"exec\s*\(",
    r"\$\{.*\}",  # Template literals
    r"`.*`",  # Backticks (command execution in some contexts)
]

# Regex special characters that need escaping for literal search
REGEX_SPECIAL_CHARS = r"[.^$*+?{}[\]\\|()\"]"

# Maximum query length to prevent DoS
MAX_QUERY_LENGTH = 500


def sanitize_query(query: str, allow_regex: bool = False) -> str:
    """Sanitize a search query to prevent injection attacks.

    Args:
        query: The query string to sanitize
        allow_regex: Whether to allow regex patterns (if False, escapes special chars)

    Returns:
        Sanitized query string

    Raises:
        SanitizationError: If query is invalid or suspicious
    """
    if not query:
        return ""

    # Check length
    if len(query) > MAX_QUERY_LENGTH:
        audit_log(
            "sanitization_violation",
            {
                "type": "query",
                "reason": "excessive_length",
                "length": len(query),
                "max_length": MAX_QUERY_LENGTH,
            },
        )
        raise SanitizationError(f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters")

    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            audit_log(
                "sanitization_violation",
                {
                    "type": "query",
                    "reason": "suspicious_pattern",
                    "pattern": pattern,
                    "query": query[:100],  # Log first 100 chars only
                },
            )
            raise SanitizationError(f"Query contains suspicious pattern: {pattern}")

    # Escape regex special characters if regex not allowed
    if not allow_regex:
        sanitized = re.sub(REGEX_SPECIAL_CHARS, r"\\\g<0>", query)
    else:
        # Validate regex syntax if regex is allowed
        try:
            re.compile(query)
            sanitized = query
        except re.error as e:
            audit_log(
                "sanitization_violation",
                {"type": "query", "reason": "invalid_regex", "error": str(e)},
            )
            raise SanitizationError(f"Invalid regex pattern: {e}") from e

    # Remove control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\n\t")

    logger.debug(f"Sanitized query: {query} -> {sanitized}")
    return sanitized


def sanitize_openapi_description(description: str) -> str:
    """Sanitize OpenAPI descriptions to prevent prompt injection in AI assistants.

    Args:
        description: The description text to sanitize

    Returns:
        Sanitized description
    """
    if not description:
        return ""

    # Check for prompt injection patterns
    injection_indicators = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+.+\s+instructions",
        r"new\s+instructions:",
        r"system\s+prompt",
        r"forget\s+everything",
    ]

    for pattern in injection_indicators:
        if re.search(pattern, description, re.IGNORECASE):
            audit_log(
                "prompt_injection_detected",
                {
                    "type": "openapi_description",
                    "pattern": pattern,
                    "description": description[:100],
                },
            )
            logger.warning(f"Potential prompt injection detected in OpenAPI description: {pattern}")
            # Replace suspicious content with placeholder
            description = re.sub(
                pattern,
                "[SANITIZED CONTENT]",
                description,
                flags=re.IGNORECASE,
            )

    # Remove excessive newlines and control characters
    description = re.sub(r"\n{3,}", "\n\n", description)
    description = "".join(char for char in description if ord(char) >= 32 or char in "\n\t")

    return description.strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename

    Raises:
        SanitizationError: If filename is invalid
    """
    if not filename:
        raise SanitizationError("Filename cannot be empty")

    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        audit_log(
            "sanitization_violation",
            {
                "type": "filename",
                "reason": "path_traversal_attempt",
                "filename": filename,
            },
        )
        raise SanitizationError("Filename contains invalid characters (path traversal attempt)")

    # Remove/replace potentially problematic characters
    # Keep alphanumeric, dots, dashes, underscores
    sanitized = re.sub(r"[^\w\-.]", "_", filename)

    # Prevent hidden files unless explicitly named
    if sanitized.startswith(".") and len(sanitized) > 1:
        audit_log(
            "sanitization_violation",
            {"type": "filename", "reason": "hidden_file", "filename": filename},
        )
        raise SanitizationError("Hidden filenames not allowed")

    return sanitized


def sanitize_uri(uri: str) -> str:
    """Sanitize a URI to ensure it follows expected patterns.

    Args:
        uri: The URI to sanitize

    Returns:
        Sanitized URI

    Raises:
        SanitizationError: If URI is invalid
    """
    if not uri:
        raise SanitizationError("URI cannot be empty")

    # Check for valid URI schemes
    valid_schemes = ["docs://", "api://"]
    if not any(uri.startswith(scheme) for scheme in valid_schemes):
        raise SanitizationError(f"Invalid URI scheme. Must start with: {', '.join(valid_schemes)}")

    # Remove query parameters and fragments that could be injection vectors
    uri = uri.split("?")[0].split("#")[0]

    # Check for path traversal in URI
    if ".." in uri:
        audit_log(
            "sanitization_violation",
            {"type": "uri", "reason": "path_traversal", "uri": uri},
        )
        raise SanitizationError("URI contains path traversal attempt")

    return uri
