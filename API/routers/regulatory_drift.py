"""
regulatory_drift.py — Sprint 38 FastAPI router for the Regulatory
Drift Agent.

Endpoints
=========
- GET  /regulatory-drift/corpus-versions
       Read the currently-ingested corpus version registry.
- POST /regulatory-drift/scan
       Run a drift scan across the supplied project snapshot.
       Returns per-UR affected citations + suggested actions.

The principle: AI proposes drift, human signs the revalidation. The
agent never modifies records, never triggers tests.

:requirement: URS-38.8 - Expose drift detection via JSON API.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

_logger = logging.getLogger("evolv.regulatory_drift")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.regulatory_drift_agent import (   # noqa: E402
    RegulatoryDriftAgent,
    RegulatoryDriftError,
    CorpusRegistryError,
    load_corpus_versions,
)
from Agents.integrity_manager import log_audit_event  # noqa: E402


router = APIRouter(tags=["Regulatory Drift"])


# ── Pydantic request models ──────────────────────────────────────────

class _RequirementInSnapshot(BaseModel):
    id:        str
    type:      str = Field(description="'UR' or 'FR'")
    statement: str = ""
    parentId:  Optional[str] = None
    reg_versions_cited: Optional[List[str]] = None


class DriftScanRequest(BaseModel):
    """POST /regulatory-drift/scan request body."""
    project_name:    str = Field(max_length=200)
    requirements:    List[_RequirementInSnapshot] = Field(
        default_factory=list,
        description="UR + FR records to scan for citation drift.",
    )
    corpus_override: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional · override the on-disk corpus registry with a "
            "custom version map (for testing). When null, the agent "
            "loads from output/corpus_versions.json."
        ),
    )
    user_id:         str = "demo"

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_name": "LabCore LIMS v4.2 Migration",
                "requirements": [
                    {
                        "id":        "UR-2",
                        "type":      "UR",
                        "statement": (
                            "Enforce e-signatures per 21 CFR Part 11."
                        ),
                    },
                ],
                "user_id": "demo",
            },
        },
    }


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/regulatory-drift/corpus-versions")
def get_corpus_versions() -> JSONResponse:
    """Return the currently-ingested regulatory corpus version
    registry.

    Read-only. Pharma QA teams use this to confirm which framework
    versions EVOLV is currently grounded against — useful before
    running a drift scan or when an auditor asks *"what corpus did
    the AI use?"*

    :requirement: URS-38.6 - Read corpus version registry.
    """
    user_id = "system"
    log_audit_event(
        agent_name="API",
        action="DRIFT_SCAN_RECEIVED",
        user_id=user_id,
        decision_logic="GET /regulatory-drift/corpus-versions",
    )
    try:
        registry = load_corpus_versions()
        log_audit_event(
            agent_name="API",
            action="DRIFT_SCAN_COMPLETED",
            user_id=user_id,
            decision_logic=(
                "Returned corpus version registry with "
                f"{len(registry.get('frameworks', {}))} framework(s)"
            ),
        )
        return JSONResponse(registry)
    except CorpusRegistryError as e:
        log_audit_event(
            agent_name="API",
            action="DRIFT_SCAN_FAILED",
            user_id=user_id,
            decision_logic=f"Corpus registry load failed: {e}",
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Corpus registry load failed. "
                "See server audit log for details."
            ),
        )


@router.post("/regulatory-drift/scan")
def scan_for_drift(payload: DriftScanRequest) -> JSONResponse:
    """Scan a project for URs citing superseded regulatory versions.

    Returns a DriftScanReport with per-UR affected_citations and
    suggested actions. The scan never modifies any record; it
    surfaces drift for the QA team to review.

    The standard `DRIFT_SCAN_RECEIVED` / `COMPLETED` / `FAILED`
    audit triplet fires inside the agent itself — this endpoint
    relies on the agent's own audit-trail wiring rather than
    duplicating it.

    :requirement: URS-38.8 - Drift scan via JSON API.
    """
    try:
        agent = RegulatoryDriftAgent()
        snap = {
            "project_name": payload.project_name,
            "requirements": [
                r.model_dump() for r in payload.requirements
            ],
        }
        report = agent.scan(
            project_snapshot=snap,
            corpus_versions=payload.corpus_override,
            user_id=payload.user_id,
        )
        return JSONResponse(report.to_dict())

    except CorpusRegistryError as e:
        _logger.exception(
            "[CSV-003] Corpus registry error: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Corpus registry error. "
                "See server audit log for details."
            ),
        )
    except RegulatoryDriftError as e:
        _logger.exception(
            "[CSV-003] Drift scan failed: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Drift scan failed. "
                "See server audit log for details."
            ),
        )
    except Exception as e:
        _logger.exception(
            "[CSV-003] Unexpected drift scan error: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Unexpected error during drift "
                "scan. See server log for details."
            ),
        )
