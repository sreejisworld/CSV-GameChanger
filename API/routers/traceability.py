"""
Traceability Matrix export router.

:requirement: URS-28.4 - System shall produce a signed Traceability
              Matrix Inspection Export PDF from a filtered slice.
:requirement: URS-28.5 - Traceability export endpoint emits the
              standard 3-event audit triplet
              (RECEIVED / COMPLETED / FAILED) per EVOLV API rules.

The Living Traceability Matrix itself is computed entirely in the
React store (it's a pure read-model over Zustand state — see
``computeTraceability()`` in ``apps/TraceabilityMatrix.jsx``).
This router only exists to render that already-computed matrix as
a signed PDF for inspector handoff.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(tags=["Traceability"])


# ── Models ──────────────────────────────────────────────────────────


class TraceabilityExportRequest(BaseModel):
    """Request body for filtered traceability slice -> signed PDF."""

    rows: List[Dict[str, Any]] = Field(
        ...,
        description=(
            "The filtered traceability rows the user wants "
            "in the PDF. Shape matches the React "
            "computeTraceability() output."
        ),
    )
    project_name: str = Field(
        default="Untitled Project",
        description="Project / system name for the cover page.",
    )
    signer_name: str = Field(
        ...,
        min_length=1,
        description=(
            "Approver full name for Manifestation of Signature."
        ),
    )
    meaning: str = Field(
        default="Traceability Matrix Inspection Export",
        description="Meaning of the electronic signature.",
    )
    filter_summary: str = Field(
        default="",
        description="Human-readable summary of the active filters.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rows": [
                        {
                            "ursId": "UR-1",
                            "statement": "Track temperature.",
                            "riskLevel": "High",
                            "isGxpDirect": True,
                            "childCount": 2,
                            "bundle": {
                                "id": "TB-UR-1",
                                "stepCount": 7,
                            },
                            "runs": [
                                {
                                    "runId": "RUN-TB-UR-1-1",
                                    "status": "locked",
                                    "passed": 5,
                                    "failed": 0,
                                }
                            ],
                            "passedCount":   5,
                            "failedCount":   0,
                            "totalSteps":    7,
                            "defectCount":   0,
                            "openDefects":   0,
                            "released":      True,
                            "approvalCount": 2,
                            "status":        "released",
                        }
                    ],
                    "project_name": "LabCore LIMS",
                    "signer_name":  "Jane Smith",
                    "meaning": (
                        "Traceability Matrix Inspection Export"
                    ),
                    "filter_summary": "All rows · GxP Direct only",
                }
            ]
        }
    }


# ── Endpoint ────────────────────────────────────────────────────────


@router.post("/traceability/export-pdf")
def export_traceability_matrix_pdf(
    body: TraceabilityExportRequest,
):
    """Render a filtered Traceability Matrix slice as a signed PDF.

    Lazy-imports the PDF generator and the audit logger so the
    router module stays cheap to import. Emits the standard
    3-event audit triplet (RECEIVED / COMPLETED / FAILED) per
    the EVOLV API rules (`.claude/rules/api.md`).

    :param body: Validated TraceabilityExportRequest.
    :return: ``application/pdf`` Response with attachment headers.
    :requirement: URS-28.4 - Generate signed Traceability Matrix
                  Inspection Export PDF.
    :requirement: URS-28.5 - Audit triplet on every export.
    """
    from Agents.integrity_manager import log_audit_event
    from utils.pdf_generator import generate_traceability_matrix_pdf

    log_audit_event(
        agent_name="TraceabilityRouter",
        action="TRACEABILITY_EXPORT_RECEIVED",
        decision_logic=(
            f"RTM export requested by {body.signer_name} "
            f"({len(body.rows)} rows) "
            f"for '{body.project_name}'"
        ),
    )

    try:
        pdf_bytes = generate_traceability_matrix_pdf(
            rows=body.rows,
            project_name=body.project_name,
            signer_name=body.signer_name,
            meaning=(
                body.meaning
                or "Traceability Matrix Inspection Export"
            ),
            filter_summary=body.filter_summary,
        )
    except Exception as exc:
        log_audit_event(
            agent_name="TraceabilityRouter",
            action="TRACEABILITY_EXPORT_FAILED",
            decision_logic=(
                f"RTM export failed for '{body.project_name}': "
                f"{type(exc).__name__}: {exc}"
            ),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Traceability export failed: {exc}",
        )

    log_audit_event(
        agent_name="TraceabilityRouter",
        action="TRACEABILITY_EXPORT_COMPLETED",
        decision_logic=(
            f"RTM PDF generated for '{body.project_name}' "
            f"signed by {body.signer_name} "
            f"({len(body.rows)} rows, {len(pdf_bytes)} bytes)"
        ),
    )

    safe_proj = "".join(
        c if c.isalnum() else "-"
        for c in body.project_name.lower()
    ).strip("-") or "project"
    filename = f"traceability-matrix-{safe_proj}.pdf"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )
