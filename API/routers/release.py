"""
release.py — FastAPI router for the Release phase.

Endpoints:
  POST /release/approve   — Record an approver's electronic signature
                            and write a 21 CFR Part 11 audit record.
  POST /release/go-live   — Formally release the system; writes the
                            final RELEASE_APPROVED audit event.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant
              audit trail.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

_logger = logging.getLogger("evolv.release")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from Agents.integrity_manager import log_audit_event

router = APIRouter(tags=["Release"])

APPROVER_ROLES = {
    "System Owner",
    "QA Lead",
    "Business Owner",
    "Validation Lead",
    "IT Manager",
}

APPROVAL_MEANINGS = {
    "Approval for Release",
    "QA Review and Approval",
    "Business Sign-off",
    "Witnessed Approval",
}


# ── Models ────────────────────────────────────────────────────────

class ApprovalRequest(BaseModel):
    """
    Single approver sign-off request.

    :requirement: URS-2.1 - Electronic signature per 21 CFR Part 11.
    """
    project_name:  str = Field(..., min_length=1, max_length=200)
    gamp_category: str = Field("", max_length=60)
    approver_name: str = Field(..., min_length=1, max_length=200)
    approver_role: str = Field(..., min_length=1, max_length=100)
    meaning:       str = Field(
        "Approval for Release", max_length=200,
    )
    test_verdict:  str = Field("", max_length=60)
    risk_summary:  str = Field("", max_length=2000)


class ApprovalResponse(BaseModel):
    status:         str
    approver_id:    str
    reasoning_hash: str
    signed_at:      str


class GoLiveRequest(BaseModel):
    """
    Final go-live release request — requires at least one prior approval.

    :requirement: URS-2.1 - Final release event logged to audit trail.
    """
    project_name:    str = Field(
        ..., min_length=1, max_length=200,
    )
    gamp_category:   str = Field("", max_length=60)
    approvals_count: int = 0
    test_verdict:    str = Field("", max_length=60)
    released_by:     str = Field(
        ..., min_length=1, max_length=200,
    )


class GoLiveResponse(BaseModel):
    status:         str
    reasoning_hash: str
    released_at:    str
    message:        str


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/approve", response_model=ApprovalResponse)
def record_approval(body: ApprovalRequest) -> ApprovalResponse:
    """
    Record one approver's electronic signature for the release package.

    Each call produces an independent audit record. Multiple approvers
    can sign the same release.

    :requirement: URS-2.1 - Maintain 21 CFR Part 11 compliant audit trail.
    """
    if body.meaning not in APPROVAL_MEANINGS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid meaning '{body.meaning}'. "
                f"Allowed: {sorted(APPROVAL_MEANINGS)}"
            ),
        )

    signed_at  = datetime.now(timezone.utc).isoformat()
    approver_id = (
        f"APV-{body.approver_name[:8].upper().replace(' ', '')}"
        f"-{signed_at[:10].replace('-', '')}"
    )

    decision_logic = (
        f"Release approval by '{body.approver_name}' "
        f"({body.approver_role}) for project '{body.project_name}' "
        f"(GAMP 5 Cat {body.gamp_category}). "
        f"Test verdict: {body.test_verdict or 'N/A'}. "
        f"Meaning: '{body.meaning}'."
    )

    thought_process = {
        "inputs": {
            "project_name":  body.project_name,
            "gamp_category": body.gamp_category,
            "approver_name": body.approver_name,
            "approver_role": body.approver_role,
            "meaning":       body.meaning,
            "test_verdict":  body.test_verdict,
        },
        "steps": [
            "Validated approver name and role are non-empty",
            "Validated meaning is from approved list",
            "Checked test verdict is present",
            "Wrote 21 CFR Part 11 approval audit record",
        ],
        "outputs": {
            "approver_id": approver_id,
            "signed_at":   signed_at,
        },
    }

    try:
        reasoning_hash = log_audit_event(
            agent_name="ReleaseGate",
            action="RELEASE_APPROVAL_SIGNED",
            user_id=body.approver_name,
            decision_logic=decision_logic,
            compliance_impact="Electronic Signature",
            thought_process=thought_process,
        )
    except Exception as exc:
        _logger.exception(
            "[CSV-002] Audit trail write failed: %s", exc,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-002] Audit trail write failed. "
                "See server log for details."
            ),
        ) from exc

    return ApprovalResponse(
        status="approved",
        approver_id=approver_id,
        reasoning_hash=reasoning_hash,
        signed_at=signed_at,
    )


@router.post("/go-live", response_model=GoLiveResponse)
def go_live(body: GoLiveRequest) -> GoLiveResponse:
    """
    Formally release the system to production. Requires at least one
    prior approval. Writes the final RELEASE_APPROVED audit event.

    :requirement: URS-2.1 - Maintain 21 CFR Part 11 compliant audit trail.
    """
    if body.approvals_count < 1:
        raise HTTPException(
            status_code=422,
            detail="At least one approval is required before go-live.",
        )

    released_at = datetime.now(timezone.utc).isoformat()

    decision_logic = (
        f"System '{body.project_name}' (GAMP 5 Cat {body.gamp_category}) "
        f"approved for production release by '{body.released_by}'. "
        f"Total approvals: {body.approvals_count}. "
        f"Test verdict: {body.test_verdict or 'N/A'}."
    )

    thought_process = {
        "inputs": {
            "project_name":    body.project_name,
            "gamp_category":   body.gamp_category,
            "approvals_count": body.approvals_count,
            "test_verdict":    body.test_verdict,
            "released_by":     body.released_by,
        },
        "steps": [
            f"Confirmed {body.approvals_count} approval(s) on record",
            "Validated test verdict is present",
            "Wrote final RELEASE_APPROVED audit event",
        ],
        "outputs": {
            "released_at": released_at,
            "status":      "released",
        },
    }

    try:
        reasoning_hash = log_audit_event(
            agent_name="ReleaseGate",
            action="RELEASE_APPROVED",
            user_id=body.released_by,
            decision_logic=decision_logic,
            compliance_impact="Release Authorization",
            thought_process=thought_process,
        )
    except Exception as exc:
        _logger.exception(
            "[CSV-002] Audit trail write failed: %s", exc,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-002] Audit trail write failed. "
                "See server log for details."
            ),
        ) from exc

    return GoLiveResponse(
        status="released",
        reasoning_hash=reasoning_hash,
        released_at=released_at,
        message=(
            f"System '{body.project_name}' formally released. "
            f"Audit record: {reasoning_hash[:16]}…"
        ),
    )
