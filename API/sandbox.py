"""
EVOLV Sandbox Mode — Developer Safety Net.

Provides the ``get_sandbox_mode`` FastAPI dependency and
``AuditGuard`` context helper.  When a request carries the header
``X-EVOLV-MODE: Sandbox``, AI outputs are generated normally but
**no records are committed** to the production audit trail or the
Pinecone / Integrity Manager stores.

All API responses in Sandbox mode include ``"sandbox": true`` so
clients can distinguish playground output from production records.

:requirement: URS-31.1 - System shall detect Sandbox mode via
              the X-EVOLV-MODE request header.
:requirement: URS-31.2 - Audit trail writes must be suppressed in
              Sandbox mode.
:requirement: URS-31.3 - Sandbox responses must be flagged with
              sandbox=True.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import Request


async def get_sandbox_mode(request: Request) -> bool:
    """
    FastAPI dependency that detects Sandbox mode.

    Returns ``True`` when the incoming request contains the header
    ``X-EVOLV-MODE: Sandbox`` (case-insensitive value).

    :param request: FastAPI request object.
    :return: True if Sandbox mode is active.
    :requirement: URS-31.1
    """
    return (
        request.headers.get("X-EVOLV-MODE", "").lower()
        == "sandbox"
    )


class AuditGuard:
    """
    Thin wrapper around ``log_audit_event`` that becomes a no-op
    in Sandbox mode.

    Usage::

        guard = AuditGuard(sandbox=sandbox)
        guard.log(agent_name="API", action="THING_DONE", ...)

    When ``sandbox=True``, the ``log()`` call returns ``None``
    without writing anything to the CSV audit trail.  All
    production audit writes are preserved when ``sandbox=False``.

    The import of ``log_audit_event`` is deferred to call-time to
    avoid any import-order issues.

    :requirement: URS-31.2 - Suppress audit writes in Sandbox mode.
    """

    def __init__(self, sandbox: bool) -> None:
        """
        Initialise the guard.

        :param sandbox: True to suppress all audit writes.
        """
        self._sandbox = sandbox

    def log(self, **kwargs: Any) -> Optional[str]:
        """
        Log an audit event, or no-op when in Sandbox mode.

        Accepts the same keyword arguments as
        ``Agents.integrity_manager.log_audit_event``.

        :return: SHA-256 reasoning hash, or None in Sandbox mode.
        :requirement: URS-31.2
        """
        if self._sandbox:
            return None
        from Agents.integrity_manager import log_audit_event
        return log_audit_event(**kwargs)

    @property
    def is_sandbox(self) -> bool:
        """Return True when Sandbox mode is active."""
        return self._sandbox
