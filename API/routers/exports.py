"""
Exports Router — PDF generation for React lifecycle pages.

POST /exports/verify-report   — Test Execution Report PDF
                                (script metadata + step results + e-sig)
POST /exports/release-package — Release Authorization Package PDF
                                (approvals + lifecycle summary + e-sig)

These endpoints receive JSON from the React shell and return
application/pdf bytes for direct browser download.

:requirement: URS-25.1 - System shall generate Test Execution Report
              PDF from React Verify page data.
:requirement: URS-25.2 - System shall generate Release Package PDF
              from React Release page approvals.
:requirement: URS-25.3 - All export PDFs shall include a
              Manifestation of Signature page per 21 CFR §11.50.
"""
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(tags=["Exports"])

# ── fpdf2 helper ───────────────────────────────────────────────────
def _fpdf():
    try:
        from fpdf import FPDF
        return FPDF
    except ImportError:
        return None


# ── Shared PDF builder helpers ─────────────────────────────────────
def _header(pdf, title: str, subtitle: str = "") -> None:
    """Draw branded EVOLV page header."""
    pdf.set_fill_color(7, 7, 15)
    pdf.rect(0, 0, 210, 18, "F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(0, 127, 255)
    pdf.set_xy(10, 5)
    pdf.cell(0, 5, "EVOLV | The Validation Factory", ln=True)
    if subtitle:
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(140, 140, 160)
        pdf.set_x(10)
        pdf.cell(0, 4, subtitle, ln=True)
    pdf.set_draw_color(0, 127, 255)
    pdf.set_line_width(0.3)
    pdf.line(0, 18, 210, 18)
    pdf.ln(6)


def _footer(pdf, page_num: int, total_pages: int) -> None:
    """Draw branded page footer."""
    pdf.set_y(-14)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(0, 4,
             f"EVOLV | The Validation Factory  ·  "
             f"WingstarTech Inc.  ·  "
             f"Page {page_num} of {total_pages}  ·  "
             f"GAMP 5 / CSA / 21 CFR Part 11 Compliant",
             align="C")


def _kv(pdf, label: str, value: str,
        label_w: int = 55, row_h: int = 6) -> None:
    """Render a key-value pair row."""
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(140, 140, 160)
    pdf.cell(label_w, row_h, label)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(232, 232, 240)
    pdf.multi_cell(0, row_h, str(value or "—"), ln=True)


def _section(pdf, title: str) -> None:
    """Render a section heading."""
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(0, 127, 255)
    pdf.cell(0, 6, title.upper(), ln=True)
    pdf.set_draw_color(0, 127, 255)
    pdf.set_line_width(0.2)
    pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)


