"""
trustworthiness.py — Sprint 39 FastAPI router for the AI
Trustworthiness Credibility Assessment Report.

Endpoints
=========
- GET  /trustworthiness/frameworks
       Read the framework canon EVOLV currently maps against
       (NIST AI RMF, FDA GMLP, ISO 22989).
- POST /trustworthiness/detect-triggers
       Scan a project snapshot for the 5 SOP triggers that
       force a fresh assessment.
- POST /trustworthiness/generate
       Produce a full TrustworthinessReport dict from a COU.
- POST /trustworthiness/pdf
       Same as /generate but returns a signed PDF (EVOLV-branded,
       5-signer Manifestation of Signature page).

The principle: AI proposes the report; humans sign it.
The generator never modifies records, never triggers
revalidation. Bounded autonomy applied to the
trustworthiness reporting loop.

:requirement: URS-39.8 - Expose trustworthiness report via
              JSON + PDF API.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from API.security import sanitize_filename_component

_logger = logging.getLogger("evolv.trustworthiness")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.trustworthiness_report import (   # noqa: E402
    TrustworthinessReportGenerator,
    TrustworthinessReportError,
    InvalidContextOfUseError,
    detect_triggers,
    NIST_AI_RMF,
    FDA_GMLP,
    ISO_22989_TERMS,
    TRIGGERS_FOR_REPORT,
    REQUIRED_SIGNERS,
    SCHEMA_VERSION,
)
from Agents.integrity_manager import log_audit_event   # noqa: E402


router = APIRouter(tags=["AI Trustworthiness"])


# ── Pydantic models ──────────────────────────────────────────────────

class _ContextOfUseModel(BaseModel):
    """Per-deployment Context of Use — the unit of assessment."""
    customer_name:       str = Field(max_length=200)
    statement:           str = Field(
        max_length=4000,
        description="What the AI does in this deployment — one "
                    "sentence. e.g. 'EVOLV drafts URs and FRs for "
                    "a GxP-Direct LIMS at a CDMO; outputs require "
                    "QA sign-off before being persisted to Vault.'",
    )
    deployment_region:   str = Field(
        max_length=30,
        description="'US' | 'EU' | 'UK' | 'India' | 'APAC' | "
                    "'Global'",
    )
    gxp_classification:  str = Field(
        max_length=30,
        description="'GxP Direct' | 'GxP Indirect' | 'Non-GxP'",
    )
    risk_level:          str = Field(
        max_length=30,
        description="'High' | 'Medium' | 'Low'",
    )
    decision_authority:  str = Field(
        default="AI proposes, human signs",
        max_length=500,
        description="Who has the last word on AI-drafted outputs.",
    )
    target_system:       str = Field("", max_length=200)
    integrates_with:     List[str] = Field(default_factory=list)
    triggers_detected:   List[str] = Field(default_factory=list)
    poc_or_production:   str = Field("POC", max_length=30)
    cou_id:              Optional[str] = Field(
        None, max_length=100,
    )


class GenerateReportRequest(BaseModel):
    """POST /trustworthiness/generate request body."""
    cou:                 _ContextOfUseModel
    primary_frameworks:  Optional[List[str]] = Field(
        default=None,
        description="Override the framework canon. US default "
                    "(when omitted) = NIST AI RMF + FDA GMLP + "
                    "ISO 22989. EU customers should pass "
                    "['NIST AI RMF 1.0','EU AI Act','ISO/IEC "
                    "42001:2023']; India customers will add "
                    "CDSCO + WHO-GMP in a future sprint.",
    )
    user_id:             str = "demo"

    model_config = {
        "json_schema_extra": {
            "example": {
                "cou": {
                    "customer_name":       "Demo CDMO",
                    "statement":
                        "EVOLV drafts URs and FRs for a GxP-Direct "
                        "LIMS at a CDMO; outputs require QA "
                        "sign-off before being persisted to Vault.",
                    "deployment_region":   "US",
                    "gxp_classification":  "GxP Direct",
                    "risk_level":          "High",
                    "decision_authority":
                        "AI proposes, human signs",
                    "target_system":       "LabCore LIMS v4.2",
                    "integrates_with":
                        ["Veeva Vault", "SAP"],
                    "triggers_detected":
                        ["T1_NEW_TOOL_TO_GXP", "T5_POC_TO_PROD"],
                    "poc_or_production":   "POC",
                },
                "primary_frameworks":
                    ["NIST AI RMF 1.0", "FDA GMLP (Oct 2021)",
                     "ISO/IEC 22989:2021"],
                "user_id":             "demo",
            },
        },
    }


class _PDFSignerMeta(BaseModel):
    """Optional pre-filled signer names on the Manifestation
    of Signature page. Empty fields render as blank signature
    lines for wet/electronic signing post-PDF."""
    business_owner:  str = ""
    quality_assurance: str = ""
    service_owner:   str = ""
    system_sme:      str = ""
    ai_model_sme:    str = ""


class GenerateReportPDFRequest(GenerateReportRequest):
    """POST /trustworthiness/pdf request body — extends
    GenerateReportRequest with signature-page metadata."""
    meaning:    str = "Approval of AI Trustworthiness Assessment"
    signers:    _PDFSignerMeta = Field(default_factory=_PDFSignerMeta)


class TriggerDetectionRequest(BaseModel):
    """POST /trustworthiness/detect-triggers request body."""
    snapshot: Dict[str, Any] = Field(
        description="Project snapshot with optional keys: "
                    "is_new_tool (bool), new_models_added (list), "
                    "major_version_bumps (list), new_cous (list), "
                    "poc_to_production_promotion (bool).",
    )
    user_id:  str = "demo"

    model_config = {
        "json_schema_extra": {
            "example": {
                "snapshot": {
                    "is_new_tool": False,
                    "new_models_added": ["Claude 3.7"],
                    "major_version_bumps": [],
                    "new_cous": [],
                    "poc_to_production_promotion": True,
                },
                "user_id": "demo",
            },
        },
    }


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/trustworthiness/frameworks")
def get_frameworks() -> JSONResponse:
    """Return the framework canon EVOLV currently maps against.

    Read-only. Pharma evaluators read this first to confirm
    EVOLV speaks their language: 'do you cover NIST? FDA GMLP?
    ISO 42001? EU AI Act?'

    :requirement: URS-39.9 - Read framework canon.
    """
    user_id = "system"
    log_audit_event(
        agent_name="API",
        action="TWR_GENERATION_RECEIVED",
        user_id=user_id,
        decision_logic="GET /trustworthiness/frameworks",
    )
    try:
        body = {
            "schema_version": SCHEMA_VERSION,
            "primary_default": [
                "NIST AI RMF 1.0",
                "FDA GMLP (Oct 2021)",
                "ISO/IEC 22989:2021",
            ],
            "available_canons": {
                "NIST AI RMF 1.0": {
                    "control_count": len(NIST_AI_RMF),
                    "functions":     sorted({
                        v["function"] for v in NIST_AI_RMF.values()
                    }),
                    "controls": NIST_AI_RMF,
                },
                "FDA GMLP (Oct 2021)": {
                    "principle_count": len(FDA_GMLP),
                    "principles":      FDA_GMLP,
                },
                "ISO/IEC 22989:2021": {
                    "term_count": len(ISO_22989_TERMS),
                    "terms":      ISO_22989_TERMS,
                },
            },
            "triggers":         TRIGGERS_FOR_REPORT,
            "required_signers": REQUIRED_SIGNERS,
        }
        log_audit_event(
            agent_name="API",
            action="TWR_GENERATION_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"Returned framework canon "
                f"({len(NIST_AI_RMF)} NIST + "
                f"{len(FDA_GMLP)} FDA + "
                f"{len(ISO_22989_TERMS)} ISO 22989)"
            ),
        )
        return JSONResponse(body)
    except Exception as e:
        log_audit_event(
            agent_name="API",
            action="TWR_GENERATION_FAILED",
            user_id=user_id,
            decision_logic=f"Framework canon read failed: {e}",
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Framework canon load failed. "
                "See server audit log for details."
            ),
        )


@router.post("/trustworthiness/detect-triggers")
def post_detect_triggers(
    payload: TriggerDetectionRequest,
) -> JSONResponse:
    """Scan a project snapshot for the 5 SOP triggers.

    Returns the fired trigger IDs + their human-readable
    labels. Caller's job is to decide whether to invoke
    /generate when triggers fire.

    :requirement: URS-39.6 - Auto-detect SOP triggers.
    """
    try:
        fired_ids = detect_triggers(payload.snapshot)
        label_map = {t["id"]: t["label"] for t in TRIGGERS_FOR_REPORT}
        return JSONResponse({
            "fired_triggers": [
                {"id": tid, "label": label_map[tid]}
                for tid in fired_ids
            ],
            "all_triggers":    TRIGGERS_FOR_REPORT,
            "snapshot_inputs": payload.snapshot,
            "report_required": len(fired_ids) > 0,
        })
    except Exception as e:
        _logger.exception(
            "[CSV-003] Trigger detection failed: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Trigger detection failed. "
                "See server log for details."
            ),
        )


@router.post("/trustworthiness/generate")
def post_generate(payload: GenerateReportRequest) -> JSONResponse:
    """Generate a full AI Trustworthiness Credibility Assessment
    Report for a given Context of Use.

    Returns the structured report dict. Auto-detects 5 SOP
    triggers if `triggers_detected` was left empty. Every
    assessment writes a Logic Archive hash-linked to the
    audit trail.

    :requirement: URS-39.1 - Generate trustworthiness report
                  via JSON API.
    """
    try:
        generator = TrustworthinessReportGenerator(
            primary_frameworks=payload.primary_frameworks,
        )
        report = generator.generate(
            cou=payload.cou.model_dump(),
            user_id=payload.user_id,
        )
        return JSONResponse(report.to_dict())

    except InvalidContextOfUseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Context of Use: {e}",
        )
    except TrustworthinessReportError as e:
        _logger.exception(
            "[CSV-003] TWR generation failed: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Report generation failed. "
                "See server audit log for details."
            ),
        )
    except Exception as e:
        _logger.exception(
            "[CSV-003] Unexpected TWR error: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Unexpected error during report "
                "generation. See server log for details."
            ),
        )


@router.post("/trustworthiness/pdf")
def post_generate_pdf(
    payload: GenerateReportPDFRequest,
) -> Response:
    """Generate a signed PDF trustworthiness report.

    EVOLV-branded format (per Sprint 39 product choice — focus
    on content, re-skin for customer templates later). 5-signer
    Manifestation of Signature page per pharma SOP RACI pattern.

    :requirement: URS-39.10 - Generate signed PDF trustworthiness
                  report.
    """
    try:
        # Engine first — get the structured report
        generator = TrustworthinessReportGenerator(
            primary_frameworks=payload.primary_frameworks,
        )
        report = generator.generate(
            cou=payload.cou.model_dump(),
            user_id=payload.user_id,
        )

        # PDF second — defer import to avoid loading fpdf2
        # on every API call to the JSON endpoints
        from utils.pdf_generator import (   # noqa: E402
            generate_trustworthiness_report_pdf,
        )
        pdf_bytes = generate_trustworthiness_report_pdf(
            report=report.to_dict(),
            signers=payload.signers.model_dump(),
            meaning=payload.meaning,
        )
        # fpdf2 returns bytearray; Response expects bytes.
        safe_report = sanitize_filename_component(
            report.report_id, default="twr-report",
        )
        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="'
                    f'{safe_report}.pdf"',
            },
        )

    except InvalidContextOfUseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Context of Use: {e}",
        )
    except TrustworthinessReportError as e:
        _logger.exception(
            "[CSV-003] TWR generation failed: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Report generation failed. "
                "See server audit log for details."
            ),
        )
    except Exception as e:
        _logger.exception(
            "[CSV-003] TWR PDF generation failed: %s", e,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] PDF generation failed. "
                "See server log for details."
            ),
        )
