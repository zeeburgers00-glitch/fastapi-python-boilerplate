"""Production API access guard.

Local development stays frictionless. Production fails closed until API_KEY is set,
then requires the key on every /api/* request using X-API-Key or Bearer auth.
"""
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from .config import get_settings


async def api_key_guard(request: Request, call_next):
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    settings = get_settings()
    environment = settings.app_env.strip().lower()
    if environment not in {"prod", "production"}:
        return await call_next(request)

    expected = (settings.api_key or "").strip()
    if not expected:
        return JSONResponse(
            status_code=503,
            content={"detail": "Production API is locked: configure API_KEY before using API routes."},
        )

    supplied = request.headers.get("x-api-key", "").strip()
    if not supplied:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()

    if not supplied or not secrets.compare_digest(supplied, expected):
        return JSONResponse(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            content={"detail": "A valid API key is required."},
        )

    return await call_next(request)