def _mos_page(pdf, signer_name: str, meaning: str,
              doc_title: str, reasoning_hash: str = "") -> None:
    """
    Add a Manifestation of Signature page (21 CFR Part 11 §11.50).

    :requirement: URS-25.3 - All export PDFs shall include a
                  Manifestation of Signature page per 21 CFR §11.50.
    """
    pdf.add_page()
    _header(pdf, doc_title,
            subtitle="Manifestation of Signature  |  21 CFR Part 11 §11.50")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(232, 232, 240)
    pdf.cell(0, 8, "Manifestation of Signature", ln=True, align="C")
    pdf.ln(4)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Signature table
    col_w = [55, 55, 55, 25]
    headers = ["Document", "Signer Name", "Timestamp (UTC)", "Meaning"]
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(14, 14, 26)
    pdf.set_text_color(0, 127, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(232, 232, 240)
    row_vals = [doc_title[:40], signer_name, ts, meaning[:20]]
    for i, v in enumerate(row_vals):
        pdf.cell(col_w[i], 7, v, border=1)
    pdf.ln(10)

    # Signature line
    pdf.set_draw_color(100, 100, 120)
    pdf.set_line_width(0.4)
    x = pdf.get_x() + 10
    pdf.line(x, pdf.get_y(), x + 80, pdf.get_y())
    pdf.set_xy(x, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(80, 4, "Authorized Signature", ln=False)
    pdf.set_x(x + 90)
    pdf.line(x + 90, pdf.get_y() - 2, x + 140, pdf.get_y() - 2)
    pdf.set_x(x + 90)
    pdf.cell(50, 4, "Date", ln=True)
    pdf.ln(6)

    if reasoning_hash:
        pdf.set_font("Courier", "", 6)
        pdf.set_text_color(100, 100, 120)
        pdf.multi_cell(0, 4,
                       f"Chain-of-custody hash: {reasoning_hash}",
                       ln=True)
        pdf.ln(2)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 120)
    pdf.multi_cell(0, 4,
                   "This electronic record and associated electronic signature "
                   "are compliant with 21 CFR Part 11 Section 11.50. "
                   "The signature is legally binding and equivalent to a "
                   "handwritten signature per §11.100.",
                   ln=True)


# ── Request models ─────────────────────────────────────────────────
class StepResultIn(BaseModel):
    step_number:   int
    step_type:     str
    step_title:    str
    step_instruction:   Optional[str] = ""
    expected_result:    Optional[str] = ""
    test_case_type:     Optional[str] = ""
    requirement_reference: Optional[str] = ""
    verdict:       Optional[str] = None
    actual_result: Optional[str] = ""
    executed_at:   Optional[str] = None
    tester_name:   Optional[str] = ""


class VerifyReportRequest(BaseModel):
    script_id:      str
    urs_id:         Optional[str] = ""
    ur_id:          Optional[str] = ""
    test_type:      Optional[str] = ""
    risk_level:     Optional[str] = ""
    test_strategy:  Optional[str] = ""
    project_name:   Optional[str] = ""
    gamp_category:  Optional[str] = ""
    run_id:         Optional[str] = ""
    started_at:     Optional[str] = None
    locked_at:      Optional[str] = None
    signer_name:    str
    signing_meaning: Optional[str] = "Approval of Test Execution"
    reasoning_hash: Optional[str] = ""
    pass_count:     int = 0
    fail_count:     int = 0
    blocked_count:  int = 0
    na_count:       int = 0
    total_steps:    int = 0
    overall_verdict: Optional[str] = ""
    steps:          List[StepResultIn] = []


class ApprovalIn(BaseModel):
    name:          str
    role:          Optional[str] = ""
    meaning:       Optional[str] = ""
    signed_at:     Optional[str] = None
    reasoning_hash: Optional[str] = ""


class ReleasePackageRequest(BaseModel):
    project_name:    str
    gamp_category:   Optional[str] = ""
    released_at:     Optional[str] = None
    approvals:       List[ApprovalIn] = []
    phase_completion: Optional[Dict[str, bool]] = None
    test_verdict:    Optional[str] = ""
    frameworks:      Optional[List[str]] = None


# ── Sprint 18.2 — Validation Deliverables Pack ────────────────────
class ValidationPlanRequest(BaseModel):
    """Request payload for POST /exports/validation-plan."""
    plan_data:    Dict[str, Any]
    signer_name:  str
    meaning:      Optional[str] = "Approval of Validation Plan"


class DesignSpecRequest(BaseModel):
    """Request payload for POST /exports/design-specification."""
    plan_data:    Dict[str, Any]
    design_data:  Dict[str, Any]
    requirements: List[Dict[str, Any]] = []
    risk_data:    Dict[str, Dict[str, Any]] = {}
    test_bundles: Dict[str, Dict[str, Any]] = {}
    signer_name:  str
    meaning:      Optional[str] = "Approval of Design Specification"


class ValidationSummaryRequest(BaseModel):
    """Request payload for POST /exports/validation-summary-report."""
    plan_data:    Dict[str, Any]
    requirements: List[Dict[str, Any]] = []
    risk_data:    Dict[str, Dict[str, Any]] = {}
    test_runs:    Dict[str, Dict[str, Any]] = {}
    defects:      Dict[str, List[Dict[str, Any]]] = {}
    qa_reviews:   Dict[str, Dict[str, Any]] = {}
    release_data: Dict[str, Any] = {}
    signer_name:  str
    meaning: Optional[str] = (
        "Approval of Validation Summary Report"
    )


# ── Endpoints ──────────────────────────────────────────────────────
@router.post(
    "/exports/verify-report",
    summary="Generate Test Execution Report PDF",
)
def export_verify_report(body: VerifyReportRequest):
    """
    Generates a Test Execution Report PDF from the React Verify
    page state. Returns raw PDF bytes as application/pdf.

    :requirement: URS-25.1 - System shall generate Test Execution
                  Report PDF from React Verify page data.
    """
    FPDF = _fpdf()
    if FPDF is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="fpdf2 is not installed. Run: pip install fpdf2",
        )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(10, 22, 10)

    # ── Page 1: Cover + Summary ────────────────────────────────────
    pdf.add_page()
    _header(pdf, "Test Execution Report",
            subtitle=(
                f"{body.script_id}  ·  "
                f"{body.project_name or 'Untitled Project'}"
            ))

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(232, 232, 240)
    pdf.cell(0, 9, "Test Execution Report", ln=True, align="C")
    _ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(140, 140, 160)
    pdf.cell(0, 5, f"Generated {_ts}", ln=True, align="C")
    pdf.ln(6)

    _section(pdf, "Script Metadata")
    _kv(pdf, "Script ID",      body.script_id)
    _kv(pdf, "URS / UR ID",
        f"{body.urs_id or '—'}  /  {body.ur_id or '—'}")
    _kv(pdf, "Test Type",      body.test_type)
    _kv(pdf, "Risk Level",     body.risk_level)
    _kv(pdf, "Test Strategy",  body.test_strategy)
    _kv(pdf, "Project",        body.project_name)
    _kv(pdf, "GAMP Category",  body.gamp_category)

    _section(pdf, "Execution Summary")
    verdict_color = {
        "PASS": (50, 205, 50),
        "FAIL": (239, 68, 68),
        "BLOCKED": (245, 158, 11),
    }.get((body.overall_verdict or "").upper(), (100, 116, 139))

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*verdict_color)
    pdf.cell(0, 10, body.overall_verdict or "IN PROGRESS",
             ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(232, 232, 240)
    pdf.cell(0, 6,
             f"Pass: {body.pass_count}   "
             f"Fail: {body.fail_count}   "
             f"Blocked: {body.blocked_count}   "
             f"N/A: {body.na_count}   "
             f"/ {body.total_steps} steps",
             ln=True, align="C")
    pdf.ln(4)

    if body.locked_at:
        _section(pdf, "Sign-off")
        _kv(pdf, "Signer",  body.signer_name)
        _kv(pdf, "Meaning", body.signing_meaning)
        _kv(pdf, "Locked At",
            body.locked_at[:19].replace("T", " ") + " UTC")
        if body.reasoning_hash:
            pdf.set_font("Courier", "", 6)
            pdf.set_text_color(100, 100, 120)
            pdf.multi_cell(0, 4,
                           f"Hash: {body.reasoning_hash}", ln=True)

    _footer(pdf, 1, 3)

    # ── Page 2: Steps Table (Landscape) ───────────────────────────
    pdf.add_page(orientation="L")
    _header(pdf, "Test Execution Report — Steps",
            subtitle=f"{body.script_id}")

    col_w = [8, 12, 35, 55, 40, 16, 28, 12, 40, 22]
    headers = [
        "#", "Type", "Title", "Instruction",
        "Expected Result", "Case", "Ref",
        "Verdict", "Actual Result", "Timestamp",
    ]
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_fill_color(14, 14, 26)
    pdf.set_text_color(0, 127, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 6, h, border=1, fill=True)
    pdf.ln()

    VERDICT_BG = {
        "pass":    (50, 205, 50),
        "fail":    (239, 68, 68),
        "blocked": (245, 158, 11),
        "na":      (100, 116, 139),
    }

    for step in body.steps:
        verdict_rgb = VERDICT_BG.get(
            (step.verdict or "").lower(), (60, 60, 80)
        )
        ts_str = ""
        if step.executed_at:
            try:
                ts_str = step.executed_at[11:16]
            except Exception:
                ts_str = ""

        row_vals = [
            str(step.step_number),
            step.step_type[:8],
            step.step_title[:30],
            (step.step_instruction or "")[:60],
            (step.expected_result or "")[:45],
            (step.test_case_type or "")[:14],
            (step.requirement_reference or "")[:25],
            (step.verdict or "—").upper()[:8],
            (step.actual_result or "")[:45],
            ts_str,
        ]

        max_h = 5
        pdf.set_font("Helvetica", "", 5.5)
        for i, val in enumerate(row_vals):
            is_verdict = (i == 7)
            if is_verdict and step.verdict:
                pdf.set_fill_color(*verdict_rgb)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(col_w[i], max_h, val, border=1, fill=True)
            else:
                pdf.set_fill_color(18, 18, 30)
                pdf.set_text_color(180, 180, 200)
                pdf.cell(col_w[i], max_h, val, border=1, fill=True)
        pdf.ln()

    _footer(pdf, 2, 3)

    # ── Page 3: MoS ───────────────────────────────────────────────
    _mos_page(
        pdf,
        signer_name=body.signer_name,
        meaning=body.signing_meaning or "Approval of Test Execution",
        doc_title=f"Test Execution Report — {body.script_id}",
        reasoning_hash=body.reasoning_hash or "",
    )
    _footer(pdf, 3, 3)

    buf = BytesIO()
    pdf.output(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="test-report-'
                f'{body.script_id}.pdf"',
        },
    )


