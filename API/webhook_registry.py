"""
EVOLV Webhook Registry — Extension Hook System.

Allows enterprise tenants to register HTTPS endpoints that receive
signed event payloads whenever EVOLV fires a system event (e.g.
``SENTINEL_SCAN_COMPLETED``, ``BULK_VALIDATE_COMPLETE``).

Security:
    Every outbound POST is signed with HMAC-SHA256 using the
    tenant's registered secret.  The signature is carried in the
    ``X-EVOLV-Signature`` header as ``sha256=<hex_digest>``.

Reliability:
    Failed deliveries are retried on a tiered backoff schedule:
    first retry after 1 minute, second after 5 minutes, third
    after 15 minutes.  Exhausted retries log a
    ``WEBHOOK_RETRY_EXHAUSTED`` audit event.

Persistence:
    Registrations are stored in ``output/webhook_registry.json``
    so they survive server restarts.

:requirement: URS-28.1 - Tenants shall be able to register
              webhooks for EVOLV events.
:requirement: URS-28.2 - Outbound payloads shall be signed with
              HMAC-SHA256.
:requirement: URS-28.3 - Failed deliveries shall be retried at
              1 min / 5 min / 15 min intervals.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from Agents.integrity_manager import log_audit_event


_STORE_PATH = Path("output") / "webhook_registry.json"

# Retry delay schedule in seconds — 1 min / 5 min / 15 min
_RETRY_DELAYS: tuple = (60, 300, 900)


# -----------------------------------------------------------------
# Data model
# -----------------------------------------------------------------

@dataclass
class WebhookRecord:
    """
    Persisted registration for a single tenant webhook.

    :requirement: URS-28.1
    """

    webhook_id: str
    tenant_id: str
    url: str
    events: List[str]
    # Raw secret used for HMAC signing — stored server-side only.
    secret: str
    created_at: str
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary (excludes secret)."""
        return {
            "webhook_id": self.webhook_id,
            "tenant_id":  self.tenant_id,
            "url":        self.url,
            "events":     self.events,
            "created_at": self.created_at,
            "active":     self.active,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Full serialisation including secret (for persistence)."""
        return asdict(self)


# -----------------------------------------------------------------
# HMAC signing
# -----------------------------------------------------------------

def sign_payload(secret: str, body: bytes) -> str:
    """
    Compute an HMAC-SHA256 signature over *body*.

    The returned string is the hex digest of the signature,
    prefixed as ``sha256=<hex>`` so recipients can verify it
    against the ``X-EVOLV-Signature`` header.

    :param secret: Shared secret registered by the tenant.
    :param body: Raw JSON bytes of the outbound payload.
    :return: ``sha256=<hex_digest>`` signature string.
    :requirement: URS-28.2
    """
    digest = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


# -----------------------------------------------------------------
# WebhookRegistry singleton
# -----------------------------------------------------------------

class WebhookRegistry:
    """
    Singleton registry for tenant-registered outbound webhooks.

    All mutations are thread-safe and immediately persisted to
    ``output/webhook_registry.json``.

    :requirement: URS-28.1 - Register and deregister webhooks.
    :requirement: URS-28.2 - HMAC-SHA256 payload signing.
    """

    _instance: Optional["WebhookRegistry"] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._records: Dict[str, WebhookRecord] = {}
        self._lock = threading.Lock()
        self._load()

    @classmethod
    def get_instance(cls) -> "WebhookRegistry":
        """Return (or create) the singleton instance."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------
    # CRUD
    # ----------------------------------------------------------

    def register(
        self,
        tenant_id: str,
        url: str,
        events: List[str],
        secret: str,
    ) -> WebhookRecord:
        """
        Register a new webhook endpoint for a tenant.

        :param tenant_id: Tenant identifier.
        :param url: HTTPS endpoint URL.
        :param events: Event names to subscribe to.
        :param secret: Shared secret for HMAC signing.
        :return: The created WebhookRecord.
        :requirement: URS-28.1
        """
        record = WebhookRecord(
            webhook_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            url=url,
            events=events,
            secret=secret,
            created_at=(
                datetime.now(timezone.utc).isoformat()
            ),
            active=True,
        )
        with self._lock:
            self._records[record.webhook_id] = record
            self._persist()

        log_audit_event(
            agent_name="WebhookRegistry",
            action="WEBHOOK_REGISTERED",
            decision_logic=(
                f"tenant={tenant_id}, "
                f"url={url}, events={events}"
            ),
        )
        return record

    def deregister(self, webhook_id: str) -> bool:
        """
        Deactivate a registered webhook.

        :param webhook_id: Webhook identifier to deactivate.
        :return: True if found and deactivated, False otherwise.
        :requirement: URS-28.1
        """
        with self._lock:
            record = self._records.get(webhook_id)
            if record is None:
                return False
            record.active = False
            self._persist()

        log_audit_event(
            agent_name="WebhookRegistry",
            action="WEBHOOK_DEREGISTERED",
            decision_logic=f"webhook_id={webhook_id}",
        )
        return True

    def get_hooks_for_event(
        self, event_name: str
    ) -> List[WebhookRecord]:
        """
        Return all active webhooks subscribed to *event_name*.

        :param event_name: Event name to match.
        :return: List of matching WebhookRecord objects.
        :requirement: URS-28.1
        """
        return [
            r for r in self._records.values()
            if r.active and event_name in r.events
        ]

    def get_record(
        self, webhook_id: str
    ) -> Optional[WebhookRecord]:
        """Return a webhook record by ID."""
        return self._records.get(webhook_id)

    # ----------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------

    def _persist(self) -> None:
        """
        Write all records to the JSON store.

        Called inside the write lock — callers are responsible for
        acquiring ``self._lock`` before calling.
        """
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            wid: rec.to_full_dict()
            for wid, rec in self._records.items()
        }
        _STORE_PATH.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _load(self) -> None:
        """Load records from disk on startup (if file exists)."""
        if not _STORE_PATH.exists():
            return
        try:
            data = json.loads(
                _STORE_PATH.read_text(encoding="utf-8")
            )
            for wid, rec_dict in data.items():
                self._records[wid] = WebhookRecord(**rec_dict)
        except Exception:
            # Corrupt file — start fresh; do not crash startup.
            pass


