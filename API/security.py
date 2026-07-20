"""
EVOLV Platform Security Module.

Centralises the platform-level security controls introduced by the
2026-07-11 security audit:

1. ``require_platform_key`` — optional global API-key gate.  When
   the ``EVOLV_API_KEY`` environment variable is set, every path
   operation requires a matching ``X-API-Key`` header (or a valid
   scoped key from the KeyStore).  When unset (local development),
   requests pass through and a startup warning is emitted.
2. ``sanitize_filename_component`` — shared helper that strips
   path separators, parent-directory tokens, and header-breaking
   characters from any user-supplied value used in a filename or
   ``Content-Disposition`` header.
3. ``get_cors_origins`` — CORS origin allow-list, restricted to
   known dev origins with an ``EVOLV_CORS_ORIGINS`` env override
   (comma-separated) for staging / production deployments.

:requirement: URS-43.1 - Platform security hardening.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
from typing import List, Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader


logger = logging.getLogger("evolv.security")


# -----------------------------------------------------------------
# Typed exceptions (CSV-050 range reserved for security errors)
# -----------------------------------------------------------------

class SecurityError(Exception):
    """Error code: CSV-050 - Security control failure."""

    error_code = "CSV-050"


class AuthenticationError(SecurityError):
    """Error code: CSV-051 - API authentication failed."""

    error_code = "CSV-051"


class UnsafeFilenameError(SecurityError):
    """Error code: CSV-052 - Unsafe filename component rejected."""

    error_code = "CSV-052"


# -----------------------------------------------------------------
# Global API-key dependency
# -----------------------------------------------------------------

_API_KEY_ENV = "EVOLV_API_KEY"

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description=(
        "EVOLV platform API key. Required for every endpoint "
        "when the server is started with EVOLV_API_KEY set."
    ),
)


def platform_key_configured() -> bool:
    """
    Return True when a platform API key is configured.

    :return: True if the EVOLV_API_KEY env var is non-empty.
    :requirement: URS-43.1 - Platform security hardening.
    """
    return bool(os.getenv(_API_KEY_ENV, "").strip())


def warn_if_auth_disabled() -> None:
    """
    Emit a startup warning when API authentication is disabled.

    Called once from ``API.main`` at application start so the
    operator sees an unmissable log line in dev mode.

    :requirement: URS-43.1 - Platform security hardening.
    """
    if not platform_key_configured():
        logger.warning(
            "EVOLV_API_KEY is not set — API authentication is "
            "DISABLED (development mode). Set EVOLV_API_KEY to "
            "require an X-API-Key header on every endpoint "
            "before exposing this server beyond localhost."
        )


def _matches_scoped_key(api_key: str) -> bool:
    """
    Check a presented key against the scoped KeyStore.

    Allows tenant keys created via ``POST /admin/api-keys`` to
    keep working when the global platform key gate is enabled.

    :param api_key: Raw key from the X-API-Key header.
    :return: True when the key hash matches an active record.
    :requirement: URS-43.1 - Platform security hardening.
    """
    try:
        from API.key_store import KeyStore
        key_hash = hashlib.sha256(
            api_key.encode("utf-8")
        ).hexdigest()
        return (
            KeyStore.get_instance().get_by_hash(key_hash)
            is not None
        )
    except Exception:
        logger.exception(
            "[CSV-051] Scoped key lookup failed during "
            "platform-key authentication."
        )
        return False


async def require_platform_key(
    request: Request,
    api_key: Optional[str] = Security(_api_key_header),
) -> None:
    """
    FastAPI dependency enforcing the optional platform API key.

    Behaviour:
    - ``EVOLV_API_KEY`` unset  → allow (dev mode; a warning was
      logged at startup by :func:`warn_if_auth_disabled`).
    - ``EVOLV_API_KEY`` set    → the ``X-API-Key`` header must
      match it (constant-time compare), or be a valid active
      scoped key from the KeyStore.  Otherwise ``HTTP 401``.

    Applied app-wide via ``FastAPI(dependencies=[...])`` so every
    router is covered without per-endpoint changes.

    :param request: FastAPI request (for denial logging).
    :param api_key: Value of the X-API-Key header, if present.
    :raises HTTPException 401: When the key is missing/invalid.
    :requirement: URS-43.1 - Platform security hardening.
    """
    configured = os.getenv(_API_KEY_ENV, "").strip()
    if not configured:
        return  # Development mode — auth disabled.

    if api_key:
        if hmac.compare_digest(api_key, configured):
            return
        if _matches_scoped_key(api_key):
            return

    logger.warning(
        "[CSV-051] Rejected unauthenticated request: %s %s",
        request.method,
        request.url.path,
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            f"[{AuthenticationError.error_code}] Missing or "
            "invalid API key."
        ),
    )


# -----------------------------------------------------------------
# Filename sanitisation (path traversal / header injection)
# -----------------------------------------------------------------

_FILENAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename_component(
    value: object,
    default: str = "file",
    max_length: int = 100,
) -> str:
    """
    Reduce a user-supplied value to a filesystem/header-safe slug.

    Strips path separators (``/``, ``\\``), parent-directory
    tokens (``..``), quotes, control characters (CR/LF header
    injection), and anything outside ``[A-Za-z0-9._-]``.

    :param value: Raw user-supplied value (any type; coerced).
    :param default: Fallback slug when nothing safe remains.
    :param max_length: Maximum length of the returned slug.
    :return: Safe filename component, never empty.
    :requirement: URS-43.1 - Platform security hardening.
    """
    cleaned = _FILENAME_UNSAFE_RE.sub("-", str(value or ""))
    while ".." in cleaned:
        cleaned = cleaned.replace("..", ".")
    cleaned = cleaned.strip(".-")
    if not cleaned:
        return default
    return cleaned[:max_length]


# -----------------------------------------------------------------
# CORS origin allow-list
# -----------------------------------------------------------------

_CORS_ENV = "EVOLV_CORS_ORIGINS"

_DEFAULT_DEV_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5179",
    "http://127.0.0.1:5179",
    "http://localhost:5180",
    "http://127.0.0.1:5180",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]


def get_cors_origins() -> List[str]:
    """
    Return the CORS origin allow-list for the API.

    Defaults to the known local dev origins (React on 5173/5174
    and legacy React on 3000).  Set ``EVOLV_CORS_ORIGINS`` to a
    comma-separated list to replace the defaults entirely (e.g.
    additional worktree ports, the Streamlit origin, or the
    production frontend URL).

    :return: List of allowed origins. Never contains ``"*"``.
    :requirement: URS-43.1 - Platform security hardening.
    """
    raw = os.getenv(_CORS_ENV, "").strip()
    if not raw:
        return list(_DEFAULT_DEV_ORIGINS)
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if "*" in origins:
        logger.warning(
            "[CSV-050] Wildcard '*' in EVOLV_CORS_ORIGINS is "
            "not permitted — falling back to dev defaults."
        )
        return list(_DEFAULT_DEV_ORIGINS)
    return origins or list(_DEFAULT_DEV_ORIGINS)