@router.post(
    "/exports/release-package",
    summary="Generate Release Authorization Package PDF",
)
def export_release_package(body: ReleasePackageRequest):
    """
    Generates a Release Authorization Package PDF from the React
    Release page state. Returns raw PDF bytes as application/pdf.

    :requirement: URS-25.2 - System shall generate Release Package
                  PDF from React Release page approvals.
    """
    FPDF = _fpdf()
    if FPDF is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="fpdf2 is not installed. Run: pip install fpdf2",
        )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(10, 22, 10)

    total_pages = 2 + (1 if body.approvals else 0)

    # ── Page 1: Release Summary ────────────────────────────────────
    pdf.add_page()
    _header(pdf, "Release Authorization Package",
            subtitle=body.project_name or "Untitled Project")

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(232, 232, 240)
    pdf.cell(0, 9, "Release Authorization Package", ln=True, align="C")
    _ts2 = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(140, 140, 160)
    pdf.cell(0, 5, f"Generated {_ts2}", ln=True, align="C")
    pdf.ln(6)

    _section(pdf, "Project Information")
    _kv(pdf, "Project Name",    body.project_name)
    _kv(pdf, "GAMP Category",   body.gamp_category)
    _kv(pdf, "Released At",
        (body.released_at or "")[:19].replace("T", " ") + " UTC"
        if body.released_at else "—")
    _kv(pdf, "Test Verdict",    body.test_verdict or "—")
    _kv(pdf, "Frameworks",
        ", ".join(body.frameworks or []) or "—")

    if body.phase_completion:
        _section(pdf, "Lifecycle Completion")
        done = [k for k, v in body.phase_completion.items() if v]
        pending = [k for k, v in body.phase_completion.items() if not v]
        _kv(pdf, "Complete",
            ", ".join(done) if done else "None")
        _kv(pdf, "Pending",
            ", ".join(pending) if pending else "None")

    # Release status badge
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(50, 205, 50)
    pdf.cell(0, 10, "✓  SYSTEM RELEASED", ln=True, align="C")

    _footer(pdf, 1, total_pages)

    # ── Page 2: Approvals Table ────────────────────────────────────
    if body.approvals:
        pdf.add_page()
        _header(pdf, "Release Authorization Package",
                subtitle="Electronic Approvals")

        _section(pdf, "Approver Sign-offs")
        col_w = [45, 35, 45, 35, 30]
        hdr   = ["Name", "Role", "Meaning",
                 "Signed At (UTC)", "Hash (short)"]
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(14, 14, 26)
        pdf.set_text_color(0, 127, 255)
        for i, h in enumerate(hdr):
            pdf.cell(col_w[i], 6, h, border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(232, 232, 240)
        for idx, a in enumerate(body.approvals, 1):
            ts = (a.signed_at or "")[:16].replace("T", " ")
            h_short = (a.reasoning_hash or "")[:12] + "…" \
                if a.reasoning_hash else "—"
            pdf.set_fill_color(18 + idx * 2, 18 + idx * 2, 30)
            row = [a.name, a.role or "", a.meaning or "", ts, h_short]
            for i, v in enumerate(row):
                pdf.cell(col_w[i], 6, str(v), border=1, fill=True)
            pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 100, 120)
        pdf.multi_cell(0, 4,
                       "All signatures are electronically captured and "
                       "compliant with 21 CFR Part 11 §11.50. Each approval "
                       "is independently logged to the immutable audit trail "
                       "with a SHA-256 chain-of-custody hash.",
                       ln=True)

        _footer(pdf, 2, total_pages)

    # ── Final page: MoS ───────────────────────────────────────────
    first_approver = body.approvals[0] if body.approvals else None
    _mos_page(
        pdf,
        signer_name=first_approver.name if first_approver else "—",
        meaning=(first_approver.meaning
                 if first_approver else "Approval for Release"),
        doc_title=(
            f"Release Authorization Package — "
            f"{body.project_name}"
        ),
        reasoning_hash=(first_approver.reasoning_hash or "")
            if first_approver else "",
    )
    _footer(pdf, total_pages, total_pages)

    buf = BytesIO()
    pdf.output(buf)
    safe_name = (body.project_name or "project").replace(" ", "-")
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="release-package-'
                f'{safe_name}.pdf"',
        },
    )