# -----------------------------------------------------------------
# Outbound delivery + retry logic
# -----------------------------------------------------------------

async def _fire_once(
    record: WebhookRecord,
    event_name: str,
    payload: Dict[str, Any],
) -> None:
    """
    Send a single signed POST request to *record.url*.

    :param record: Target webhook.
    :param event_name: The triggering event name.
    :param payload: Event payload dict.
    :raises Exception: On HTTP error or network failure.
    :requirement: URS-28.2 - HMAC-SHA256 signing.
    """
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError(
            "httpx is required for webhook delivery. "
            "Run: pip install httpx"
        ) from exc

    body = json.dumps(
        {"event": event_name, "payload": payload},
        ensure_ascii=False,
    ).encode("utf-8")

    sig = sign_payload(record.secret, body)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            record.url,
            content=body,
            headers={
                "Content-Type":       "application/json",
                "X-EVOLV-Signature":  sig,
                "X-EVOLV-Event":      event_name,
                "X-EVOLV-WebhookID":  record.webhook_id,
            },
        )
        resp.raise_for_status()


async def _retry_loop(
    record: WebhookRecord,
    event_name: str,
    payload: Dict[str, Any],
) -> None:
    """
    Attempt webhook delivery with tiered exponential back-off.

    Attempts: immediate → 1 min → 5 min → 15 min.
    Logs ``WEBHOOK_RETRY_EXHAUSTED`` when all retries fail.

    :requirement: URS-28.3 - Tiered retry: 1/5/15 minutes.
    """
    last_exc: Optional[Exception] = None

    for attempt, delay in enumerate(
        [0] + list(_RETRY_DELAYS), start=1
    ):
        if delay:
            await asyncio.sleep(delay)
        try:
            await _fire_once(record, event_name, payload)
            log_audit_event(
                agent_name="WebhookRegistry",
                action="WEBHOOK_FIRED",
                decision_logic=(
                    f"webhook_id={record.webhook_id}, "
                    f"event={event_name}, attempt={attempt}"
                ),
            )
            return  # Success — stop retrying
        except Exception as exc:
            last_exc = exc

    # All attempts exhausted
    log_audit_event(
        agent_name="WebhookRegistry",
        action="WEBHOOK_RETRY_EXHAUSTED",
        decision_logic=(
            f"webhook_id={record.webhook_id}, "
            f"event={event_name}, "
            f"error={str(last_exc)[:200]}"
        ),
    )


def schedule_webhook(
    record: WebhookRecord,
    event_name: str,
    payload: Dict[str, Any],
    background_tasks: Any,
) -> None:
    """
    Schedule a webhook delivery as a FastAPI background task.

    Uses ``background_tasks.add_task`` so the API endpoint
    returns its response immediately without waiting for
    delivery confirmation.

    :param record: Target webhook record.
    :param event_name: Triggering event name.
    :param payload: Event payload.
    :param background_tasks: FastAPI BackgroundTasks instance.
    :requirement: URS-28.1, URS-28.3
    """
    background_tasks.add_task(
        _retry_loop, record, event_name, payload
    )
