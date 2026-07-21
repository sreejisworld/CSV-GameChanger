"""
versions.py — Version Registry + Transparency Dossier API.

Sprint 48 ("The Governable Vendor"). Exposes the answers to the
vendor-AI governance questions a pharma sponsor asks at
procurement:

- ``GET  /versions/registry``  — component/model registry +
  customer-facing changelog + notification commitment.
- ``POST /versions/dossier``   — generate the signed AI Vendor
  Transparency Dossier PDF from LIVE platform data (runs the
  eval suite + audit-chain verification, then renders).

:requirement: URS-48.1 - Machine-readable version registry API.
:requirement: URS-48.3 - One-click Transparency Dossier.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

router = APIRouter(tags=["Vendor Governance"])
_logger = logging.getLogger("evolv.versions")


class DossierRequest(BaseModel):
    """POST /versions/dossier request body."""
    signer_name: str = Field(
        "", max_length=200,
        description="Attestation signer (optional).",
    )
    meaning: str = Field(
        "Attestation of Dossier Accuracy", max_length=200,
    )


class SelfValidationRequest(BaseModel):
    """POST /versions/self-validation request body."""
    signer_name: str = Field(
        "", max_length=200,
        description="Validation approver (optional).",
    )
    meaning: str = Field(
        "Approval of Validation Package", max_length=200,
    )


@router.get("/versions/registry")
def get_version_registry() -> Dict[str, Any]:
    """Return the component/model version registry, the
    customer-facing changelog, and EVOLV's change-notification
    commitment.

    :requirement: URS-48.1 - Machine-readable version registry.
    """
    from Agents.version_registry import get_registry
    return get_registry()


@router.get("/versions/self-validation/rtm")
def self_validation_rtm() -> Dict[str, Any]:
    """Return EVOLV's own Requirements Traceability Matrix
    (URS -> implementation -> verification evidence), parsed
    from the living URS index. Lightweight — no OQ run.

    :requirement: URS-50.2 - Self-validation package assembler.
    """
    from Agents.self_validation import parse_urs_index
    rtm = parse_urs_index()
    return {
        "requirement_count": len(rtm),
        "traceability": [
            {
                "urs_id": r.urs_id,
                "requirement": r.requirement,
                "implementation": r.implementation,
                "verification": r.verification,
            }
            for r in rtm
        ],
    }


@router.post("/versions/self-validation")
def generate_self_validation(
    body: SelfValidationRequest,
) -> Response:
    """Generate EVOLV's signed self-validation package PDF
    (Validation Plan + IQ + OQ + Requirements Traceability
    Matrix), assembled from standing evidence with the OQ eval
    suite executed live. Emits the SELF_VALIDATION_* triplet.

    :requirement: URS-50.3 - Signed self-validation package PDF.
    """
    from Agents.integrity_manager import log_audit_event
    from Agents.self_validation import (
        generate_self_validation_package,
    )
    from utils.pdf_generator import generate_self_validation_pdf

    log_audit_event(
        agent_name="SelfValidation",
        action="SELF_VALIDATION_RECEIVED",
        decision_logic="Self-validation package requested",
    )
    try:
        pkg = generate_self_validation_package().to_dict()
        pdf_bytes = generate_self_validation_pdf(
            package=pkg,
            signer_name=body.signer_name,
            meaning=body.meaning,
        )
        oq = pkg.get("oq", {})
        log_audit_event(
            agent_name="SelfValidation",
            action="SELF_VALIDATION_COMPLETED",
            decision_logic=(
                f"Package generated: "
                f"{pkg.get('requirement_count')} requirements "
                f"traced, OQ {oq.get('passed')}/"
                f"{oq.get('total_tests')}, "
                f"{len(pdf_bytes)} bytes"
            ),
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    'attachment; '
                    'filename="EVOLV_Self_Validation'
                    '_Package.pdf"',
            },
        )
    except Exception as exc:
        _logger.exception(
            "[CSV-003] Self-validation generation failed: %s",
            exc,
        )
        log_audit_event(
            agent_name="SelfValidation",
            action="SELF_VALIDATION_FAILED",
            decision_logic="Self-validation raised an error.",
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Self-validation package generation "
                "failed. See server audit log for details."
            ),
        ) from exc


@router.post("/versions/dossier")
def generate_dossier(body: DossierRequest) -> Response:
    """Generate the signed AI Vendor Transparency Dossier PDF.

    Runs the full eval suite and audit-chain verification LIVE,
    assembles the version registry, and renders the dossier —
    so the document can never be stale marketing. Emits the
    DOSSIER_GENERATION_* audit triplet; the eval + verify runs
    append their own chained audit evidence.

    :requirement: URS-48.3 - One-click signed Transparency
                  Dossier assembled from live platform data.
    """
    from Agents.eval_suite import run_suite
    from Agents.integrity_manager import (
        log_audit_event,
        verify_audit_chain,
    )
    from Agents.version_registry import get_registry
    from utils.pdf_generator import (
        generate_transparency_dossier_pdf,
    )

    log_audit_event(
        agent_name="VersionRegistry",
        action="DOSSIER_GENERATION_RECEIVED",
        decision_logic=(
            "Transparency Dossier requested"
            + (f" (signer: {body.signer_name})"
               if body.signer_name else "")
        ),
    )
    try:
        runs = run_suite()
        total = sum(r.eval_count for r in runs)
        passed = sum(
            sum(1 for x in r.results if x.passed)
            for r in runs
        )
        eval_summary = {
            "total_evals": total,
            "total_passed": passed,
            "scoreboard": [
                {
                    "agent_name": r.agent_name,
                    "eval_count": r.eval_count,
                    "passed": sum(
                        1 for x in r.results if x.passed
                    ),
                    "pass_rate": r.aggregate_pass_rate,
                }
                for r in runs
            ],
        }
        chain = verify_audit_chain().to_dict()
        pdf_bytes = generate_transparency_dossier_pdf(
            eval_summary=eval_summary,
            chain_report=chain,
            registry=get_registry(),
            signer_name=body.signer_name,
            meaning=body.meaning,
        )
        log_audit_event(
            agent_name="VersionRegistry",
            action="DOSSIER_GENERATION_COMPLETED",
            decision_logic=(
                f"Dossier generated: {passed}/{total} evals, "
                f"chain "
                f"{'INTACT' if chain.get('intact') else 'BROKEN'}"
                f", {len(pdf_bytes)} bytes"
            ),
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    'attachment; filename="EVOLV_Transparency'
                    '_Dossier.pdf"',
            },
        )
    except Exception as exc:
        _logger.exception(
            "[CSV-003] Dossier generation failed: %s", exc,
        )
        log_audit_event(
            agent_name="VersionRegistry",
            action="DOSSIER_GENERATION_FAILED",
            decision_logic="Dossier generation raised an error.",
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Dossier generation failed. "
                "See server audit log for details."
            ),
        ) from exc