# ── Sprint 18.2 — Validation Deliverables Pack ────────────────────
#
# Three thin endpoints that delegate to utils/pdf_generator.py
# (per CLAUDE.md: PDF logic lives there, not inline in the router).
# Each emits the standard RECEIVED / COMPLETED / FAILED audit
# triplet via integrity_manager.log_audit_event().

def _slug(name: str) -> str:
    """Filesystem-safe ASCII slug for the PDF filename."""
    return "".join(
        c if c.isalnum() else "-" for c in (name or "")
    ).strip("-").lower() or "project"


def _pdf_response(
    pdf_bytes: bytes,
    filename: str,
) -> Response:
    """Return a uniformly-shaped application/pdf Response.

    fpdf2's ``pdf.output()`` returns ``bytearray``; Starlette's
    ``Response.render()`` calls ``.encode()`` on non-``bytes`` content,
    which fails on ``bytearray``. Coerce explicitly.

    :requirement: URS-26.4
    """
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/exports/validation-plan",
    summary="Generate Validation Plan (VP) PDF",
)
def export_validation_plan(body: ValidationPlanRequest):
    """Render the Validation Plan into a signed PDF.

    Receives a ``plan_data`` dict (matches the React Plan page
    Zustand slice) and a signer identity. Returns the PDF as
    application/pdf bytes.

    :requirement: URS-26.1 - Generate Validation Plan PDF.
    """
    from Agents.integrity_manager import log_audit_event
    from utils.pdf_generator import (
        generate_validation_plan_pdf,
    )

    project_name = (
        body.plan_data.get("projectName") or "Untitled Project"
    )
    log_audit_event(
        agent_name="ExportsRouter",
        action="VALIDATION_PLAN_EXPORT_RECEIVED",
        decision_logic=(
            f"VP export requested for project "
            f"'{project_name}' by {body.signer_name}"
        ),
    )

    try:
        pdf_bytes = generate_validation_plan_pdf(
            plan_data=body.plan_data,
            signer_name=body.signer_name,
            meaning=body.meaning
                or "Approval of Validation Plan",
        )
    except Exception as exc:
        log_audit_event(
            agent_name="ExportsRouter",
            action="VALIDATION_PLAN_EXPORT_FAILED",
            decision_logic=(
                f"VP export failed for '{project_name}': "
                f"{type(exc).__name__}: {exc}"
            ),
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"VP generation failed: {exc}",
        )

    log_audit_event(
        agent_name="ExportsRouter",
        action="VALIDATION_PLAN_EXPORT_COMPLETED",
        decision_logic=(
            f"VP exported for '{project_name}' "
            f"({len(pdf_bytes)} bytes) "
            f"signed by {body.signer_name}"
        ),
    )

    return _pdf_response(
        pdf_bytes,
        f"validation-plan-{_slug(project_name)}.pdf",
    )


