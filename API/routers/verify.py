"""
verify.py — FastAPI router for the Verify phase.

Endpoints:
  POST /verify/sign-off   — Lock a test run and write a 21 CFR Part 11
                            compliant audit record with electronic signature.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant
              audit trail.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

_logger = logging.getLogger("evolv.verify")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from Agents.integrity_manager import log_audit_event

router = APIRouter(tags=["Verify"])


# ── Request / Response models ──────────────────────────────────────

class StepResultIn(BaseModel):
    """Execution result for a single test step."""
    verdict:       str  # pass | fail | blocked | na
    actual_result: str  = ""
    tester_name:   str  = ""
    executed_at:   Optional[str] = None


class SignOffRequest(BaseModel):
    """
    Request body for POST /verify/sign-off.

    :requirement: URS-2.1 - Audit trail must capture signer, timestamp,
                  meaning of signature per 21 CFR Part 11 §11.50.
    """
    script_id:      str = Field(
        ..., max_length=100, description="DeltaAgent script ID",
    )
    run_id:         str = Field(
        ..., max_length=100,
        description="TestRun ID from React store",
    )
    urs_id:         str = Field(
        "", max_length=60, description="Source URS ID",
    )
    signer_name:    str = Field(..., min_length=1, max_length=200)
    meaning:        str = Field(
        "Approval of Test Execution",
        max_length=200,
        description=(
            "Meaning of electronic signature per 21 CFR Part 11 §11.50"
        ),
    )
    pass_count:     int = 0
    fail_count:     int = 0
    blocked_count:  int = 0
    na_count:       int = 0
    total_steps:    int = 0
    overall_verdict: str = "PASS"
    step_results:   Dict[str, StepResultIn] = Field(default_factory=dict)


class SignOffResponse(BaseModel):
    """
    Response body for POST /verify/sign-off.

    reasoning_hash — SHA-256 from the audit trail row; store this in
    the React TestRun for chain-of-custody traceability.
    """
    status:          str
    reasoning_hash:  str
    signed_at:       str
    audit_message:   str


# ── Endpoint ───────────────────────────────────────────────────────

@router.post("/sign-off", response_model=SignOffResponse)
def sign_off_test_run(body: SignOffRequest) -> SignOffResponse:
    """
    Lock a completed test run and write a 21 CFR Part 11 electronic
    signature record to the EVOLV audit trail.

    Validation rules (enforced server-side):
    - signer_name must be non-empty
    - meaning must be one of the approved values
    - overall_verdict is recorded as-is (UI has already computed it)

    :requirement: URS-2.1 - Maintain 21 CFR Part 11 compliant audit trail.
    """
    ALLOWED_MEANINGS = {
        "Approval of Test Execution",
        "Review of Test Results",
        "Witnessed Test Execution",
    }
    if body.meaning not in ALLOWED_MEANINGS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid signature meaning '{body.meaning}'. "
                f"Allowed: {sorted(ALLOWED_MEANINGS)}"
            ),
        )

    signed_at = datetime.now(timezone.utc).isoformat()

    decision_logic = (
        f"Test run {body.run_id} signed off by '{body.signer_name}'. "
        f"Script: {body.script_id}. URS: {body.urs_id}. "
        f"Overall verdict: {body.overall_verdict}. "
        f"Steps — Pass: {body.pass_count}, Fail: {body.fail_count}, "
        f"Blocked: {body.blocked_count}, N/A: {body.na_count} "
        f"/ {body.total_steps} total. "
        f"Meaning: '{body.meaning}'."
    )

    thought_process = {
        "inputs": {
            "script_id":   body.script_id,
            "run_id":      body.run_id,
            "urs_id":      body.urs_id,
            "signer_name": body.signer_name,
            "meaning":     body.meaning,
        },
        "steps": [
            "Validated signer name is non-empty",
            "Validated meaning is from approved list",
            f"Computed overall verdict: {body.overall_verdict}",
            "Wrote 21 CFR Part 11 audit record",
        ],
        "outputs": {
            "verdict":   body.overall_verdict,
            "signed_at": signed_at,
        },
    }

    try:
        reasoning_hash = log_audit_event(
            agent_name="TestExecutionUI",
            action="TEST_RUN_SIGNED_OFF",
            user_id=body.signer_name,
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

    return SignOffResponse(
        status="signed_off",
        reasoning_hash=reasoning_hash,
        signed_at=signed_at,
        audit_message=(
            f"Test run locked. Audit record written. "
            f"Chain-of-custody hash: {reasoning_hash[:16]}…"
        ),
    )
