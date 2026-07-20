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


@router.get("/versions/registry")
def get_version_registry() -> Dict[str, Any]:
    """Return the component/model version registry, the
    customer-facing changelog, and EVOLV's change-notification
    commitment.

    :requirement: URS-48.1 - Machine-readable version registry.
    """
    from Agents.version_registry import get_registry
    return get_registry()


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
