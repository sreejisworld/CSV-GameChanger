"""
EVOLV Scoped API Key Management.

Creates, stores, and validates identity-aware API tokens.  Each
key is linked to a ``Tenant_ID`` and a ``DAC_Policy``.  The
``audit_only`` scope enforces read-only access at the API layer
by blocking any non-GET HTTP method.

Keys are stored as SHA-256 hashes in ``output/api_keys.json`` so
the raw key can never be recovered from disk.

:requirement: URS-29.1 - API keys shall be linked to a Tenant_ID
              and a DAC_Policy.
:requirement: URS-29.2 - The get_current_key dependency shall
              authenticate inbound API keys.
:requirement: URS-29.3 - The audit_only scope shall block POST,
              PUT, PATCH, and DELETE requests.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from Agents.integrity_manager import log_audit_event


_STORE_PATH = Path("output") / "api_keys.json"

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="EVOLV Scoped API Key.",
)


# -----------------------------------------------------------------
# Data model
# -----------------------------------------------------------------

@dataclass
class ScopedAPIKey:
    """
    Persisted representation of an EVOLV API key.

    The ``key_hash`` field stores the SHA-256 hash of the raw
    key — the raw key is never written to disk.

    :requirement: URS-29.1
    """

    key_id: str
    tenant_id: str
    scopes: List[str]
    dac_policy: Optional[Dict[str, Any]]
    key_hash: str
    created_at: str
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "key_id":     self.key_id,
            "tenant_id":  self.tenant_id,
            "scopes":     self.scopes,
            "dac_policy": self.dac_policy,
            "created_at": self.created_at,
            "active":     self.active,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Full serialisation including key_hash (for storage)."""
        return asdict(self)


# -----------------------------------------------------------------
# KeyStore singleton
# -----------------------------------------------------------------

class KeyStore:
    """
    Thread-safe, JSON-backed store for ScopedAPIKey records.

    :requirement: URS-29.1 - Keys linked to Tenant_ID + DAC_Policy.
    """

    _instance: Optional["KeyStore"] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._records: Dict[str, ScopedAPIKey] = {}
        self._lock = threading.Lock()
        self._load()

    @classmethod
    def get_instance(cls) -> "KeyStore":
        """Return (or create) the singleton instance."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------

    def create_key(
        self,
        tenant_id: str,
        scopes: List[str],
        dac_policy: Optional[Dict[str, Any]] = None,
    ) -> tuple:  # tuple[ScopedAPIKey, str]
        """
        Generate a new scoped API key.

        Returns the ``ScopedAPIKey`` record and the raw key
        string.  The raw key is shown **once** — it cannot be
        recovered afterwards.

        :param tenant_id: Tenant the key belongs to.
        :param scopes: Permission scopes for the key.
        :param dac_policy: Optional DAC policy attributes.
        :return: (ScopedAPIKey record, raw_key string).
        :requirement: URS-29.1
        """
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(
            raw_key.encode("utf-8")
        ).hexdigest()

        record = ScopedAPIKey(
            key_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            scopes=scopes,
            dac_policy=dac_policy,
            key_hash=key_hash,
            created_at=(
                datetime.now(timezone.utc).isoformat()
            ),
            active=True,
        )

        with self._lock:
            self._records[record.key_id] = record
            self._persist()

        log_audit_event(
            agent_name="KeyStore",
            action="API_KEY_CREATED",
            decision_logic=(
                f"key_id={record.key_id}, "
                f"tenant={tenant_id}, scopes={scopes}"
            ),
        )
        return record, raw_key

    def get_by_hash(
        self, key_hash: str
    ) -> Optional[ScopedAPIKey]:
        """
        Look up an active key by its SHA-256 hash.

        :param key_hash: SHA-256 hex digest of the raw key.
        :return: ScopedAPIKey or None.
        """
        for record in self._records.values():
            if record.key_hash == key_hash and record.active:
                return record
        return None

    def get_by_id(
        self, key_id: str
    ) -> Optional[ScopedAPIKey]:
        """
        Look up a key by its key_id.

        :param key_id: UUID key identifier.
        :return: ScopedAPIKey or None.
        """
        return self._records.get(key_id)

    # ----------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------

    def _persist(self) -> None:
        """Write all records to disk (called inside lock)."""
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            kid: rec.to_full_dict()
            for kid, rec in self._records.items()
        }
        _STORE_PATH.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _load(self) -> None:
        """Load records from disk on startup."""
        if not _STORE_PATH.exists():
            return
        try:
            data = json.loads(
                _STORE_PATH.read_text(encoding="utf-8")
            )
            for kid, rec_dict in data.items():
                self._records[kid] = ScopedAPIKey(**rec_dict)
        except Exception:
            pass  # Corrupt file — start fresh


# -----------------------------------------------------------------
# FastAPI dependencies
# -----------------------------------------------------------------

async def get_current_key(
    request: Request,
    api_key: Optional[str] = Security(_api_key_header),
) -> Optional[ScopedAPIKey]:
    """
    FastAPI dependency: authenticate and return the active key.

    When no ``X-API-Key`` header is present, returns ``None``
    (unauthenticated access is still allowed for endpoints that
    do not require a key).

    When a key is provided but is invalid or inactive, raises
    ``HTTP 401``.

    :param request: FastAPI request object.
    :param api_key: Value of the X-API-Key header.
    :return: ScopedAPIKey or None.
    :requirement: URS-29.2
    """
    if not api_key:
        return None

    key_hash = hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()
    record = KeyStore.get_instance().get_by_hash(key_hash)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key.",
        )

    log_audit_event(
        agent_name="KeyStore",
        action="API_KEY_USED",
        user_id=record.tenant_id,
        decision_logic=(
            f"key_id={record.key_id}, "
            f"method={request.method}, "
            f"path={request.url.path}"
        ),
    )

    return record


async def require_api_key(
    current_key: Optional[ScopedAPIKey] = Depends(
        get_current_key
    ),
) -> ScopedAPIKey:
    """
    FastAPI dependency: require a valid API key.

    Raises ``HTTP 401`` when no ``X-API-Key`` header is present
    or the provided key is invalid.

    :param current_key: Resolved from X-API-Key header.
    :return: ScopedAPIKey when authenticated.
    :raises HTTPException 401: When key is missing or invalid.
    :requirement: URS-29.2
    """
    if current_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )
    return current_key


async def enforce_audit_only_scope(
    request: Request,
    current_key: Optional[ScopedAPIKey] = Depends(
        get_current_key
    ),
) -> None:
    """
    FastAPI dependency: block write requests from audit_only keys.

    An API key with ``scope='audit_only'`` may only perform GET
    requests.  Any POST, PUT, PATCH, or DELETE attempt raises
    ``HTTP 403``.

    This dependency should be added to all write-capable routes::

        @app.post(
            "/bulk/validate",
            dependencies=[Depends(enforce_audit_only_scope)],
        )

    :param request: FastAPI request object.
    :param current_key: Resolved from X-API-Key header.
    :raises HTTPException 403: When audit_only scope attempts write.
    :requirement: URS-29.3
    """
    if current_key is None:
        return  # No key — other auth mechanisms apply

    if (
        "audit_only" in current_key.scopes
        and request.method.upper() not in ("GET", "HEAD")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "API key scope 'audit_only' does not permit "
                f"'{request.method}' requests. "
                "Use a key with write scopes for this action."
            ),
        )
