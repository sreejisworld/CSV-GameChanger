"""
bap.py - Sprint 40 FastAPI router for the Bounded Autonomy
Profile (BAP) engine.

Endpoints
=========
- GET  /bap/tiers
       Return the BAP tier ladder (BAP-0 through BAP-4 + BAP-X)
       and the per-tier required-controls catalogue.
- GET  /bap/exclusion-rules
       Return the hard exclusion rules that force BAP-X
       regardless of other inputs (the rules that won't yield
       to "control upward").
- POST /bap/assess
       Run a Context of Use through the three-layer diagnostic
       stack and return a full Bounded Autonomy Profile.
- POST /bap/check-exclusion
       Quick exclusion-only check (no full assessment). Useful
       for sales conversations + pre-flight checks before
       investing in a full BAP run.

The principle: AI proposes the tier + assurance argument; a
human reviewer signs. The engine never modifies records,
never persists approvals, never overrides exclusions. Bounded
autonomy applied to the assurance diagnostic itself.

:requirement: URS-40.7 - Expose BAP assessment via JSON API.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.bounded_autonomy_profile import (   # noqa: E402
    BoundedAutonomyProfileEngine,
    BoundedAutonomyProfileError,
    InvalidProfileInputError,
    BAP_TIERS,
    EXCLUSION_RULES,
    REQUIRED_CONTROLS_BY_TIER,
    SCENARIO_BUCKETS,
    SCHEMA_VERSION,
)
from Agents.integrity_manager import log_audit_event   # noqa: E402


router = APIRouter(tags=["Bounded Autonomy Profile"])


# --- Pydantic models -------------------------------------------------

class _ContextOfUseModel(BaseModel):
    """Per-deployment Context of Use - the unit of assessment.

    Same shape as Sprint 39's Trustworthiness Report COU so the
    two engines can be invoked from a single React call.
    """
    customer_name:       str
    statement:           str = Field(
        description=(
            "What the AI does in this deployment - one "
            "sentence. e.g. 'EVOLV drafts URs and FRs for a "
            "GxP-Direct LIMS at a CDMO; outputs require QA "
            "sign-off before being persisted to Vault.'"
        ),
    )
    deployment_region:   str = Field(
        default="US",
        description="'US' | 'EU' | 'UK' | 'India' | 'APAC' | 'Global'",
    )
    gxp_classification:  str = Field(
        description="'GxP Direct' | 'GxP Indirect' | 'Non-GxP'",
    )
    risk_level:          str = Field(
        description="'High' | 'Medium' | 'Low'",
    )
    decision_authority:  str = Field(
        default="AI proposes, human signs",
    )
    target_system:       str = ""
    integrates_with:     List[str] = Field(default_factory=list)
    poc_or_production:   str = "POC"
    cou_id:              Optional[str] = None


class BAPAssessRequest(BaseModel):
    """POST /bap/assess request body."""
    cou:     _ContextOfUseModel
    user_id: str = "demo"

    model_config = {
        "json_schema_extra": {
            "example": {
                "cou": {
                    "customer_name":      "Demo CDMO",
                    "statement":
                        "EVOLV drafts URs and FRs for a "
                        "GxP-Direct LIMS at a CDMO; outputs "
                        "require QA sign-off before being "
                        "persisted to Vault.",
                    "deployment_region":  "US",
                    "gxp_classification": "GxP Direct",
                    "risk_level":         "High",
                    "decision_authority":
                        "AI proposes, human signs",
                    "target_system":      "LabCore LIMS v4.2",
                    "poc_or_production":  "POC",
                },
                "user_id": "demo",
            },
        },
    }


class _BAPSignerMeta(BaseModel):
    """Optional pre-filled signer names on the Manifestation
    of Signature page. Empty fields render as blank signature
    lines for wet/electronic signing post-PDF."""
    business_owner:    str = ""
    quality_assurance: str = ""
    service_owner:     str = ""
    system_sme:        str = ""
    ai_model_sme:      str = ""


class BAPAssessPDFRequest(BAPAssessRequest):
    """POST /bap/pdf request body - extends BAPAssessRequest with
    signature-page metadata."""
    meaning: str = "Approval of Bounded Autonomy Profile"
    signers: _BAPSignerMeta = Field(default_factory=_BAPSignerMeta)


class ExclusionCheckRequest(BaseModel):
    """POST /bap/check-exclusion request body.

    Lightweight pre-flight - returns just the exclusion result
    without running the full three-layer stack. Useful for
    sales conversations: 'let me check if this would even pass
    our exclusion rules before we commit to a full assessment.'
    """
    statement:          str = Field(
        description=(
            "Free-text deployment description to be screened "
            "against the exclusion rules."
        ),
    )
    decision_authority: str = Field(
        default="AI proposes, human signs",
        description=(
            "Who has the last word on AI-drafted outputs. "
            "Words like 'autonomous' here change the result."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "statement":
                    "AI signs the electronic signature on "
                    "behalf of the QA reviewer.",
                "decision_authority":
                    "AI proposes, human signs",
            },
        },
    }


# --- Helpers ---------------------------------------------------------

def _serialise_exclusion_rules() -> List[Dict[str, str]]:
    """Convert EXCLUSION_RULES (which include compiled regex
    objects) into JSON-safe dicts for the API response."""
    out: List[Dict[str, str]] = []
    for rule in EXCLUSION_RULES:
        out.append({
            "id":         rule["id"],
            "violation":  rule["violation"],
            "why":        rule["why"],
            "pattern":    rule["pattern"].pattern,
        })
    return out


# --- Endpoints -------------------------------------------------------

@router.get("/bap/tiers")
def get_tiers() -> JSONResponse:
    """Return the BAP tier ladder + per-tier required controls.

    Read-only. Pharma evaluators read this to understand the
    proportional control system EVOLV uses to scale assurance
    against deployment risk - the answer to 'what do I need by
    Monday for this tier'.

    :requirement: URS-40.8 - Read tier ladder + control catalogue.
    """
    user_id = "system"
    log_audit_event(
        agent_name="API",
        action="BAP_ASSESSMENT_RECEIVED",
        user_id=user_id,
        decision_logic="GET /bap/tiers",
    )
    try:
        body = {
            "schema_version":   SCHEMA_VERSION,
            "tiers":            BAP_TIERS,
            "required_controls_by_tier": REQUIRED_CONTROLS_BY_TIER,
            "scenario_buckets": SCENARIO_BUCKETS,
            "tier_count":       len(BAP_TIERS),
        }
        log_audit_event(
            agent_name="API",
            action="BAP_ASSESSMENT_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"Returned tier ladder ({len(BAP_TIERS)} tiers + "
                f"per-tier control catalogue)"
            ),
        )
        return JSONResponse(body)
    except Exception as e:
        log_audit_event(
            agent_name="API",
            action="BAP_ASSESSMENT_FAILED",
            user_id=user_id,
            decision_logic=f"Tier ladder read failed: {e}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Tier ladder load failed: {e}",
        )


@router.get("/bap/exclusion-rules")
def get_exclusion_rules() -> JSONResponse:
    """Return the hard exclusion rules that force BAP-X.

    These are the use-case shapes that won't yield to 'control
    upward'. Reviewing this list is the fastest way for a
    pharma QA director to understand EVOLV's honesty contract:
    we will refuse deployments in certain shapes, regardless
    of how much customer revenue is at stake.

    :requirement: URS-40.9 - Read hard exclusion rules.
    """
    user_id = "system"
    log_audit_event(
        agent_name="API",
        action="BAP_ASSESSMENT_RECEIVED",
        user_id=user_id,
        decision_logic="GET /bap/exclusion-rules",
    )
    try:
        body = {
            "schema_version":  SCHEMA_VERSION,
            "rule_count":      len(EXCLUSION_RULES),
            "rules":           _serialise_exclusion_rules(),
            "principle":
                "The temptation in pharma is always to control "
                "upward (more documentation, more review). "
                "Some risks don't yield to that. The exclusion "
                "rules below name use-case shapes that should "
                "not run, regardless of controls applied.",
        }
        log_audit_event(
            agent_name="API",
            action="BAP_ASSESSMENT_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"Returned {len(EXCLUSION_RULES)} exclusion rules"
            ),
        )
        return JSONResponse(body)
    except Exception as e:
        log_audit_event(
            agent_name="API",
            action="BAP_ASSESSMENT_FAILED",
            user_id=user_id,
            decision_logic=f"Exclusion-rule read failed: {e}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Exclusion-rule load failed: {e}",
        )


@router.post("/bap/assess")
def post_assess(payload: BAPAssessRequest) -> JSONResponse:
    """Run a Context of Use through the three-layer diagnostic
    stack and return a full Bounded Autonomy Profile.

    Returns the structured BoundedAutonomyProfile dict. Audit
    triplet (RECEIVED / COMPLETED / FAILED) handled inside the
    engine. Every assessment writes a Logic Archive
    hash-linked to the audit trail so an inspector can replay
    the diagnostic from inputs alone.

    :requirement: URS-40.1 - Generate BAP via JSON API.
    """
    try:
        engine = BoundedAutonomyProfileEngine()
        profile = engine.assess(
            cou=payload.cou.model_dump(),
            user_id=payload.user_id,
        )
        return JSONResponse(profile.to_dict())
    except InvalidProfileInputError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Context of Use: {e}",
        )
    except BoundedAutonomyProfileError as e:
        raise HTTPException(
            status_code=500,
            detail=f"BAP assessment failed: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )


@router.post("/bap/pdf")
def post_assess_pdf(payload: BAPAssessPDFRequest) -> Response:
    """Generate a signed PDF Bounded Autonomy Profile report.

    EVOLV-branded format with prominent tier badge on the cover,
    full three-layer diagnostic, the 7-question Assurance
    Argument with Q7 Fragility Markers, and a 5-signer
    Manifestation of Signature page (pharma SOP RACI).

    :requirement: URS-40.11 - Generate signed BAP PDF.
    """
    try:
        engine = BoundedAutonomyProfileEngine()
        profile = engine.assess(
            cou=payload.cou.model_dump(),
            user_id=payload.user_id,
        )
        # Defer fpdf2 import to avoid loading on every JSON call
        from utils.pdf_generator import (   # noqa: E402
            generate_bounded_autonomy_profile_pdf,
        )
        pdf_bytes = generate_bounded_autonomy_profile_pdf(
            profile=profile.to_dict(),
            signers=payload.signers.model_dump(),
            meaning=payload.meaning,
        )
        return Response(
            content=bytes(pdf_bytes),   # fpdf2 returns bytearray
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="'
                    f'{profile.profile_id}.pdf"',
            },
        )
    except InvalidProfileInputError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Context of Use: {e}",
        )
    except BoundedAutonomyProfileError as e:
        raise HTTPException(
            status_code=500,
            detail=f"BAP assessment failed: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {e}",
        )


@router.post("/bap/check-exclusion")
def post_check_exclusion(
    payload: ExclusionCheckRequest,
) -> JSONResponse:
    """Pre-flight exclusion-only check.

    Useful for sales conversations and pre-flight screening
    before investing in a full BAP assessment. Returns the
    exclusion verdict (would_be_excluded: bool) + which rule(s)
    fired + the refusal rationale, without running the
    three-layer stack or writing audit rows.

    :requirement: URS-40.10 - Pre-flight exclusion check.
    """
    try:
        haystack = (
            f"{payload.statement} | {payload.decision_authority}"
        )
        hits: List[Dict[str, str]] = []
        for rule in EXCLUSION_RULES:
            if rule["pattern"].search(haystack):
                hits.append({
                    "rule_id":   rule["id"],
                    "violation": rule["violation"],
                    "why":       rule["why"],
                })
        return JSONResponse({
            "would_be_excluded": len(hits) > 0,
            "rules_fired":       hits,
            "verdict":           (
                "BAP-X (Out-of-Envelope Exclusion) - would refuse "
                "in this shape" if hits else
                "Would proceed to full three-layer assessment "
                "(BAP-0 through BAP-4 possible)"
            ),
            "principle":
                "If your statement uses words like 'AI signs', "
                "'AI releases', 'AI closes', 'AI modifies "
                "validated record', the engine will refuse to "
                "control-upward. Rewriting the statement with "
                "an explicit human-signature gate "
                "(e.g. 'AI drafts; QA signs') typically moves "
                "the deployment into BAP-2 or BAP-3.",
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Exclusion check failed: {e}",
        )
