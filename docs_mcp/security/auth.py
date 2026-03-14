"""Authentication middleware for the FastAPI web server."""

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from docs_mcp.utils.logger import logger

# Paths that bypass authentication
_PUBLIC_PATHS: frozenset[str] = frozenset({"/api/health"})


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces Bearer token authentication.

    When *enabled*, every request (except those to public paths such as
    ``/api/health``) must carry a valid ``Authorization: Bearer <token>``
    header.  Invalid or missing credentials result in an HTTP 401 response.

    Parameters
    ----------
    app:
        The ASGI application to wrap.
    auth_tokens:
        Iterable of accepted bearer tokens.
    """

    def __init__(self, app, auth_tokens: list[str]) -> None:  # noqa: ANN001
        super().__init__(app)
        self._tokens: list[str] = list(auth_tokens)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check the ``Authorization`` header before forwarding the request."""
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning("Auth: missing or malformed Authorization header")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[len("Bearer "):]

        if not token or not self._is_valid_token(token):
            logger.warning("Auth: invalid bearer token")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    def _is_valid_token(self, token: str) -> bool:
        """Constant-time comparison against every accepted token."""
        return any(hmac.compare_digest(token, valid) for valid in self._tokens)