@router.post(
    "/exports/design-specification",
    summary="Generate Design Specification PDF",
)
def export_design_specification(body: DesignSpecRequest):
    """Render the Design Specification into a signed PDF.

    Includes architecture / HLD / LLD / integration notes, the
    configuration items table, and a UR -> FR -> Test Bundle
    traceability matrix.

    :requirement: URS-26.2 - Generate Design Specification PDF
                  with requirement-to-test traceability matrix.
    """
    from Agents.integrity_manager import log_audit_event
    from utils.pdf_generator import (
        generate_design_specification_pdf,
    )

    project_name = (
        body.plan_data.get("projectName") or "Untitled Project"
    )
    ur_count = sum(
        1 for r in body.requirements if r.get("type") == "UR"
    )
    bundle_count = sum(1 for v in body.test_bundles.values() if v)

    log_audit_event(
        agent_name="ExportsRouter",
        action="DESIGN_SPEC_EXPORT_RECEIVED",
        decision_logic=(
            f"DS export requested for '{project_name}' - "
            f"{ur_count} URs, {bundle_count} bundles, by "
            f"{body.signer_name}"
        ),
    )

    try:
        pdf_bytes = generate_design_specification_pdf(
            plan_data=body.plan_data,
            design_data=body.design_data,
            requirements=body.requirements,
            risk_data=body.risk_data,
            test_bundles=body.test_bundles,
            signer_name=body.signer_name,
            meaning=body.meaning
                or "Approval of Design Specification",
        )
    except Exception as exc:
        log_audit_event(
            agent_name="ExportsRouter",
            action="DESIGN_SPEC_EXPORT_FAILED",
            decision_logic=(
                f"DS export failed for '{project_name}': "
                f"{type(exc).__name__}: {exc}"
            ),
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Design Spec generation failed: {exc}",
        )

    log_audit_event(
        agent_name="ExportsRouter",
        action="DESIGN_SPEC_EXPORT_COMPLETED",
        decision_logic=(
            f"DS exported for '{project_name}' "
            f"({len(pdf_bytes)} bytes) "
            f"signed by {body.signer_name}"
        ),
    )

    return _pdf_response(
        pdf_bytes,
        f"design-specification-{_slug(project_name)}.pdf",
    )


