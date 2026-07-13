"""
change_control.py — Sprint 36 FastAPI router for Change Impact
Assessment + Change Control Record signing.

Endpoints
=========
- POST /change-control/cia
       Generate a draft Change Impact Assessment from a CR + active
       project snapshot. AI proposes; human reviews.
- POST /change-control/ccr
       Record a signed Change Control Record against a generated CIA.
       This is the human signature gate. Only after a CCR is signed
       can revalidation be triggered.

The principle: AI proposes, human signs, revalidation runs.

:requirement: URS-36.7 - Expose CIA generation via JSON API.
:requirement: URS-36.8 - Expose CCR signing via JSON API.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

_logger = logging.getLogger("evolv.change_control")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.change_impact_agent import (   # noqa: E402
    ChangeImpactAgent,
    ChangeImpactError,
    InvalidProjectSnapshotError,
    sign_ccr as agent_sign_ccr,
)


router = APIRouter(tags=["Change Control"])


# ── Pydantic request models ──────────────────────────────────────────

class _RequirementInSnapshot(BaseModel):
    """One UR or FR inside a project snapshot."""
    id:        str
    type:      str = Field(description="'UR' or 'FR'")
    statement: str = ""
    parentId:  Optional[str] = None


class CIARequest(BaseModel):
    """POST /change-control/cia request body."""
    cr_id:           str = Field(
        max_length=60,
        description=(
            "ServiceNow Change Request ID, e.g. 'CR-2026-0421'."
        ),
    )
    cr_text:         str = Field(
        max_length=8000,
        description="Free-text description of the proposed change.",
    )
    project_name:    str = Field(
        max_length=200,
        description="Active project name from planData.",
    )
    requirements:    List[_RequirementInSnapshot] = Field(
        default_factory=list,
        description="UR + FR records the CR will be assessed against.",
    )
    risk_data:       Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "riskData slice keyed by UR id. Each value contains "
            "impact + implMethod + riskLevel."
        ),
    )
    test_bundles:    Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="testBundles slice keyed by UR id.",
    )
    approvals:       List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "releaseData.approvals — signed approver records."
        ),
    )
    user_id:         str = "demo"

    model_config = {
        "json_schema_extra": {
            "example": {
                "cr_id":   "CR-2026-0421",
                "cr_text": (
                    "Change e-signature session timeout from 5 "
                    "minutes to 3 minutes per new corporate "
                    "security policy."
                ),
                "project_name": "LabCore LIMS v4.2 Migration",
                "requirements": [
                    {
                        "id":        "UR-1",
                        "type":      "UR",
                        "statement": (
                            "The system shall enforce qualified "
                            "electronic signatures on sample "
                            "disposal."
                        ),
                    },
                ],
                "risk_data":    {
                    "UR-1": {"riskLevel": "HIGH"},
                },
                "test_bundles": {
                    "UR-1": {"bundle_id": "TB-UR-1"},
                },
                "approvals":    [],
                "user_id":      "demo",
            },
        },
    }


class CCRRequest(BaseModel):
    """POST /change-control/ccr request body."""
    cia_id:      str = Field(max_length=100)
    cr_id:       str = Field(max_length=60)
    signer_name: str = Field(min_length=1, max_length=200)
    role:        str = Field(
        "QA Director", max_length=100,
    )
    meaning:     str = Field(
        "Approval of Change Impact Assessment", max_length=200,
    )
    decision:    str = Field(
        max_length=40,
        description=(
            "'approve_revalidation' | 'approve_no_revalidation' "
            "| 'reject'"
        ),
    )
    user_id:     str = Field("demo", max_length=100)


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/change-control/cia")
def generate_cia(payload: CIARequest) -> JSONResponse:
    """Generate an AI-drafted Change Impact Assessment.

    The agent identifies affected URs/FRs/bundles and computes a
    summary. The CIA is a *proposal* — no records are modified, no
    revalidation runs, no approvals are invalidated downstream.
    Only the subsequent CCR sign-off can authorise action.

    :requirement: URS-36.7 - Expose CIA generation via JSON API.
    """
    try:
        agent = ChangeImpactAgent()
        snapshot = {
            "project_name": payload.project_name,
            "requirements": [
                r.model_dump() for r in payload.requirements
            ],
            "risk_data":    payload.risk_data,
            "test_bundles": payload.test_bundles,
            "approvals":    payload.approvals,
        }
        cia = agent.assess(
            cr_id=payload.cr_id,
            cr_text=payload.cr_text,
            project_snapshot=snapshot,
            user_id=payload.user_id,
        )
        return JSONResponse(cia.to_dict())
    except InvalidProjectSnapshotError as e:
        # Audit triplet is logged inside the agent — we just shape
        # the HTTP error here.
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project snapshot: {e}",
        )
    except ChangeImpactError as e:
        _logger.exception("[CSV-003] CIA generation failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] CIA generation failed. "
                "See server audit log for details."
            ),
        )
    except Exception as e:
        _logger.exception("[CSV-003] Unexpected CIA error: %s", e)
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Unexpected error during CIA "
                "generation. See server log for details."
            ),
        )


@router.post("/change-control/ccr")
def sign_ccr_endpoint(payload: CCRRequest) -> JSONResponse:
    """Record a signed Change Control Record for a CIA.

    This is the human-signature gate that authorises (or rejects)
    revalidation. The agent's CIA was a proposal; the CCR is the
    decision.

    :requirement: URS-36.8 - Expose CCR signing via JSON API.
    """
    try:
        ccr = agent_sign_ccr(
            cia_id=payload.cia_id,
            cr_id=payload.cr_id,
            signer_name=payload.signer_name,
            role=payload.role,
            meaning=payload.meaning,
            decision=payload.decision,
            user_id=payload.user_id,
        )
        return JSONResponse(ccr)
    except ChangeImpactError as e:
        # Typed validation error — curated message is safe to
        # return to the caller (400-class, not internal state).
        raise HTTPException(
            status_code=400,
            detail=f"CCR sign-off failed: {e}",
        )
    except Exception as e:
        _logger.exception("[CSV-003] Unexpected CCR error: %s", e)
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Unexpected error during CCR "
                "sign-off. See server log for details."
            ),
        )
