"""
EVOLV Bulk Job Store — In-Memory Async Job Tracking.

Provides the ``JobStore`` singleton and the ``run_bulk_validate``
background-task function for the ``POST /bulk/validate`` endpoint.

Each submitted batch receives a unique ``job_id`` and is processed
item-by-item in a FastAPI ``BackgroundTask``.  Progress and partial
results are accessible at any time via ``GET /bulk/status/{job_id}``.

:requirement: URS-30.1 - System shall accept up to 500 requirements
              per bulk request and return 202 Accepted.
:requirement: URS-30.2 - System shall track per-item progress.
:requirement: URS-30.3 - System shall expose job status via
              GET /bulk/status/{job_id}.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # Import only for type hints — avoids circular import at runtime.
    from API.agent_controller import AgentController


# -----------------------------------------------------------------
# BulkJob dataclass
# -----------------------------------------------------------------

@dataclass
class BulkJob:
    """
    State of a single bulk-validation job.

    :requirement: URS-30.2
    """

    job_id: str
    status: Literal["queued", "running", "complete", "failed"]
    total: int
    completed: int
    results: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    sandbox: bool
    error: Optional[str] = None

    def progress_pct(self) -> float:
        """Return percentage of items completed (0.0–100.0)."""
        if self.total == 0:
            return 100.0
        return round((self.completed / self.total) * 100.0, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "job_id":        self.job_id,
            "status":        self.status,
            "total":         self.total,
            "completed":     self.completed,
            "progress_pct":  self.progress_pct(),
            "results":       self.results,
            "error":         self.error,
            "sandbox":       self.sandbox,
        }


# -----------------------------------------------------------------
# JobStore singleton
# -----------------------------------------------------------------

class JobStore:
    """
    Thread-safe in-memory store for bulk validation jobs.

    The store is intentionally in-memory (not persisted) so that
    job records are transient and never pollute the GxP audit
    store with incomplete processing artefacts.

    :requirement: URS-30.2 - Per-item progress tracking.
    """

    _instance: Optional["JobStore"] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._jobs: Dict[str, BulkJob] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "JobStore":
        """Return (or create) the singleton instance."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------

    def create_job(
        self, total: int, sandbox: bool = False
    ) -> BulkJob:
        """
        Create a new job in 'queued' state.

        :param total: Total items to be processed.
        :param sandbox: Whether the job is in Sandbox mode.
        :return: New BulkJob instance.
        :requirement: URS-30.1
        """
        now = datetime.now(timezone.utc).isoformat()
        job = BulkJob(
            job_id=str(uuid.uuid4()),
            status="queued",
            total=total,
            completed=0,
            results=[],
            created_at=now,
            updated_at=now,
            sandbox=sandbox,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[BulkJob]:
        """
        Retrieve a job by ID.

        :param job_id: Job identifier.
        :return: BulkJob or None if not found.
        :requirement: URS-30.3
        """
        return self._jobs.get(job_id)

    def _update(self, job_id: str, **kwargs: Any) -> None:
        """
        Thread-safe partial update of a job's fields.

        :param job_id: Job identifier.
        :param kwargs: Fields to update.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)
            job.updated_at = (
                datetime.now(timezone.utc).isoformat()
            )

    def _append_result(
        self, job_id: str, result: Dict[str, Any]
    ) -> None:
        """
        Thread-safe append of a single result to a job.

        :param job_id: Job identifier.
        :param result: Completed item result dict.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.results.append(result)
            job.completed += 1
            job.updated_at = (
                datetime.now(timezone.utc).isoformat()
            )


# -----------------------------------------------------------------
# Background task
# -----------------------------------------------------------------

def run_bulk_validate(
    job_id: str,
    items: List[Dict[str, Any]],
    controller: "AgentController",
    sandbox: bool = False,
) -> None:
    """
    Process a bulk validation job item-by-item.

    This function is designed to be run as a FastAPI
    ``BackgroundTask``.  It updates the ``JobStore`` with
    progress and partial results as each item completes.

    Per item:
        1. Call ``controller.generate_urs()`` to produce a URS.
        2. Call ``controller.verify_urs()`` to verify it.
        3. Append the combined result to ``job.results``.

    Failed items are recorded with an ``error`` key rather than
    aborting the entire job.

    When *sandbox* is ``True``, no audit events are logged by the
    controller (the controller's internal ``log_audit_event`` calls
    are not suppressed here — sandbox suppression is applied at the
    API layer via ``AuditGuard``).

    :param job_id: Target job identifier in JobStore.
    :param items: List of item dicts with a 'text' key at minimum.
    :param controller: Instantiated AgentController.
    :param sandbox: True when processing in Sandbox mode.
    :requirement: URS-30.1, URS-30.2
    """
    store = JobStore.get_instance()
    store._update(job_id, status="running")

    from Agents.integrity_manager import log_audit_event

    if not sandbox:
        log_audit_event(
            agent_name="JobStore",
            action="BULK_VALIDATE_STARTED",
            decision_logic=(
                f"job_id={job_id}, total={len(items)}"
            ),
        )

    try:
        for idx, item in enumerate(items):
            item_result: Dict[str, Any] = {
                "index": idx,
                "text": item.get("text", "")[:100],
            }
            try:
                urs = controller.generate_urs(
                    requirement=item.get("text", ""),
                    min_score=item.get("min_score", 0.35),
                    expert_mode=item.get(
                        "expert_mode", False
                    ),
                )
                verification = controller.verify_urs(
                    urs=urs,
                    min_score=item.get("min_score", 0.35),
                )
                item_result["urs"] = urs
                item_result["verification"] = verification
                item_result["status"] = "success"
            except Exception as item_exc:
                item_result["status"] = "failed"
                item_result["error"] = str(item_exc)

            store._append_result(job_id, item_result)

        store._update(job_id, status="complete")

        if not sandbox:
            log_audit_event(
                agent_name="JobStore",
                action="BULK_VALIDATE_COMPLETE",
                decision_logic=(
                    f"job_id={job_id}, total={len(items)}, "
                    f"completed={len(items)}"
                ),
            )

    except Exception as exc:
        store._update(
            job_id,
            status="failed",
            error=str(exc),
        )
        if not sandbox:
            log_audit_event(
                agent_name="JobStore",
                action="BULK_VALIDATE_FAILED",
                decision_logic=(
                    f"job_id={job_id}, error={str(exc)[:200]}"
                ),
            )