@router.post(
    "/exports/validation-summary-report",
    summary="Generate Validation Summary Report (VSR) PDF",
)
def export_validation_summary_report(
    body: ValidationSummaryRequest,
):
    """Render the Validation Summary Report into a signed PDF.

    Aggregates execution outcomes, defect log, QA review
    attestation, and release approvals into the closing
    Phase-6 evidence artefact.

    :requirement: URS-26.3 - Generate Validation Summary Report
                  PDF with execution outcomes, defects,
                  deviations and approvals.
    """
    from Agents.integrity_manager import log_audit_event
    from utils.pdf_generator import (
        generate_validation_summary_report_pdf,
    )

    project_name = (
        body.plan_data.get("projectName") or "Untitled Project"
    )
    run_count = len(body.test_runs)
    defect_count = sum(
        len(v or []) for v in body.defects.values()
    )
    approval_count = len(
        (body.release_data or {}).get("approvals") or []
    )

    log_audit_event(
        agent_name="ExportsRouter",
        action="VALIDATION_SUMMARY_EXPORT_RECEIVED",
        decision_logic=(
            f"VSR export requested for '{project_name}' - "
            f"{run_count} runs, {defect_count} defects, "
            f"{approval_count} approvals, by {body.signer_name}"
        ),
    )

    try:
        pdf_bytes = generate_validation_summary_report_pdf(
            plan_data=body.plan_data,
            requirements=body.requirements,
            risk_data=body.risk_data,
            test_runs=body.test_runs,
            defects=body.defects,
            qa_reviews=body.qa_reviews,
            release_data=body.release_data,
            signer_name=body.signer_name,
            meaning=body.meaning
                or "Approval of Validation Summary Report",
        )
    except Exception as exc:
        log_audit_event(
            agent_name="ExportsRouter",
            action="VALIDATION_SUMMARY_EXPORT_FAILED",
            decision_logic=(
                f"VSR export failed for '{project_name}': "
                f"{type(exc).__name__}: {exc}"
            ),
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"VSR generation failed: {exc}",
        )

    log_audit_event(
        agent_name="ExportsRouter",
        action="VALIDATION_SUMMARY_EXPORT_COMPLETED",
        decision_logic=(
            f"VSR exported for '{project_name}' "
            f"({len(pdf_bytes)} bytes) "
            f"signed by {body.signer_name}"
        ),
    )

    return _pdf_response(
        pdf_bytes,
        f"validation-summary-report-{_slug(project_name)}.pdf",
    )
