"""
PDF Generators for the EVOLV Engine.

Converts approved URS dictionaries and Validation Reports
into professional PDFs with a Manifestation of Signature
page for 21 CFR Part 11 compliance.

Sprint 18.2 added the Validation Deliverables Pack:
    * generate_validation_plan_pdf()
    * generate_design_specification_pdf()
    * generate_validation_summary_report_pdf()

All three accept the same loose dict shapes the React Zustand
store already serialises (planData, designData, requirements,
riskData, testBundles, testRuns, defects, releaseData).

:requirement: URS-7.3  - Output URS as formatted document.
:requirement: URS-18.1 - Generate combined Validation Report.
:requirement: URS-26.1 - Generate Validation Plan (VP) PDF.
:requirement: URS-26.2 - Generate Design Specification PDF with
                         requirement-to-test traceability matrix.
:requirement: URS-26.3 - Generate Validation Summary Report
                         (VSR) PDF with execution outcomes,
                         defects, deviations, and approvals.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fpdf import FPDF


# ---------------------------------------------------------------
# GAMP 5 category labels (kept in sync with Plan.jsx GAMP_CATEGORIES)
# ---------------------------------------------------------------
GAMP_CATEGORY_LABELS: Dict[str, str] = {
    "1": "Category 1 - Infrastructure Software",
    "3": "Category 3 - Non-Configurable Software",
    "4": "Category 4 - Configurable Software",
    "5": "Category 5 - Custom / Bespoke Software",
}


def _gamp_label(cat: str) -> str:
    """Resolve a GAMP category code to its human label."""
    return GAMP_CATEGORY_LABELS.get(
        str(cat or "").strip(),
        f"Category {cat}" if cat else "Not categorised",
    )


def _safe(text: Any) -> str:
    """Coerce arbitrary input to a Latin-1-safe string.

    fpdf2 core fonts (Helvetica) only support Latin-1. Common
    Unicode characters in our seeded data (em-dash, section sign,
    arrows, check marks) are mapped to ASCII equivalents so they
    render visibly rather than as ``?``.
    """
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "\u2014": "-",       # em dash
        "\u2013": "-",       # en dash
        "\u2018": "'",       # left single quote
        "\u2019": "'",       # right single quote
        "\u201c": '"',       # left double quote
        "\u201d": '"',       # right double quote
        "\u2026": "...",     # ellipsis
        "\u00a7": "Sec.",    # section sign
        "\u00b7": "-",       # middle dot
        "\u2022": "-",       # bullet
        "\u2192": "->",      # right arrow
        "\u2190": "<-",      # left arrow
        "\u2191": "^",       # up arrow
        "\u2193": "v",       # down arrow
        "\u2713": "[x]",     # check mark
        "\u2717": "[ ]",     # ballot x
        "\u26a0": "!",       # warning
        "\u26a1": "*",       # high voltage
        "\u2605": "*",       # star
        "\u00b0": " deg",    # degree sign
    }
    for src, dst in replacements.items():
        s = s.replace(src, dst)
    # Final fallback - strip anything still outside Latin-1.
    return s.encode("latin-1", "replace").decode("latin-1")


# ---------------------------------------------------------------
# Colour palette (matches Streamlit theme)
# ---------------------------------------------------------------
NAVY = (27, 42, 74)
ACCENT = (59, 130, 246)
WHITE = (255, 255, 255)
LIGHT_GREY = (245, 245, 250)
DARK_TEXT = (30, 30, 30)
CRIT_COLOURS = {
    "High": (185, 28, 28),
    "Medium": (146, 64, 14),
    "Low": (6, 95, 70),
}


class _URSPDF(FPDF):
    """Custom FPDF subclass with header/footer branding."""

    def __init__(self, urs_id: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self._urs_id = urs_id

    # -- Page header ------------------------------------------
    def header(self) -> None:
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(10, 4)
        self.cell(
            0, 10, "EVOLV  |  The Validation Factory", align="L",
        )
        self.set_font("Helvetica", "", 9)
        self.set_xy(-60, 4)
        self.cell(
            50, 10, self._urs_id, align="R",
        )
        self.ln(16)

    # -- Page footer ------------------------------------------
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 140)
        self.cell(
            0, 10,
            f"Page {self.page_no()}/{{nb}}  |  "
            f"Generated {datetime.now(timezone.utc):%Y-%m-%d}  |  "
            "Confidential",
            align="C",
        )


def generate_urs_pdf(
    urs: Dict[str, Any],
    signer_name: str,
    meaning: str = "Approval of Requirements",
) -> bytes:
    """
    Generate a two-page PDF from an approved URS dictionary.

    Page 1 contains the formatted URS document.
    Page 2 contains the Manifestation of Signature.

    :param urs: URS dict with keys URS_ID,
        Requirement_Statement, Criticality,
        Regulatory_Rationale, Reg_Versions_Cited.
    :param signer_name: Full name of the approver.
    :param meaning: Meaning of the signature.
    :return: PDF file content as bytes.
    :requirement: URS-7.3 - Output URS as formatted document.
    """
    urs_id: str = urs.get("URS_ID", "URS-UNKNOWN")
    statement: str = urs.get("Requirement_Statement", "")
    criticality: str = urs.get("Criticality", "Medium")
    rationale: str = urs.get("Regulatory_Rationale", "")
    versions: List[str] = urs.get(
        "Reg_Versions_Cited", []
    )
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    pdf = _URSPDF(urs_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ===========================================================
    # Page 1 - URS Document
    # ===========================================================
    pdf.add_page()
    y_start = pdf.get_y() + 4

    # Title
    pdf.set_xy(10, y_start)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 12, "User Requirements Specification",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    # Subtitle line
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        f"{urs_id}  |  Generated: {timestamp}",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    # -- Requirement Statement --------------------------------
    _section_heading(pdf, "Requirement Statement")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, 6, statement, new_x="LMARGIN",
                   new_y="NEXT")
    pdf.ln(6)

    # -- Criticality ------------------------------------------
    _section_heading(pdf, "Criticality")
    crit_colour = CRIT_COLOURS.get(
        criticality, DARK_TEXT
    )
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*crit_colour)
    pdf.cell(
        0, 7, criticality,
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    # -- Regulatory Rationale ---------------------------------
    _section_heading(pdf, "Regulatory Rationale")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    # Rationale may contain " | " delimiters; render
    # each citation as its own paragraph.
    parts = [
        p.strip() for p in rationale.split(" | ") if p.strip()
    ]
    for part in parts:
        pdf.multi_cell(0, 5, part,
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
    if not parts:
        pdf.multi_cell(0, 5, rationale,
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # -- Regulatory Versions Cited ----------------------------
    if versions:
        _section_heading(pdf, "Regulatory Versions Cited")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(
            0, 6, ", ".join(versions),
            new_x="LMARGIN", new_y="NEXT",
        )

    # ===========================================================
    # Page 2 - Manifestation of Signature
    # ===========================================================
    pdf.add_page()
    y_start = pdf.get_y() + 4

    # Title
    pdf.set_xy(10, y_start)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 12, "Manifestation of Signature",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    # Explanatory text
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0, 5,
        "This page constitutes the electronic signature "
        "record for the above User Requirements "
        "Specification in accordance with 21 CFR Part 11. "
        "The signature below indicates that the signer has "
        "reviewed the document and confirms the stated "
        "meaning.",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(8)

    # Signature table
    col_w = [50, 90]
    row_h = 10
    rows = [
        ("Document", urs_id),
        ("Signer Name", signer_name),
        ("Timestamp (UTC)", timestamp),
        ("Meaning", meaning),
    ]

    for label, value in rows:
        # Label cell
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.set_text_color(*NAVY)
        pdf.cell(col_w[0], row_h, f"  {label}",
                 border=1, fill=True)
        # Value cell
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(col_w[1], row_h, f"  {value}",
                 border=1,
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(14)

    # Signature line
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(0, 6, "Signature: "
             + "_" * 50,
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.cell(0, 6, "Date: "
             + "_" * 55,
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(16)

    # Compliance note
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 4,
        "This document was generated by the EVOLV "
        "Engine. Per 21 CFR Part 11, electronic "
        "signatures are the legally binding equivalent of "
        "handwritten signatures. The integrity of this "
        "record is maintained via the system audit trail.",
        new_x="LMARGIN", new_y="NEXT",
    )

    return pdf.output()


def _section_heading(pdf: FPDF, title: str) -> None:
    """Render a coloured section heading with underline."""
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ACCENT)
    pdf.cell(
        0, 8, title,
        new_x="LMARGIN", new_y="NEXT",
    )
    # Thin accent underline
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.4)
    pdf.line(x, y, x + 60, y)
    pdf.ln(3)


# ---------------------------------------------------------------
# Validation Report PDF
# ---------------------------------------------------------------

class _ValidationReportPDF(FPDF):
    """FPDF subclass supporting mixed portrait/landscape pages.

    Uses ``self.w`` instead of hard-coded 210 so that headers
    and footers render correctly on both orientations.
    """

    def __init__(self, doc_id: str) -> None:
        super().__init__(
            orientation="P", unit="mm", format="A4",
        )
        self._doc_id = doc_id

    # -- Page header -------------------------------------------
    def header(self) -> None:
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(10, 4)
        self.cell(
            0, 10, "EVOLV  |  The Validation Factory",
            align="L",
        )
        self.set_font("Helvetica", "", 9)
        self.set_xy(self.w - 70, 4)
        self.cell(50, 10, self._doc_id, align="R")
        self.ln(16)

    # -- Page footer -------------------------------------------
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 140)
        self.cell(
            0, 10,
            f"Page {self.page_no()}/{{nb}}  |  "
            f"Generated "
            f"{datetime.now(timezone.utc):%Y-%m-%d}"
            "  |  Confidential",
            align="C",
        )


def _kv_row(
    pdf: FPDF,
    label: str,
    value: str,
    label_w: float = 55,
) -> None:
    """Render a key-value row in a summary table."""
    row_h = 8
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*LIGHT_GREY)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        label_w, row_h, f"  {label}",
        border=1, fill=True,
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    val_w = pdf.w - pdf.l_margin - pdf.r_margin - label_w
    pdf.cell(
        val_w, row_h, f"  {value}",
        border=1, new_x="LMARGIN", new_y="NEXT",
    )


def _table_page(
    pdf: _ValidationReportPDF,
    heading: str,
    columns: List[str],
    col_widths: List[float],
    rows: List[Tuple[str, ...]],
    meta_line: str = "",
) -> None:
    """Render a landscape table page with header row.

    :requirement: URS-18.3 - Tabular UR/FR and test steps.
    """
    pdf.add_page(orientation="L")
    y = pdf.get_y() + 2

    # Section heading
    pdf.set_xy(10, y)
    _section_heading(pdf, heading)

    if meta_line:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            0, 5, meta_line,
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(2)

    page_w = pdf.w - pdf.l_margin - pdf.r_margin

    # Table header
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 7)
    for i, hdr in enumerate(columns):
        pdf.cell(
            col_widths[i], 7, f" {hdr}",
            border=1, fill=True,
        )
    pdf.ln()

    # Table rows
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_font("Helvetica", "", 7)
    for row in rows:
        # Estimate row height
        max_lines = 1
        cell_texts: List[str] = []
        for idx, val in enumerate(row):
            txt = str(val) if val else ""
            w = col_widths[idx] - 2
            lines = max(
                1,
                int(pdf.get_string_width(txt) / w) + 1
                if w > 0 else 1,
            )
            max_lines = max(max_lines, lines)
            cell_texts.append(txt)
        row_h = max(6, max_lines * 5)
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        if y_start + row_h > pdf.h - 15:
            pdf.add_page(orientation="L")
            # Re-draw column headers on new page
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 7)
            for i, hdr in enumerate(columns):
                pdf.cell(
                    col_widths[i], 7, f" {hdr}",
                    border=1, fill=True,
                )
            pdf.ln()
            pdf.set_text_color(*DARK_TEXT)
            pdf.set_font("Helvetica", "", 7)
            x_start = pdf.get_x()
            y_start = pdf.get_y()
        for ci, txt in enumerate(cell_texts):
            pdf.set_xy(
                x_start + sum(col_widths[:ci]),
                y_start,
            )
            pdf.multi_cell(
                col_widths[ci], 5, txt, border=1,
            )
        pdf.set_xy(
            x_start,
            max(pdf.get_y(), y_start + row_h),
        )


def generate_validation_report_pdf(
    ur_fr: Dict[str, Any],
    test_script: Dict[str, Any],
    signer_name: str,
    meaning: str = "Approval of Validation Report",
) -> bytes:
    """Generate a combined Validation Report PDF.

    Merges the UR/FR document and CSA test script into a
    single professional PDF with portrait cover/signature
    pages and landscape table pages.

    :param ur_fr: UR/FR dict from RequirementArchitect.
    :param test_script: Test script dict from DeltaAgent.
    :param signer_name: Full name of the approver.
    :param meaning: Meaning of the electronic signature.
    :return: PDF file content as bytes.
    :requirement: URS-18.1 - Generate combined Validation
        Report PDF.
    """
    urs_id = ur_fr.get("urs_id", "URS-UNKNOWN")
    ur = ur_fr.get("user_requirement", {})
    frs = ur_fr.get("functional_requirements", [])
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds",
    )

    doc_id = f"VR-{urs_id}"
    pdf = _ValidationReportPDF(doc_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # Page 1 - Cover (Portrait)
    # =========================================================
    pdf.add_page(orientation="P")
    y = pdf.get_y() + 4

    # Title
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 14, "Validation Report",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    # Subtitle
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        f"{doc_id}  |  {urs_id}  |  "
        f"Generated: {timestamp}",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(8)

    # Summary table
    _section_heading(pdf, "Summary")
    _kv_row(pdf, "URS ID", urs_id)
    _kv_row(
        pdf, "Category",
        ur_fr.get("category", "-"),
    )
    _kv_row(
        pdf, "Risk Assessment",
        ur.get("risk_assessment", "-"),
    )
    _kv_row(
        pdf, "Implementation",
        ur.get("implementation_method", "-"),
    )

    # Risk level with colour
    risk_lvl = ur.get("risk_level", "-")
    _kv_row(pdf, "Risk Level", risk_lvl)

    _kv_row(
        pdf, "Test Strategy",
        ur.get("test_strategy", "-"),
    )
    _kv_row(
        pdf, "Script ID",
        test_script.get("script_id", "-"),
    )
    _kv_row(
        pdf, "Test Type",
        test_script.get("test_type", "-"),
    )
    pdf.ln(6)

    # Requirement summary
    _section_heading(pdf, "Requirement Summary")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(
        0, 5,
        ur_fr.get("requirement_summary", ""),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    # Assumptions & Dependencies
    assumptions = ur_fr.get(
        "assumptions_and_dependencies", [],
    )
    if assumptions:
        _section_heading(
            pdf, "Assumptions & Dependencies",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        for a in assumptions:
            pdf.multi_cell(
                0, 5, f"  - {a}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(4)

    # Compliance notes
    notes = ur_fr.get("compliance_notes", [])
    if notes:
        _section_heading(pdf, "Compliance Notes")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        for n in notes:
            pdf.multi_cell(
                0, 5, f"  - {n}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(4)

    # Reg versions
    reg_vers = ur_fr.get("reg_versions_cited", [])
    if reg_vers:
        _section_heading(
            pdf, "Regulatory Versions Cited",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(
            0, 6, ", ".join(reg_vers),
            new_x="LMARGIN", new_y="NEXT",
        )

    # =========================================================
    # Page 2 - UR/FR Table (Landscape)
    # =========================================================
    ur_cols = [
        "FR ID", "Parent UR", "Statement",
        "Acceptance Criteria",
    ]
    # Landscape usable ~277mm
    ur_col_w = [22, 22, 115, 118]

    ur_rows: List[Tuple[str, ...]] = []
    for fr in frs:
        ac = fr.get("acceptance_criteria", [])
        ur_rows.append((
            fr.get("fr_id", ""),
            fr.get("parent_ur_id", ""),
            fr.get("statement", ""),
            "; ".join(ac) if isinstance(ac, list) else
            str(ac),
        ))

    ur_meta = (
        f"UR: {ur.get('ur_id', '-')}  |  "
        f"Statement: {ur.get('statement', '-')[:80]}...  |  "
        f"Risk: {risk_lvl}  |  "
        f"Strategy: {ur.get('test_strategy', '-')}"
    )
    _table_page(
        pdf, "User & Functional Requirements",
        ur_cols, ur_col_w, ur_rows, ur_meta,
    )

    # =========================================================
    # Page 3 - Test Script Table (Landscape)
    # =========================================================
    ts_cols = [
        "Type", "#", "Title", "Instruction",
        "Expected Result", "Case", "Ref",
    ]
    ts_col_w = [22, 10, 45, 75, 65, 30, 30]

    steps = test_script.get("steps", [])
    ts_rows: List[Tuple[str, ...]] = []
    for s in steps:
        ts_rows.append((
            s.get("step_type", ""),
            str(s.get("step_number", "")),
            s.get("step_title", ""),
            s.get("step_instruction", ""),
            s.get("expected_result", ""),
            s.get("test_case_type", ""),
            s.get("requirement_reference", ""),
        ))

    ts_meta = (
        f"Script: "
        f"{test_script.get('script_id', '-')}  |  "
        f"Risk: "
        f"{test_script.get('risk_level', '-')}  |  "
        f"Type: "
        f"{test_script.get('test_type', '-')}"
    )
    _table_page(
        pdf, "CSA Test Script",
        ts_cols, ts_col_w, ts_rows, ts_meta,
    )

    # =========================================================
    # Page 4 - Regulatory Justification (Portrait)
    # =========================================================
    just_text = test_script.get(
        "regulatory_justification", "",
    )
    if just_text:
        pdf.add_page(orientation="P")
        y = pdf.get_y() + 4
        pdf.set_xy(10, y)
        _section_heading(
            pdf, "Regulatory Justification",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(
            0, 5, just_text,
            new_x="LMARGIN", new_y="NEXT",
        )

    # =========================================================
    # Page 5 - Manifestation of Signature (Portrait)
    # =========================================================
    pdf.add_page(orientation="P")
    y = pdf.get_y() + 4

    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 12, "Manifestation of Signature",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    # Explanatory text
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0, 5,
        "This page constitutes the electronic signature "
        "record for the above Validation Report in "
        "accordance with 21 CFR Part 11. The signature "
        "below indicates that the signer has reviewed "
        "the document and confirms the stated meaning.",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(8)

    # Signature table
    col_w = [50, 90]
    row_h = 10
    sig_rows = [
        ("Document", doc_id),
        ("Signer Name", signer_name),
        ("Timestamp (UTC)", timestamp),
        ("Meaning", meaning),
    ]
    for label, value in sig_rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.set_text_color(*NAVY)
        pdf.cell(
            col_w[0], row_h, f"  {label}",
            border=1, fill=True,
        )
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(
            col_w[1], row_h, f"  {value}",
            border=1,
            new_x="LMARGIN", new_y="NEXT",
        )
    pdf.ln(14)

    # Signature line
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(
        0, 6,
        "Signature: " + "_" * 50,
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)
    pdf.cell(
        0, 6,
        "Date: " + "_" * 55,
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(16)

    # Compliance note
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 4,
        "This document was generated by the EVOLV "
        "Engine. Per 21 CFR Part 11, electronic "
        "signatures are the legally binding equivalent "
        "of handwritten signatures. The integrity of "
        "this record is maintained via the system "
        "audit trail.",
        new_x="LMARGIN", new_y="NEXT",
    )

    return pdf.output()


# ===============================================================
# Sprint 18.2 - Validation Deliverables Pack
# ===============================================================
#
# Three generators sharing the _ValidationReportPDF chrome (NAVY
# header, orientation-aware, branded footer). All three end with
# a Manifestation of Signature page emitted by _mos_page_navy().
# ---------------------------------------------------------------


def _mos_page_navy(
    pdf: _ValidationReportPDF,
    doc_id: str,
    doc_kind: str,
    signer_name: str,
    meaning: str,
    timestamp: str,
    extra_note: str = "",
) -> None:
    """Render a Manifestation of Signature page (21 CFR Part 11
    Sec. 11.50) consistent with the existing URS / Validation
    Report style.

    :param pdf: orientation-aware FPDF subclass instance.
    :param doc_id: short id printed in the signature table
        (e.g. ``"VP-LabCore"``).
    :param doc_kind: human label printed in the title and
        explanatory paragraph (e.g. ``"Validation Plan"``).
    :param signer_name: full name of the approver.
    :param meaning: meaning of the signature.
    :param timestamp: ISO-8601 timestamp string for the table.
    :param extra_note: optional italic footnote rendered after
        the boilerplate compliance text.
    :requirement: URS-26.4 - Manifestation of Signature page
                  shall be appended to every Validation
                  Deliverables Pack PDF.
    """
    pdf.add_page(orientation="P")
    y = pdf.get_y() + 4
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 12, "Manifestation of Signature",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0, 5,
        _safe(
            f"This page constitutes the electronic signature "
            f"record for the above {doc_kind} in accordance "
            f"with 21 CFR Part 11. The signature below "
            f"indicates that the signer has reviewed the "
            f"document and confirms the stated meaning."
        ),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(8)

    col_w = [50, 90]
    row_h = 10
    rows = [
        ("Document",        doc_id),
        ("Document Kind",   doc_kind),
        ("Signer Name",     signer_name),
        ("Timestamp (UTC)", timestamp),
        ("Meaning",         meaning),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.set_text_color(*NAVY)
        pdf.cell(
            col_w[0], row_h, f"  {_safe(label)}",
            border=1, fill=True,
        )
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(
            col_w[1], row_h, f"  {_safe(value)}",
            border=1,
            new_x="LMARGIN", new_y="NEXT",
        )

    pdf.ln(14)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(
        0, 6, "Signature: " + "_" * 50,
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)
    pdf.cell(
        0, 6, "Date: " + "_" * 55,
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(14)

    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 4,
        _safe(
            "This document was generated by the EVOLV Engine. "
            "Per 21 CFR Part 11, electronic signatures are the "
            "legally binding equivalent of handwritten "
            "signatures. The integrity of this record is "
            "maintained via the system audit trail."
        ),
        new_x="LMARGIN", new_y="NEXT",
    )
    if extra_note:
        pdf.ln(2)
        pdf.multi_cell(
            0, 4, _safe(extra_note),
            new_x="LMARGIN", new_y="NEXT",
        )


def _bullet_block(
    pdf: _ValidationReportPDF,
    items: Iterable[str],
    indent: float = 4,
) -> None:
    """Render a list of items as ``- item`` bullets."""
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for item in items:
        pdf.set_x(pdf.l_margin + indent)
        pdf.multi_cell(
            0, 5, _safe(f"- {item}"),
            new_x="LMARGIN", new_y="NEXT",
        )


def _para(
    pdf: _ValidationReportPDF,
    text: str,
    size: int = 9,
    color: Tuple[int, int, int] = DARK_TEXT,
    italic: bool = False,
) -> None:
    """Render a flowing paragraph using multi_cell."""
    style = "I" if italic else ""
    pdf.set_font("Helvetica", style, size)
    pdf.set_text_color(*color)
    pdf.multi_cell(
        0, 5, _safe(text or "-"),
        new_x="LMARGIN", new_y="NEXT",
    )


# ---------------------------------------------------------------
# 1. Validation Plan PDF
# ---------------------------------------------------------------

def generate_validation_plan_pdf(
    plan_data: Dict[str, Any],
    signer_name: str,
    meaning: str = "Approval of Validation Plan",
) -> bytes:
    """Generate a Validation Plan (VP) PDF.

    The Validation Plan is the gating Phase-1 deliverable. It
    captures project scope, GAMP 5 category, applicable
    regulatory frameworks, and the Validation Master Plan
    (validation strategy, resources, timeline).

    :param plan_data: Plan slice from the React Zustand store.
        Expected keys: ``projectName``, ``gampCategory``,
        ``systemDescription``, ``projectScope``,
        ``regulatoryFrameworks`` (List[str]),
        ``vmpContent`` (Dict with ``validationStrategy``,
        ``resourcesResponsibilities``, ``timeline``).
    :param signer_name: full name of the QA approver.
    :param meaning: meaning of the electronic signature.
    :return: PDF bytes.
    :requirement: URS-26.1 - Generate Validation Plan PDF.
    """
    project_name = plan_data.get("projectName") or "Untitled Project"
    cat = str(plan_data.get("gampCategory") or "")
    cat_label = _gamp_label(cat)
    system_desc = plan_data.get("systemDescription") or ""
    scope = plan_data.get("projectScope") or ""
    frameworks: List[str] = list(
        plan_data.get("regulatoryFrameworks") or []
    )
    vmp = dict(plan_data.get("vmpContent") or {})
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds",
    )
    safe_slug = "".join(
        c if c.isalnum() else "-" for c in project_name
    )[:32].strip("-") or "project"
    doc_id = f"VP-{safe_slug}"

    pdf = _ValidationReportPDF(doc_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # Page 1 - Cover
    # =========================================================
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 14, "Validation Plan",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(
            f"{doc_id}  |  {project_name}  |  "
            f"Generated: {timestamp}"
        ),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    _section_heading(pdf, "Project Identification")
    _kv_row(pdf, "Project Name",     project_name)
    _kv_row(pdf, "GAMP 5 Category",  cat_label)
    _kv_row(
        pdf, "Frameworks",
        ", ".join(frameworks) if frameworks else "Not specified",
    )
    pdf.ln(4)

    _section_heading(pdf, "System Description")
    _para(pdf, system_desc)
    pdf.ln(2)

    _section_heading(pdf, "Project Scope")
    _para(pdf, scope)
    pdf.ln(2)

    # =========================================================
    # Page 2 - Validation Master Plan
    # =========================================================
    pdf.add_page(orientation="P")
    _section_heading(pdf, "Validation Strategy")
    _para(
        pdf,
        vmp.get("validationStrategy")
        or "Validation strategy has not been documented yet.",
    )
    pdf.ln(2)

    _section_heading(pdf, "Resources & Responsibilities")
    _para(
        pdf,
        vmp.get("resourcesResponsibilities")
        or "Roles & responsibilities have not been documented yet.",
    )
    pdf.ln(2)

    _section_heading(pdf, "Timeline & Milestones")
    _para(
        pdf,
        vmp.get("timeline")
        or "Timeline has not been documented yet.",
    )
    pdf.ln(2)

    _section_heading(pdf, "Regulatory Frameworks Applied")
    if frameworks:
        _bullet_block(pdf, frameworks)
    else:
        _para(
            pdf,
            "No frameworks selected. Plan is incomplete.",
            italic=True,
            color=(120, 120, 120),
        )

    # =========================================================
    # Manifestation of Signature
    # =========================================================
    _mos_page_navy(
        pdf,
        doc_id=doc_id,
        doc_kind="Validation Plan",
        signer_name=signer_name,
        meaning=meaning,
        timestamp=timestamp,
        extra_note=(
            "This Validation Plan is the controlling document "
            "for the project. Subsequent deliverables (Design "
            "Specification, Test Scripts, Validation Summary "
            "Report) shall trace back to the scope, "
            "frameworks, and strategy approved here."
        ),
    )

    return pdf.output()


# ---------------------------------------------------------------
# 2. Design Specification PDF
# ---------------------------------------------------------------

def _build_traceability_rows(
    requirements: List[Dict[str, Any]],
    risk_data: Dict[str, Dict[str, Any]],
    test_bundles: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, ...]]:
    """Compose UR-keyed rows for the Design traceability table.

    Columns: UR ID | UR Statement | FR IDs | Risk Level
        | Test Strategy | Bundle ID | # Steps | Coverage
    """
    # Group FRs under their parent UR.
    frs_by_ur: Dict[str, List[Dict[str, Any]]] = {}
    for r in requirements:
        if r.get("type") == "FR":
            parent = r.get("parentId") or ""
            frs_by_ur.setdefault(parent, []).append(r)

    rows: List[Tuple[str, ...]] = []
    for ur in [r for r in requirements if r.get("type") == "UR"]:
        ur_id = ur.get("id", "")
        frs = frs_by_ur.get(ur_id, [])
        risk = risk_data.get(ur_id) or {}
        bundle = test_bundles.get(ur_id) or {}
        steps = bundle.get("steps") or []
        rows.append((
            ur_id,
            ur.get("statement", ""),
            ", ".join(f.get("id", "") for f in frs) or "-",
            risk.get("riskLevel") or "-",
            risk.get("testAssurance") or "-",
            bundle.get("bundle_id") or "-",
            str(len(steps)) if steps else "0",
            "Covered" if bundle else "GAP",
        ))
    return rows


def generate_design_specification_pdf(
    plan_data: Dict[str, Any],
    design_data: Dict[str, Any],
    requirements: List[Dict[str, Any]],
    risk_data: Dict[str, Dict[str, Any]],
    test_bundles: Dict[str, Dict[str, Any]],
    signer_name: str,
    meaning: str = "Approval of Design Specification",
) -> bytes:
    """Generate a Design Specification PDF.

    Renders architecture / HLD / LLD / integration notes from
    the React designData slice, the configuration items table,
    and a traceability matrix linking each UR to its FRs, risk
    rating, and authored test bundle.

    :param plan_data: Plan slice (used for project name + GAMP
        category context).
    :param design_data: Design slice with architectureNotes,
        hldNotes, lldNotes, integrationNotes, diagramUrl, and
        configItems list.
    :param requirements: Flat list of UR + FR dicts (matches
        useAppStore ``requirements`` slice).
    :param risk_data: Map ``{ur_id: {impact, implMethod,
        riskLevel, testAssurance}}``.
    :param test_bundles: Map ``{ur_id: bundle_dict}`` from the
        Test Authoring engine.
    :param signer_name: full name of the QA / Validation Lead.
    :param meaning: meaning of the electronic signature.
    :return: PDF bytes.
    :requirement: URS-26.2 - Generate Design Specification PDF
                  with requirement-to-test traceability matrix.
    """
    project_name = plan_data.get("projectName") or "Untitled Project"
    cat = str(plan_data.get("gampCategory") or "")
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds",
    )
    safe_slug = "".join(
        c if c.isalnum() else "-" for c in project_name
    )[:32].strip("-") or "project"
    doc_id = f"DS-{safe_slug}"

    pdf = _ValidationReportPDF(doc_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # Page 1 - Cover
    # =========================================================
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 14, "Design Specification",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(
            f"{doc_id}  |  {project_name}  |  "
            f"Generated: {timestamp}"
        ),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    ur_count = sum(
        1 for r in requirements if r.get("type") == "UR"
    )
    fr_count = sum(
        1 for r in requirements if r.get("type") == "FR"
    )
    bundle_count = sum(
        1 for v in test_bundles.values() if v
    )
    config_items = list(design_data.get("configItems") or [])

    _section_heading(pdf, "Summary")
    _kv_row(pdf, "Project",          project_name)
    _kv_row(pdf, "GAMP 5 Category",  _gamp_label(cat))
    _kv_row(pdf, "Requirements",
            f"{ur_count} URs / {fr_count} FRs")
    _kv_row(pdf, "Test Bundles",     str(bundle_count))
    _kv_row(pdf, "Configuration Items",
            str(len(config_items)))
    diagram = design_data.get("diagramUrl") or ""
    if diagram:
        _kv_row(pdf, "Diagram", diagram)
    pdf.ln(4)

    _section_heading(pdf, "System Architecture Notes")
    _para(pdf, design_data.get("architectureNotes") or "")
    pdf.ln(2)

    _section_heading(pdf, "High-Level Design")
    _para(pdf, design_data.get("hldNotes") or "")
    pdf.ln(2)

    if cat == "5" and (design_data.get("lldNotes") or "").strip():
        _section_heading(
            pdf, "Low-Level Design (Cat 5 only)",
        )
        _para(pdf, design_data.get("lldNotes") or "")
        pdf.ln(2)

    _section_heading(pdf, "Interface / Integration Notes")
    _para(pdf, design_data.get("integrationNotes") or "")

    # =========================================================
    # Page 2 - Configuration Items Table (Landscape)
    # =========================================================
    if config_items:
        cfg_cols = [
            "Item", "System", "Parameter",
            "Value", "Rationale",
        ]
        cfg_col_w = [40, 35, 60, 30, 112]
        cfg_rows = [
            (
                _safe(c.get("item", "")),
                _safe(c.get("system", "")),
                _safe(c.get("parameter", "")),
                _safe(c.get("value", "")),
                _safe(c.get("rationale", "")),
            )
            for c in config_items
        ]
        _table_page(
            pdf, "Configuration Items",
            cfg_cols, cfg_col_w, cfg_rows,
            f"{len(config_items)} configured parameters "
            "subject to change-control.",
        )

    # =========================================================
    # Page 3 - Traceability Matrix (Landscape)
    # =========================================================
    trace_cols = [
        "UR ID", "UR Statement", "FR IDs", "Risk",
        "Strategy", "Bundle ID", "Steps", "Coverage",
    ]
    trace_col_w = [18, 95, 32, 18, 24, 30, 14, 22]
    trace_rows = _build_traceability_rows(
        requirements, risk_data, test_bundles,
    )
    if trace_rows:
        gaps = sum(1 for r in trace_rows if r[-1] == "GAP")
        meta = (
            f"{len(trace_rows)} URs total. "
            f"{len(trace_rows) - gaps} covered, "
            f"{gaps} gap{'s' if gaps != 1 else ''}."
        )
        _table_page(
            pdf, "Traceability Matrix (UR -> FR -> Test Bundle)",
            trace_cols, trace_col_w, trace_rows, meta,
        )
    else:
        pdf.add_page(orientation="P")
        _section_heading(pdf, "Traceability Matrix")
        _para(
            pdf,
            "No requirements have been authored yet. "
            "Complete the Requirements phase before "
            "approving the Design Specification.",
            italic=True,
            color=(120, 120, 120),
        )

    # =========================================================
    # Manifestation of Signature
    # =========================================================
    _mos_page_navy(
        pdf,
        doc_id=doc_id,
        doc_kind="Design Specification",
        signer_name=signer_name,
        meaning=meaning,
        timestamp=timestamp,
        extra_note=(
            "Coverage status reflects the state of the test "
            "authoring engine at the time of generation. Any "
            "UR flagged GAP must be remediated (or formally "
            "deferred) before the Design phase can be marked "
            "complete per the GxP-Direct coverage gate."
        ),
    )

    return pdf.output()


# ---------------------------------------------------------------
# 3. Validation Summary Report PDF
# ---------------------------------------------------------------

def _summarise_runs(
    test_runs: Dict[str, Dict[str, Any]],
) -> Dict[str, int]:
    """Aggregate pass/fail/blocked/na counts across all runs."""
    totals = {
        "runs": 0, "locked": 0,
        "pass": 0, "fail": 0,
        "blocked": 0, "na": 0,
        "steps": 0,
    }
    for run in test_runs.values():
        if not isinstance(run, dict):
            continue
        totals["runs"] += 1
        if run.get("status") == "locked":
            totals["locked"] += 1
        results = run.get("stepResults") or {}
        for entry in results.values():
            # The React store stores stepResults as a flat
            # ``{stepKey: 'pass' | 'fail' | ...}`` map, but legacy
            # callers may pass full ``{stepKey: {verdict: ...}}``
            # dicts. Accept both for defensive robustness.
            if isinstance(entry, dict):
                verdict = (entry.get("verdict") or "").upper()
            else:
                verdict = str(entry or "").upper()
            totals["steps"] += 1
            if verdict == "PASS":
                totals["pass"] += 1
            elif verdict == "FAIL":
                totals["fail"] += 1
            elif verdict == "BLOCKED":
                totals["blocked"] += 1
            elif verdict in ("N/A", "NA"):
                totals["na"] += 1
    return totals


def _flatten_defects(
    defects: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Flatten the per-script defect map into a single ordered
    list, preserving script_id context for the table."""
    out: List[Dict[str, Any]] = []
    for script_id, items in (defects or {}).items():
        for d in items or []:
            row = dict(d)
            row.setdefault("script_id", script_id)
            out.append(row)
    return out


def generate_validation_summary_report_pdf(
    plan_data: Dict[str, Any],
    requirements: List[Dict[str, Any]],
    risk_data: Dict[str, Dict[str, Any]],
    test_runs: Dict[str, Dict[str, Any]],
    defects: Dict[str, List[Dict[str, Any]]],
    qa_reviews: Dict[str, Dict[str, Any]],
    release_data: Dict[str, Any],
    signer_name: str,
    meaning: str = "Approval of Validation Summary Report",
) -> bytes:
    """Generate the Validation Summary Report (VSR) PDF.

    The VSR is the closing Phase-6 deliverable. It summarises
    every test execution outcome, defect, QA review, deviation
    and release approval into a single signed artefact suitable
    for inclusion in the validation evidence binder.

    :param plan_data: Plan slice (project name, GAMP cat,
        frameworks).
    :param requirements: Flat UR/FR list.
    :param risk_data: Per-UR risk map.
    :param test_runs: Map ``{run_id: run_dict}`` from the
        Verify phase.
    :param defects: Map ``{script_id: List[defect_dict]}``.
    :param qa_reviews: Map ``{run_id: review_dict}`` from the
        QA Review panel.
    :param release_data: Release slice with ``approvals``
        list, ``released`` flag, ``releasedAt`` timestamp.
    :param signer_name: full name of the QA Director / Head.
    :param meaning: meaning of the electronic signature.
    :return: PDF bytes.
    :requirement: URS-26.3 - Generate Validation Summary Report
                  PDF with execution outcomes, defects,
                  deviations and approvals.
    """
    project_name = plan_data.get("projectName") or "Untitled Project"
    cat = str(plan_data.get("gampCategory") or "")
    frameworks: List[str] = list(
        plan_data.get("regulatoryFrameworks") or []
    )
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds",
    )
    safe_slug = "".join(
        c if c.isalnum() else "-" for c in project_name
    )[:32].strip("-") or "project"
    doc_id = f"VSR-{safe_slug}"

    totals = _summarise_runs(test_runs)
    defect_rows = _flatten_defects(defects)
    approvals: List[Dict[str, Any]] = list(
        release_data.get("approvals") or []
    )
    released = bool(release_data.get("released"))
    released_at = release_data.get("releasedAt") or "-"

    # Risk distribution
    risk_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in risk_data.values():
        lvl = (r or {}).get("riskLevel", "").upper()
        if lvl in risk_dist:
            risk_dist[lvl] += 1

    pdf = _ValidationReportPDF(doc_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # Page 1 - Cover & headline outcome
    # =========================================================
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 14, "Validation Summary Report",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(
            f"{doc_id}  |  {project_name}  |  "
            f"Generated: {timestamp}"
        ),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    _section_heading(pdf, "Project Identification")
    _kv_row(pdf, "Project",          project_name)
    _kv_row(pdf, "GAMP 5 Category",  _gamp_label(cat))
    _kv_row(
        pdf, "Frameworks",
        ", ".join(frameworks) if frameworks else "Not specified",
    )
    _kv_row(
        pdf, "Release Status",
        "RELEASED" if released else "Not released",
    )
    _kv_row(pdf, "Released At", released_at)
    pdf.ln(2)

    # Headline verdict banner
    verdict = "PASS" if (
        released
        and totals["fail"] == 0
        and totals["blocked"] == 0
    ) else (
        "FAIL" if totals["fail"] else
        ("BLOCKED" if totals["blocked"] else "INCOMPLETE")
    )
    verdict_color = {
        "PASS":       (6, 95, 70),
        "FAIL":       (185, 28, 28),
        "BLOCKED":    (146, 64, 14),
        "INCOMPLETE": (100, 100, 100),
    }[verdict]
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*verdict_color)
    pdf.cell(
        0, 12, _safe(f"Overall Verdict: {verdict}"),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    _section_heading(pdf, "Execution Statistics")
    _kv_row(pdf, "Test Runs",        str(totals["runs"]))
    _kv_row(pdf, "Locked / Signed",  str(totals["locked"]))
    _kv_row(pdf, "Total Steps",      str(totals["steps"]))
    _kv_row(pdf, "Pass",             str(totals["pass"]))
    _kv_row(pdf, "Fail",             str(totals["fail"]))
    _kv_row(pdf, "Blocked",          str(totals["blocked"]))
    _kv_row(pdf, "N/A",              str(totals["na"]))
    pdf.ln(2)

    _section_heading(pdf, "Risk Distribution")
    _kv_row(pdf, "HIGH risk URs",    str(risk_dist["HIGH"]))
    _kv_row(pdf, "MEDIUM risk URs",  str(risk_dist["MEDIUM"]))
    _kv_row(pdf, "LOW risk URs",     str(risk_dist["LOW"]))

    # =========================================================
    # Page 2 - Per-run summary (Landscape)
    # =========================================================
    if test_runs:
        run_cols = [
            "Run ID", "Script ID", "Status",
            "Pass", "Fail", "Blocked", "Started", "Locked",
        ]
        run_col_w = [30, 35, 22, 14, 14, 18, 50, 94]
        run_rows: List[Tuple[str, ...]] = []

        def _verdict_of(v: Any) -> str:
            """Accept both flat string and dict step-result shapes."""
            if isinstance(v, dict):
                return (v.get("verdict") or "").upper()
            return str(v or "").upper()

        for run_id, run in test_runs.items():
            if not isinstance(run, dict):
                continue
            results = run.get("stepResults") or {}
            p = sum(
                1 for v in results.values()
                if _verdict_of(v) == "PASS"
            )
            f = sum(
                1 for v in results.values()
                if _verdict_of(v) == "FAIL"
            )
            b = sum(
                1 for v in results.values()
                if _verdict_of(v) == "BLOCKED"
            )
            run_rows.append((
                _safe(run_id),
                _safe(run.get("scriptId") or "-"),
                _safe(run.get("status") or "-"),
                str(p), str(f), str(b),
                _safe(run.get("startedAt") or "-"),
                _safe(run.get("lockedAt") or "-"),
            ))
        _table_page(
            pdf, "Test Run Outcomes",
            run_cols, run_col_w, run_rows,
            f"{totals['runs']} run(s); "
            f"{totals['locked']} locked & signed.",
        )
    else:
        pdf.add_page(orientation="P")
        _section_heading(pdf, "Test Run Outcomes")
        _para(
            pdf,
            "No test runs have been initiated. The Verify "
            "phase has not started or has been reset.",
            italic=True,
            color=(120, 120, 120),
        )

    # =========================================================
    # Page 3 - Defect Log (Landscape)
    # =========================================================
    if defect_rows:
        def_cols = [
            "Defect ID", "Script", "Severity",
            "Status", "Title", "Assignee",
            "Fix Date", "FR Ref",
        ]
        def_col_w = [22, 25, 18, 18, 90, 30, 24, 50]
        def_table: List[Tuple[str, ...]] = []
        sev_count = {"Critical": 0, "Major": 0, "Minor": 0}
        for d in defect_rows:
            sev = d.get("severity") or ""
            if sev in sev_count:
                sev_count[sev] += 1
            def_table.append((
                _safe(d.get("defectId") or d.get("id") or "-"),
                _safe(d.get("script_id") or "-"),
                _safe(sev or "-"),
                _safe(d.get("status") or "Open"),
                _safe(d.get("title") or d.get("description") or "-"),
                _safe(d.get("assignee") or "-"),
                _safe(d.get("fixDate") or "-"),
                _safe(d.get("frRef") or "-"),
            ))
        meta = (
            f"{len(defect_rows)} defect(s): "
            f"{sev_count['Critical']} Critical, "
            f"{sev_count['Major']} Major, "
            f"{sev_count['Minor']} Minor."
        )
        _table_page(
            pdf, "Defect Log",
            def_cols, def_col_w, def_table, meta,
        )
    else:
        pdf.add_page(orientation="P")
        _section_heading(pdf, "Defect Log")
        _para(
            pdf,
            "No defects were raised during validation "
            "execution.",
        )

    # =========================================================
    # Page 4 - QA Review attestation
    # =========================================================
    pdf.add_page(orientation="P")
    _section_heading(pdf, "Independent QA Review")
    if qa_reviews:
        for run_id, rv in qa_reviews.items():
            rv = rv or {}
            checks = rv.get("checks") or {}
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(
                0, 6,
                _safe(f"Run: {run_id}"),
                new_x="LMARGIN", new_y="NEXT",
            )
            checklist_items = [
                ("Actual results recorded for failed/blocked "
                 "steps",         checks.get("actualResults")),
                ("Defects logged for every fail",
                 checks.get("defectsLogged")),
                ("Evidence attached where required",
                 checks.get("evidenceAttached")),
                ("Adhoc steps justified",
                 checks.get("adhocJustified")),
            ]
            for label, val in checklist_items:
                mark = "[x]" if val else "[ ]"
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*DARK_TEXT)
                pdf.multi_cell(
                    0, 5,
                    _safe(f"  {mark}  {label}"),
                    new_x="LMARGIN", new_y="NEXT",
                )
            comments = rv.get("comments") or ""
            if comments:
                pdf.ln(1)
                _para(
                    pdf,
                    f"Reviewer comments: {comments}",
                    italic=True,
                    color=(80, 80, 80),
                )
            signed = rv.get("signedAt")
            reviewer = rv.get("reviewer") or "-"
            if signed:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(6, 95, 70)
                pdf.multi_cell(
                    0, 5,
                    _safe(
                        f"Signed by {reviewer} at {signed}."
                    ),
                    new_x="LMARGIN", new_y="NEXT",
                )
            else:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(146, 64, 14)
                pdf.multi_cell(
                    0, 5,
                    _safe("QA review not yet signed."),
                    new_x="LMARGIN", new_y="NEXT",
                )
            pdf.ln(3)
    else:
        _para(
            pdf,
            "No QA reviews have been recorded. Per 21 CFR "
            "Part 11 Sec. 11.10(b) an independent attestation "
            "is recommended before release.",
            italic=True,
            color=(120, 120, 120),
        )

    # =========================================================
    # Page 5 - Release Approvals (Landscape)
    # =========================================================
    if approvals:
        ap_cols = [
            "#", "Name", "Role", "Meaning",
            "Signed At (UTC)", "Reasoning Hash",
        ]
        ap_col_w = [10, 50, 35, 50, 50, 82]
        ap_rows: List[Tuple[str, ...]] = []
        for i, a in enumerate(approvals, start=1):
            ap_rows.append((
                str(i),
                _safe(a.get("name") or "-"),
                _safe(a.get("role") or "-"),
                _safe(a.get("meaning") or "-"),
                _safe(a.get("signedAt") or "-"),
                _safe(
                    (a.get("reasoningHash") or "-")[:32]
                ),
            ))
        _table_page(
            pdf, "Release Approvals",
            ap_cols, ap_col_w, ap_rows,
            f"{len(approvals)} approval(s) on file.",
        )
    else:
        pdf.add_page(orientation="P")
        _section_heading(pdf, "Release Approvals")
        _para(
            pdf,
            "No release approvals on file. The system has "
            "not been authorised for go-live.",
            italic=True,
            color=(146, 64, 14),
        )

    # =========================================================
    # Manifestation of Signature
    # =========================================================
    _mos_page_navy(
        pdf,
        doc_id=doc_id,
        doc_kind="Validation Summary Report",
        signer_name=signer_name,
        meaning=meaning,
        timestamp=timestamp,
        extra_note=(
            "Together with the underlying test execution "
            "records, defect log, and release approvals, this "
            "Validation Summary Report constitutes the closing "
            "evidence required for the validation binder."
        ),
    )

    return pdf.output()


# ---------------------------------------------------------------
# Sprint 19 - Audit Trail Inspection Export PDF
# ---------------------------------------------------------------

def generate_audit_export_pdf(
    rows: List[Dict[str, Any]],
    project_name: str,
    signer_name: str,
    meaning: str = "Audit Trail Inspection Export",
    filter_summary: str = "",
) -> bytes:
    """Render a filtered slice of the audit trail as a signed PDF.

    Layout:

    - **Page 1 (portrait):** Cover with project name, generation
      timestamp, applied filter summary, row count, and a
      phase-breakdown summary table.
    - **Pages 2-N (landscape):** Tabular dump of every row with
      Timestamp / Phase / Agent / Action / Hash / Logic columns.
    - **Final page (portrait):** Manifestation of Signature
      (21 CFR Part 11 Sec. 11.50).

    Each row dict is expected to be the shape returned by
    ``GET /audit/all``: keys ``timestamp``, ``user_id``,
    ``agent_name``, ``action``, ``decision_logic``,
    ``compliance_impact``, ``reasoning_hash``, ``severity``,
    ``phase``. Missing keys are tolerated.

    :param rows: filtered audit rows (list of dicts).
    :param project_name: project / system name for the cover page.
    :param signer_name: full name of the inspecting reviewer.
    :param meaning: meaning of the electronic signature.
    :param filter_summary: human-readable filter description.
    :return: PDF file content as bytes.
    :requirement: URS-27.4 - Generate signed audit-trail export PDF.
    """
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds",
    )
    safe_slug = "".join(
        c if c.isalnum() else "-" for c in project_name
    )[:32].strip("-") or "project"
    doc_id = f"AUDIT-{safe_slug}"

    # Phase breakdown for the cover summary
    phase_counts: Dict[str, int] = {}
    for r in rows:
        ph = str(r.get("phase") or "Other")
        phase_counts[ph] = phase_counts.get(ph, 0) + 1
    phase_order = [
        "Plan", "Requirements", "Risk", "Design",
        "Verify", "Release", "Monitor", "Other",
    ]

    pdf = _ValidationReportPDF(doc_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # Page 1 - Cover
    # =========================================================
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 14, "Audit Trail Inspection Export",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(
            f"{doc_id}  |  {project_name}  |  "
            f"Generated: {timestamp}"
        ),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    _section_heading(pdf, "Export Identification")
    _kv_row(pdf, "Project / System", project_name)
    _kv_row(pdf, "Document ID",       doc_id)
    _kv_row(pdf, "Generated (UTC)",   timestamp)
    _kv_row(pdf, "Inspector",         signer_name)
    _kv_row(pdf, "Total Rows",        str(len(rows)))
    pdf.ln(4)

    _section_heading(pdf, "Applied Filters")
    _para(
        pdf,
        filter_summary
        or "No filters applied - full audit trail included.",
    )
    pdf.ln(2)

    _section_heading(pdf, "Lifecycle Phase Breakdown")
    if rows:
        for ph in phase_order:
            cnt = phase_counts.get(ph, 0)
            if cnt == 0:
                continue
            _kv_row(pdf, ph, f"{cnt} event(s)")
    else:
        _para(pdf, "No rows match the active filter.")
    pdf.ln(2)

    _section_heading(pdf, "Statement of Integrity")
    _para(
        pdf,
        "Every row in this export was retrieved unchanged from "
        "the append-only EVOLV audit trail "
        "(output/audit_trail.csv). Each row carries a SHA-256 "
        "Reasoning Hash that is also recorded in the "
        "underlying logic-archive JSON file. This page-set is "
        "an inspection artifact only; it does not alter the "
        "system of record.",
    )

    # =========================================================
    # Pages 2..N - Landscape audit table
    # =========================================================
    if rows:
        # Column widths sum to ~277mm (A4 landscape width minus margins)
        cols = [
            "Timestamp (UTC)",
            "Phase",
            "Agent",
            "Action",
            "Hash (12)",
            "Decision Logic",
        ]
        col_widths = [42.0, 22.0, 32.0, 50.0, 28.0, 103.0]
        table_rows: List[Tuple[str, ...]] = []
        for r in rows:
            ts = str(r.get("timestamp") or "")
            # Strip subsecond + tz for tighter column
            if len(ts) > 19:
                ts = ts[:19]
            table_rows.append((
                ts,
                str(r.get("phase") or "Other"),
                str(r.get("agent_name") or ""),
                str(r.get("action") or ""),
                str(r.get("reasoning_hash") or "")[:12],
                str(r.get("decision_logic") or ""),
            ))

        _table_page(
            pdf,
            heading="Audit Trail Records",
            columns=cols,
            col_widths=col_widths,
            rows=table_rows,
            meta_line=(
                f"{len(rows)} row(s) included. "
                "Sorted newest-first; hash column shows the "
                "first 12 characters of the SHA-256 Reasoning "
                "Hash used for logic-archive lookup."
            ),
        )

    # =========================================================
    # Final page - Manifestation of Signature
    # =========================================================
    _mos_page_navy(
        pdf,
        doc_id=doc_id,
        doc_kind="Audit Trail Inspection Export",
        signer_name=signer_name,
        meaning=meaning,
        timestamp=timestamp,
        extra_note=(
            "This signature attests that the inspector has "
            "reviewed the included audit rows. The export is an "
            "inspection copy; the system of record remains "
            "output/audit_trail.csv on the EVOLV platform."
        ),
    )

    return pdf.output()


# =====================================================================
# Sprint 28 - Living Traceability Matrix PDF
# =====================================================================


_TRACE_STATUS_LABEL = {
    "no-bundle":   "No Test Bundle",
    "authored":    "Bundle Authored",
    "in-progress": "Tests In Progress",
    "failed":      "Tests Failed",
    "passed":      "Tests Passed",
    "released":    "Released",
}


def _trace_summary_counts(
    rows: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Aggregate counts by status for the cover summary."""
    counts: Dict[str, int] = {}
    for r in rows:
        s = str(r.get("status") or "no-bundle")
        counts[s] = counts.get(s, 0) + 1
    return counts


def generate_traceability_matrix_pdf(
    rows: List[Dict[str, Any]],
    project_name: str,
    signer_name: str,
    meaning: str = "Traceability Matrix Inspection Export",
    filter_summary: str = "",
) -> bytes:
    """Render the Living Traceability Matrix as a signed PDF.

    Layout:

    - **Page 1 (portrait):** Cover with project name, doc id,
      generation timestamp, applied filter summary, and a status
      breakdown summary table (no-bundle, authored, in-progress,
      failed, passed, released).
    - **Pages 2-N (landscape):** Wide traceability table with
      one row per requirement covering the full chain
      (URS / Risk / UR/FR / Bundle / Tests / Pass-Fail / Defects /
      Approved).
    - **Final page (portrait):** Manifestation of Signature
      (21 CFR Part 11 §11.50).

    Each row dict is expected to be the shape produced by the
    React ``computeTraceability()`` helper. Required keys:
    ``ursId``, ``statement``, ``riskLevel`` (str|None),
    ``isGxpDirect`` (bool), ``childCount`` (int),
    ``bundle`` (dict|None with ``id`` + ``stepCount``),
    ``runs`` (list[dict] with ``status`` and ``passed``/``failed``),
    ``passedCount``, ``failedCount``, ``totalSteps``,
    ``defectCount``, ``openDefects``, ``released`` (bool),
    ``approvalCount``, ``status`` (one of _TRACE_STATUS_LABEL keys).

    :param rows: filtered traceability rows (list of dicts).
    :param project_name: project / system name for the cover page.
    :param signer_name: full name of the inspecting reviewer.
    :param meaning: meaning of the electronic signature.
    :param filter_summary: human-readable filter description.
    :return: PDF file content as bytes.
    :requirement: URS-28.4 - Generate signed Traceability Matrix
                  Inspection Export PDF.
    """
    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds",
    )
    safe_slug = "".join(
        c if c.isalnum() else "-" for c in project_name
    )[:32].strip("-") or "project"
    doc_id = f"RTM-{safe_slug}"

    status_counts = _trace_summary_counts(rows)
    status_order = [
        "released", "passed", "failed",
        "in-progress", "authored", "no-bundle",
    ]
    gxp_direct_count = sum(
        1 for r in rows if r.get("isGxpDirect")
    )
    gap_count = sum(
        1 for r in rows
        if r.get("status") in ("no-bundle", "authored")
    )
    failed_count = status_counts.get("failed", 0)

    pdf = _ValidationReportPDF(doc_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # Page 1 - Cover
    # =========================================================
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 14, "Requirements Traceability Matrix",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(
            f"{doc_id}  |  {project_name}  |  "
            f"Generated: {timestamp}"
        ),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    _section_heading(pdf, "Export Identification")
    _kv_row(pdf, "Project / System",   _safe(project_name))
    _kv_row(pdf, "Document ID",        _safe(doc_id))
    _kv_row(pdf, "Generated (UTC)",    _safe(timestamp))
    _kv_row(pdf, "Inspector",          _safe(signer_name))
    _kv_row(pdf, "Total Requirements", str(len(rows)))
    _kv_row(pdf, "GxP Direct",         str(gxp_direct_count))
    _kv_row(pdf, "Coverage Gaps",      str(gap_count))
    _kv_row(pdf, "Failed Tests",       str(failed_count))
    pdf.ln(4)

    _section_heading(pdf, "Applied Filters")
    _para(
        pdf,
        filter_summary
        or "No filters applied - full requirement set included.",
    )
    pdf.ln(2)

    _section_heading(pdf, "Status Breakdown")
    if rows:
        for s in status_order:
            cnt = status_counts.get(s, 0)
            if cnt == 0:
                continue
            _kv_row(
                pdf,
                _safe(_TRACE_STATUS_LABEL.get(s, s)),
                _safe(f"{cnt} requirement(s)"),
            )
    else:
        _para(pdf, "No rows match the active filter.")
    pdf.ln(2)

    _section_heading(pdf, "Statement of Integrity")
    _para(
        pdf,
        "This matrix was assembled from the live EVOLV platform "
        "state at the moment of export - Requirements, Risk, "
        "Test Bundles, Test Runs, Defects, and Release Approvals. "
        "Every linked artefact is recorded in the append-only "
        "audit trail (output/audit_trail.csv). This page-set is "
        "an inspection artefact only; it does not alter any "
        "system of record.",
    )

    # =========================================================
    # Pages 2..N - Landscape traceability table
    # =========================================================
    if rows:
        # Column widths sum to ~277mm (A4 landscape width minus margins)
        cols = [
            "URS ID",
            "Requirement",
            "Risk",
            "UR/FR",
            "Bundle",
            "Tests Run",
            "Pass / Fail",
            "Defects",
            "Released",
            "Status",
        ]
        col_widths = [
            22.0, 75.0, 16.0, 18.0, 28.0,
            22.0, 22.0, 22.0, 18.0, 34.0,
        ]
        dash = "-"  # Latin-1 safe placeholder
        table_rows: List[Tuple[str, ...]] = []
        for r in rows:
            urs_id = str(r.get("ursId") or "")
            statement = str(r.get("statement") or "")
            if len(statement) > 220:
                statement = statement[:217] + "..."

            risk = str(r.get("riskLevel") or dash)
            if r.get("isGxpDirect"):
                risk += " *"

            child_count = int(r.get("childCount") or 0)
            ur_fr = (
                f"UR + {child_count} FR"
                if child_count else "UR only"
            )

            bundle = r.get("bundle") or {}
            bundle_str = (
                f"{bundle.get('id') or dash} "
                f"({bundle.get('stepCount') or 0} steps)"
                if bundle else dash
            )

            runs = r.get("runs") or []
            tests_run = (
                f"{len(runs)} run(s)" if runs else dash
            )

            passed = int(r.get("passedCount") or 0)
            failed = int(r.get("failedCount") or 0)
            pf = (
                f"{passed} P / {failed} F"
                if (passed or failed) else dash
            )

            d_total = int(r.get("defectCount") or 0)
            d_open  = int(r.get("openDefects") or 0)
            defects_str = (
                f"{d_total} ({d_open} open)"
                if d_total else dash
            )

            released_str = (
                f"Yes ({r.get('approvalCount') or 0})"
                if r.get("released") else dash
            )

            status_str = _TRACE_STATUS_LABEL.get(
                str(r.get("status") or "no-bundle"),
                str(r.get("status") or "no-bundle"),
            )

            table_rows.append((
                _safe(urs_id),
                _safe(statement),
                _safe(risk),
                _safe(ur_fr),
                _safe(bundle_str),
                _safe(tests_run),
                _safe(pf),
                _safe(defects_str),
                _safe(released_str),
                _safe(status_str),
            ))

        _table_page(
            pdf,
            heading="Requirements Traceability Matrix",
            columns=cols,
            col_widths=col_widths,
            rows=table_rows,
            meta_line=_safe(
                f"{len(rows)} requirement(s) included. "
                "Risk column appends '*' when impact is "
                "GxP Direct. Pass / Fail counts reflect the "
                "latest test run for the linked bundle."
            ),
        )

    # =========================================================
    # Final page - Manifestation of Signature
    # =========================================================
    _mos_page_navy(
        pdf,
        doc_id=doc_id,
        doc_kind="Traceability Matrix Inspection Export",
        signer_name=signer_name,
        meaning=meaning,
        timestamp=timestamp,
        extra_note=(
            "This signature attests that the inspector has "
            "reviewed the full requirements-to-release chain "
            "shown in this matrix. The export is an inspection "
            "copy; the systems of record remain the EVOLV "
            "platform state and the append-only audit trail."
        ),
    )

    return pdf.output()


# =====================================================================
# Sprint 39 - AI Trustworthiness Credibility Assessment Report
# =====================================================================

_STATUS_COLOR = {
    "Met":     (6, 95, 70),      # lime-green
    "Partial": (146, 64, 14),    # amber
    "Gap":     (185, 28, 28),    # red
}


def _twr_status_pill(
    pdf: FPDF, status: str, x: float, y: float,
) -> None:
    """Draw a colored status pill at (x, y) for Met/Partial/Gap."""
    pdf.set_xy(x, y)
    pdf.set_fill_color(*_STATUS_COLOR.get(status, DARK_TEXT))
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(16, 5, status, align="C", fill=True)
    pdf.set_text_color(*DARK_TEXT)


def _twr_5_signer_page(pdf: FPDF, report_id: str,
                       signers_meta: Dict[str, str],
                       meaning: str) -> None:
    """Manifestation of Signature page - 5 signers per the
    pharma SOP RACI pattern. Pre-fills any signer name passed
    in signers_meta; empty fields render as blank signature lines.
    """
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 12, "Manifestation of Signature",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(
            f"{report_id}  |  21 CFR Part 11 §11.50  |  "
            f"5-signer RACI per AI Trustworthiness SOP pattern"
        ),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    _section_heading(pdf, "Meaning of Signatures")
    _para(pdf, meaning)
    pdf.ln(2)

    _section_heading(pdf, "Required Approvals")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)

    role_to_key = [
        ("Business Owner",
         "business_owner",
         "Performs the assessment and documents results. "
         "Verifies operational SOP(s) are made effective."),
        ("Quality Assurance",
         "quality_assurance",
         "Ensures the assessment is performed properly and "
         "documented per controlled procedures."),
        ("Service Owner",
         "service_owner",
         "Reviews / approves documents per the operating SOP."),
        ("System SME (System / IT Application Owner)",
         "system_sme",
         "Reviews and approves. Provides technical assessments. "
         "Identifies strategy for leveraging supplier "
         "documentation."),
        ("AI Model SME",
         "ai_model_sme",
         "Assists with the assessment. Ensures proper "
         "data-science / statistical analysis has been "
         "performed to evidence credibility."),
    ]

    for role, key, duty in role_to_key:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 6, _safe(role),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, _safe(duty),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Name + signature + date row
        signer_name = signers_meta.get(key, "") or ""
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(35, 6, "Name:")
        pdf.cell(75, 6, _safe(signer_name) or "_" * 40)
        pdf.cell(25, 6, "Date (UTC):")
        pdf.cell(0, 6, "_" * 22,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.cell(35, 6, "Signature:")
        pdf.cell(0, 6, "_" * 80,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.ln(2)
    _section_heading(pdf, "21 CFR Part 11 Compliance Note")
    _para(
        pdf,
        "Electronic signatures executed in EVOLV are "
        "non-repudiable, attributable to the named individual, "
        "captured with a UTC timestamp, and bound to this "
        "specific document by SHA-256 hash. Per 21 CFR "
        "Part 11.50, this Manifestation of Signature page "
        "documents the meaning of each signature (review, "
        "approval, attestation) and the identity of each "
        "signer. The signed PDF is the controlled record; "
        "the underlying JSON is preserved in EVOLV's "
        "append-only audit trail.",
    )


def generate_trustworthiness_report_pdf(
    report: Dict[str, Any],
    signers: Optional[Dict[str, str]] = None,
    meaning: str = "Approval of AI Trustworthiness Assessment",
) -> bytes:
    """Generate a signed PDF AI Trustworthiness Credibility
    Assessment Report.

    Pharma-SOP compliant structure:
      Page 1 - Cover (report ID, customer, COU, frameworks,
               summary counts)
      Page 2 - Executive Summary + COU Assessment
      Page 3 - AI Tool Description (SOP 5.1.3.2-5.1.3.5)
      Page 4 - Risk Analysis (per-agent risk inheritance)
      Page 5 - Bounded Autonomy Evidence (5 pillars)
      Page 6 - Continuous Monitoring + Incident Response
      Page 7 - Limitations (the honest section)
      Pages 8-N (landscape) - Framework Mappings table with
               Met/Partial/Gap status pills + evidence refs
      Final page - Manifestation of Signature (5 signers per
               pharma SOP RACI)

    :param report: TrustworthinessReport.to_dict() output.
    :param signers: optional dict pre-filling signer names -
        keys: business_owner, quality_assurance, service_owner,
        system_sme, ai_model_sme.
    :param meaning: meaning of the electronic signatures.
    :return: PDF file content as bytes.
    :requirement: URS-39.10 - Generate signed PDF trustworthiness
                  report.
    """
    signers = signers or {}
    report_id = str(report.get("report_id", "TWR-UNKNOWN"))
    cou = report.get("cou", {})
    customer = report.get("customer_name", "?")
    frameworks = report.get("primary_frameworks", [])
    summary = report.get("summary_counts", {})
    generated_at = report.get("generated_at", "")
    mappings = report.get("framework_mappings", [])

    pdf = _ValidationReportPDF(report_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =====================================================
    # Page 1 - Cover
    # =====================================================
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(
        0, 12, "AI Trustworthiness Credibility",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_xy(10, pdf.get_y())
    pdf.cell(
        0, 12, "Assessment Report",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        _safe(f"{report_id}  |  Generated: {generated_at}"),
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    _section_heading(pdf, "Report Identification")
    _kv_row(pdf, "Report ID",          report_id)
    _kv_row(pdf, "Customer",           customer)
    _kv_row(pdf, "COU Identifier",
            cou.get("cou_id", "?"))
    _kv_row(pdf, "Target System",
            cou.get("target_system", "-"))
    _kv_row(pdf, "Deployment Region",
            cou.get("deployment_region", "?"))
    _kv_row(pdf, "GxP Classification",
            cou.get("gxp_classification", "?"))
    _kv_row(pdf, "Risk Level",
            cou.get("risk_level", "?"))
    _kv_row(pdf, "Lifecycle Stage",
            cou.get("poc_or_production", "POC"))
    pdf.ln(2)

    _section_heading(pdf, "Context of Use")
    _para(pdf, cou.get("statement", "-"))
    pdf.ln(2)

    _section_heading(pdf, "Primary Frameworks Mapped")
    for fw in frameworks:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 6, _safe(f"- {fw}"),
                 new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*DARK_TEXT)
    pdf.ln(2)

    _section_heading(pdf, "Assessment Headline")
    pdf.set_font("Helvetica", "", 10)
    n_total   = summary.get("controls_mapped", 0)
    n_met     = summary.get("controls_met", 0)
    n_partial = summary.get("controls_partial", 0)
    n_gap     = summary.get("controls_gap", 0)
    pct_met   = (n_met / n_total * 100) if n_total else 0
    pdf.multi_cell(
        0, 6,
        _safe(
            f"{n_met} of {n_total} mapped controls fully met "
            f"({pct_met:.0f}%). "
            f"{n_partial} partial coverage. "
            f"{n_gap} explicit gaps with documented mitigation. "
            f"Every claim in this report cites a verifiable "
            f"artefact - Agent Passport version, audit-trail "
            f"row, or Logic Archive hash - so an inspector "
            f"can re-derive the assessment from EVOLV's own "
            f"records."
        ),
        new_x="LMARGIN", new_y="NEXT",
    )

    # =====================================================
    # Page 2 - Executive Summary
    # =====================================================
    pdf.add_page(orientation="P")
    _section_heading(pdf, "Executive Summary")
    _para(pdf, report.get("executive_summary", ""))
    pdf.ln(4)

    _section_heading(pdf, "Context of Use Assessment")
    cou_assess = report.get("cou_assessment", {})
    _kv_row(pdf, "Decision Authority",
            cou_assess.get("decision_authority", "-"))
    _kv_row(pdf, "Human in Loop",
            cou_assess.get("human_in_loop", "-")[:120])
    triggers = cou_assess.get("triggers_detected", [])
    if triggers:
        _kv_row(pdf, "Triggers Detected", ", ".join(triggers))
    integrates = cou_assess.get("integrates_with", [])
    if integrates:
        _kv_row(pdf, "Integrates With", ", ".join(integrates))

    # =====================================================
    # Page 3 - AI Tool Description (SOP 5.1.3.2-5.1.3.5)
    # =====================================================
    pdf.add_page(orientation="P")
    desc = report.get("ai_tool_description", {})
    _section_heading(pdf, "AI Tool Description")
    _kv_row(pdf, "Tool Name",     desc.get("tool_name", "-"))
    _kv_row(pdf, "Vendor",        desc.get("vendor", "-"))
    _kv_row(pdf, "Tool Type",     desc.get("tool_type", "-"))
    _kv_row(pdf, "Intended Use",  desc.get("intended_use", "-")[:80])
    pdf.ln(2)

    comp = desc.get("ai_components", {})
    _section_heading(pdf, "AI Components")
    det = comp.get("deterministic_agents", [])
    llm = comp.get("llm_backed_agents", [])
    fnd = comp.get("foundation_models", [])
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, _safe(
        f"Deterministic agents ({len(det)}):"),
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, 5, _safe(", ".join(det) or "-"),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, _safe(
        f"LLM-backed agents ({len(llm)}):"),
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, 5, _safe(", ".join(llm) or "-"),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, "Foundation models:",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, 5, _safe(", ".join(fnd)),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    prov = desc.get("model_provenance", {})
    _section_heading(pdf, "Model Provenance")
    for label, key in [
        ("Type",            "type"),
        ("Training Data",   "training_data"),
        ("Tenant Isolation", "tenant_isolation"),
    ]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 5, _safe(label),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5, _safe(prov.get(key, "-")),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    pdf.ln(2)
    _section_heading(pdf, "Development Process")
    _para(pdf, desc.get("development_process", "-"))
    pdf.ln(2)

    _section_heading(pdf, "Assessment Process")
    _para(pdf, desc.get("assessment_process", "-"))

    # =====================================================
    # Page 4 - Risk Analysis
    # =====================================================
    pdf.add_page(orientation="P")
    risk = report.get("risk_analysis", {})
    _section_heading(pdf, "Risk Analysis")
    _kv_row(pdf, "Method",           risk.get("method", "-"))
    _kv_row(pdf, "COU Risk Level",   risk.get("cou_risk_level", "-"))
    highest = risk.get("highest_risk_agents", [])
    _kv_row(pdf, "Highest-Risk Agents",
            ", ".join(highest) or "-")
    pdf.ln(2)

    _section_heading(pdf, "Per-Agent Risk Inheritance")
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.cell(45, 6, "Agent",         border=0, fill=True)
    pdf.cell(15, 6, "Passport",      border=0, fill=True)
    pdf.cell(18, 6, "LLM?",          border=0, fill=True, align="C")
    pdf.cell(20, 6, "Rollback?",     border=0, fill=True, align="C")
    pdf.cell(0,  6, "Risk for this COU",
             border=0, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_font("Helvetica", "", 8)
    for ar in risk.get("agent_risks", []):
        pdf.cell(45, 5, _safe(ar.get("agent", ""))[:32])
        pdf.cell(15, 5, _safe(ar.get("passport_version", "?")))
        pdf.cell(18, 5,
                 "Yes" if ar.get("calls_llm") else "No",
                 align="C")
        pdf.cell(20, 5,
                 "Yes" if ar.get("rollback_eligible") else "No",
                 align="C")
        risk_lvl = ar.get("risk_for_this_cou", "?")
        pdf.set_text_color(*_STATUS_COLOR.get(
            "Met" if risk_lvl == "Low"
            else "Partial" if risk_lvl == "Medium"
            else "Gap", DARK_TEXT,
        ))
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 5, risk_lvl,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_TEXT)

    # =====================================================
    # Page 5 - Bounded Autonomy Evidence
    # =====================================================
    pdf.add_page(orientation="P")
    ba = report.get("bounded_autonomy_evidence", {})
    _section_heading(pdf, "Bounded Autonomy - Principle")
    _para(pdf, ba.get("principle", "-"))
    pdf.ln(3)

    _section_heading(pdf, "Five Evidence Pillars")
    for pillar in ba.get("evidence_pillars", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 6, _safe(pillar.get("pillar", "-")),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5, _safe(pillar.get("summary", "")),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            0, 4,
            _safe(f"Evidence: {pillar.get('evidence', '')}"),
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(2)

    # =====================================================
    # Page 6 - Continuous Monitoring + Incident Response
    # =====================================================
    pdf.add_page(orientation="P")
    mon = report.get("continuous_monitoring", {})
    _section_heading(pdf, "Continuous Monitoring")
    for k, label in [
        ("validated_state_engine", "Validated State Engine"),
        ("regulatory_drift_agent", "Regulatory Drift Agent"),
        ("eval_framework",         "Eval Framework"),
    ]:
        block = mon.get(k, {})
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5, _safe(block.get("purpose", "-")),
                       new_x="LMARGIN", new_y="NEXT")
        if block.get("exposed_at"):
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5,
                     _safe(f"Exposed at: {block['exposed_at']}"),
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.ln(2)
    _section_heading(pdf, "Incident Response")
    inc = report.get("incident_response", {})
    for k, label in [
        ("if_ai_misbehaves",   "If AI Behaves Unexpectedly"),
        ("if_corpus_drifts",   "If Regulatory Corpus Drifts"),
        ("if_inspector_arrives", "If An Inspector Arrives"),
    ]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_TEXT)
        for item in inc.get(k, []):
            pdf.multi_cell(0, 5, _safe(f"- {item}"),
                           new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # =====================================================
    # Page 7 - Limitations (the honest section)
    # =====================================================
    pdf.add_page(orientation="P")
    _section_heading(pdf, "Limitations and Documented Gaps")
    _para(
        pdf,
        "EVOLV publishes its known constraints. Pharma "
        "evaluators value honest gap-naming over comprehensive-"
        "sounding marketing copy. Each item below names a real "
        "limitation today and the roadmap path that closes it "
        "where applicable.",
    )
    pdf.ln(2)
    for item in report.get("limitations", []):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5, _safe(f"- {item}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # =====================================================
    # Pages 8-N (landscape) - Framework Mappings table
    # =====================================================
    if mappings:
        pdf.add_page(orientation="L")
        pdf.set_xy(10, pdf.get_y() + 4)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 10, "Framework Mappings",
                 align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0, 6,
            _safe(
                f"{len(mappings)} controls mapped across "
                f"{len(frameworks)} framework(s). Status "
                f"taxonomy: Met / Partial / Gap. Every row "
                f"cites verifiable evidence references."
            ),
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(4)

        # Table header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.cell(40, 6, "Framework",   border=0, fill=True)
        pdf.cell(20, 6, "Section",     border=0, fill=True)
        pdf.cell(70, 6, "Requirement", border=0, fill=True)
        pdf.cell(90, 6, "EVOLV Evidence",
                 border=0, fill=True)
        pdf.cell(28, 6, "Evidence Refs",
                 border=0, fill=True)
        pdf.cell(20, 6, "Status",
                 border=0, fill=True, align="C",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*DARK_TEXT)
        pdf.set_font("Helvetica", "", 7)

        for m in mappings:
            row_top = pdf.get_y()
            # Truncate to keep rows readable; full text is in JSON
            fw = _safe(m.get("framework", ""))[:24]
            sec = _safe(m.get("section_id", ""))[:12]
            req = _safe(m.get("requirement", ""))[:140]
            resp = _safe(m.get("evolv_response", ""))[:180]
            n_evidence = len(m.get("evidence_refs", []))
            status = m.get("status", "Met")

            # Measure max height needed
            pdf.set_xy(70, row_top)
            req_lines = pdf.multi_cell(70, 4, req,
                                       split_only=True)
            resp_lines = pdf.multi_cell(90, 4, resp,
                                        split_only=True)
            n_lines = max(len(req_lines), len(resp_lines), 1)
            row_h = max(8, 4 * n_lines + 2)

            # Page-break guard
            if row_top + row_h > 195:   # below page bottom
                pdf.add_page(orientation="L")
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_fill_color(*NAVY)
                pdf.set_text_color(*WHITE)
                pdf.cell(40, 6, "Framework",   border=0, fill=True)
                pdf.cell(20, 6, "Section",     border=0, fill=True)
                pdf.cell(70, 6, "Requirement", border=0, fill=True)
                pdf.cell(90, 6, "EVOLV Evidence",
                         border=0, fill=True)
                pdf.cell(28, 6, "Evidence Refs",
                         border=0, fill=True)
                pdf.cell(20, 6, "Status",
                         border=0, fill=True, align="C",
                         new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*DARK_TEXT)
                pdf.set_font("Helvetica", "", 7)
                row_top = pdf.get_y()

            # Draw the row
            pdf.set_xy(10, row_top)
            pdf.cell(40, row_h, fw, border="B")
            pdf.set_xy(50, row_top)
            pdf.cell(20, row_h, sec, border="B")
            pdf.set_xy(70, row_top)
            pdf.multi_cell(70, 4, req, border=0)
            pdf.set_xy(140, row_top)
            pdf.multi_cell(90, 4, resp, border=0)
            pdf.set_xy(230, row_top)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(28, row_h, f"{n_evidence} ref(s)",
                     border="B", align="C")
            pdf.set_font("Helvetica", "", 7)
            _twr_status_pill(pdf, status,
                             x=261, y=row_top + (row_h - 5) / 2)
            pdf.set_xy(10, row_top + row_h)

        # Evidence references appendix - one row per mapping
        pdf.add_page(orientation="P")
        _section_heading(pdf, "Evidence Reference Appendix")
        _para(
            pdf,
            "Per-control evidence references. An inspector with "
            "this appendix plus the EVOLV audit trail and Logic "
            "Archive directory can re-derive every claim above.",
        )
        pdf.ln(2)
        for m in mappings:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*ACCENT)
            pdf.cell(
                0, 5,
                _safe(
                    f"{m.get('framework', '?')} "
                    f"{m.get('section_id', '?')}"
                ),
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*DARK_TEXT)
            for ref in m.get("evidence_refs", []):
                pdf.multi_cell(
                    0, 4,
                    _safe(
                        f"  - [{ref.get('kind', '?')}] "
                        f"{ref.get('identifier', '?')} "
                        f"@ {ref.get('location', '')}"
                    ),
                    new_x="LMARGIN", new_y="NEXT",
                )
            if m.get("notes"):
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(
                    0, 4,
                    _safe(f"  Note: {m['notes']}"),
                    new_x="LMARGIN", new_y="NEXT",
                )
            pdf.ln(1)

    # =====================================================
    # Final page - Manifestation of Signature (5 signers)
    # =====================================================
    _twr_5_signer_page(pdf, report_id, signers, meaning)

    return pdf.output()


# =====================================================================
# Sprint 40 - Bounded Autonomy Profile (BAP) PDF
# =====================================================================

_BAP_TIER_COLOR = {
    "BAP-0": (107, 114, 128),
    "BAP-1": (59, 130, 246),
    "BAP-2": (6, 95, 70),
    "BAP-3": (146, 64, 14),
    "BAP-4": (124, 58, 237),
    "BAP-X": (185, 28, 28),
}


def _bap_tier_badge(
    pdf: FPDF, tier_id: str, tier_name: str,
    x: float, y: float, width: float = 90, height: float = 18,
) -> None:
    """Draw a coloured tier badge on the BAP cover."""
    color = _BAP_TIER_COLOR.get(tier_id, DARK_TEXT)
    pdf.set_xy(x, y)
    pdf.set_fill_color(*color)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(width, height,
             _safe(f"{tier_id} - {tier_name}"),
             align="C", fill=True)
    pdf.set_text_color(*DARK_TEXT)


def _bap_section(pdf: FPDF, label: str) -> None:
    """Section heading specific to BAP layout - with underline."""
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 7, _safe(label),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.2)
    pdf.ln(2)


def _bap_q_block(pdf: FPDF, label: str, body: str) -> None:
    """One Assurance-Argument question block - heading + body."""
    _bap_section(pdf, label)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, 5, _safe(body or "-"),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _bap_q_block_list(
    pdf: FPDF, label: str, items: List[str],
) -> None:
    """One Assurance-Argument question block - heading + list."""
    _bap_section(pdf, label)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    if not items:
        pdf.cell(0, 5, "(none)", new_x="LMARGIN", new_y="NEXT")
        return
    for it in items:
        pdf.multi_cell(0, 5, _safe(f"- {it}"),
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _bap_5_signer_page(
    pdf: FPDF, profile_id: str, tier_id: str,
    signers: Dict[str, str], meaning: str,
) -> None:
    """5-signer Manifestation of Signature page (pharma SOP RACI)."""
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 12, "Manifestation of Signature",
             align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6,
             _safe(f"{profile_id}  |  Tier {tier_id}  |  "
                   "21 CFR Part 11 Sec.11.50  |  5-signer RACI"),
             align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    _section_heading(pdf, "Meaning of Signatures")
    _para(pdf, meaning)
    pdf.ln(2)

    _section_heading(pdf, "Required Approvals")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)

    roles = [
        ("Business Owner", "business_owner",
         "Owns the deployment. Verifies the BAP tier reflects "
         "operational reality."),
        ("Quality Assurance", "quality_assurance",
         "Verifies the BAP is documented and signed per "
         "controlled procedures."),
        ("Service Owner", "service_owner",
         "Reviews / approves per the operating SOP."),
        ("System SME (System / IT Application Owner)",
         "system_sme",
         "Reviews technical fit. Verifies Failure Envelope "
         "coverage is achievable in the target environment."),
        ("AI Model SME", "ai_model_sme",
         "Verifies the tier, the Assurance Argument, and the "
         "named Fragility Markers reflect the AI model's "
         "actual behaviour envelope."),
    ]
    for role, key, duty in roles:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 6, _safe(role), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, _safe(duty),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        signer_name = signers.get(key, "") or ""
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(35, 6, "Name:")
        pdf.cell(75, 6, _safe(signer_name) or "_" * 40)
        pdf.cell(25, 6, "Date (UTC):")
        pdf.cell(0, 6, "_" * 22, new_x="LMARGIN", new_y="NEXT")
        pdf.cell(35, 6, "Signature:")
        pdf.cell(0, 6, "_" * 80, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)


def generate_bounded_autonomy_profile_pdf(
    profile: Dict[str, Any],
    signers: Optional[Dict[str, str]] = None,
    meaning: str = "Approval of Bounded Autonomy Profile",
) -> bytes:
    """Generate a signed PDF Bounded Autonomy Profile report.

    Structure (~11 pages):

      Page 1 - Cover with Tier badge, COU, profile ID, headline
               scores (coverage + capability)
      Page 2 - Tier verdict + tier rationale chain
      Page 3 - Layer 1: Impact Class detail
      Page 4 - Layer 2: Failure Envelope (AOE + 4 scenario buckets)
      Page 5 - Layer 2 continued: open hazards + automation-bias
      Page 6 - Layer 3: Control Sustainability gaps
      Page 7 - Assurance Argument Q1 to Q4
      Page 8 - Assurance Argument Q5 to Q6
      Page 9 - Q7 Fragility Markers
      Page 10 - Required Controls + Next Actions
      Final page - 5-signer Manifestation of Signature

    BAP-X profiles render the same shape but page 2 leads with
    a red exclusion verdict and the refusal action chain.

    :requirement: URS-40.11 - Generate signed BAP PDF report.
    """
    signers = signers or {}
    profile_id = str(profile.get("profile_id", "BAP-UNKNOWN"))
    tier_id = str(profile.get("tier_id", "BAP-?"))
    tier_name = str(profile.get("tier_name", "Unknown"))
    cou = profile.get("cou", {})
    customer = cou.get("customer_name", "?")
    statement = cou.get("statement", "")
    is_exclusion = bool(profile.get("is_exclusion", False))
    generated_at = profile.get("generated_at", "")
    impact = profile.get("impact_class", {})
    envelope = profile.get("failure_envelope", {})
    sustainability = profile.get("control_sustainability", {})
    argument = profile.get("assurance_argument", {})
    required_controls = profile.get("required_controls_at_tier", [])
    next_actions = profile.get("next_actions", [])
    tier_rationale = profile.get("tier_rationale", [])

    pdf = _ValidationReportPDF(profile_id)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Page 1 - Cover
    pdf.add_page(orientation="P")
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 14, "Bounded Autonomy Profile",
             align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6,
             _safe(f"{profile_id}  |  Generated: {generated_at}"),
             align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    _bap_tier_badge(pdf, tier_id, tier_name,
                    x=10, y=pdf.get_y(), width=90, height=18)
    pdf.ln(24)

    _section_heading(pdf, "Profile Identification")
    _kv_row(pdf, "Profile ID", profile_id)
    _kv_row(pdf, "Customer", customer)
    _kv_row(pdf, "Target System",
            cou.get("target_system") or "-")
    _kv_row(pdf, "Deployment Region",
            cou.get("deployment_region", "-"))
    _kv_row(pdf, "GxP Classification",
            cou.get("gxp_classification", "-"))
    _kv_row(pdf, "Risk Level", cou.get("risk_level", "-"))
    _kv_row(pdf, "Lifecycle Stage",
            cou.get("poc_or_production", "-"))
    pdf.ln(2)
    _section_heading(pdf, "Context of Use")
    _para(pdf, statement)
    pdf.ln(2)
    _section_heading(pdf, "Headline Scores")
    _kv_row(pdf, "Impact Class",
            f"{impact.get('class_id', '?')} "
            f"({impact.get('name', '?')})")
    _kv_row(pdf, "Failure Envelope coverage",
            f"{envelope.get('coverage_score', 0)} / 100")
    _kv_row(pdf, "Control Sustainability",
            f"{sustainability.get('capability_score', 0)} / 100")
    _kv_row(pdf, "Open hazards",
            str(len(envelope.get('open_hazards', []))))
    _kv_row(pdf, "Fragility Markers",
            str(len(argument.get('q7_fragility_markers', []))))

    # Page 2 - Tier verdict
    pdf.add_page(orientation="P")
    _section_heading(pdf, "Tier Verdict")
    if is_exclusion:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 8, "BAP-X (Out-of-Envelope Exclusion)",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        _para(pdf,
              "This deployment cannot be approved in its "
              "current shape, regardless of controls applied. "
              "EVOLV's exclusion category names use-case shapes "
              "that do not yield to 'control upward' (more "
              "documentation, more review). The correct move "
              "is a structured refusal plus a re-scope path.")
        pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, _safe(f"{tier_id} - {tier_name}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        _para(pdf, str(profile.get("tier_summary", "")))
        pdf.ln(2)
    _section_heading(pdf, "Tier Rationale Chain")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for r in tier_rationale:
        pdf.multi_cell(0, 5, _safe(f"- {r}"),
                       new_x="LMARGIN", new_y="NEXT")

    # Page 3 - Layer 1 Impact Class
    pdf.add_page(orientation="P")
    _bap_section(pdf,
                 "Layer 1 - Impact Class (consequence ceiling)")
    _kv_row(pdf, "Class ID", impact.get("class_id", "-"))
    _kv_row(pdf, "Class Name", impact.get("name", "-"))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Consequence Ceiling",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, 5,
                   _safe(impact.get("consequence_ceiling", "-")),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Drivers", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for d in impact.get("drivers", []):
        pdf.multi_cell(0, 5, _safe(f"- {d}"),
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Rationale", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, _safe(impact.get("rationale", "-")),
                   new_x="LMARGIN", new_y="NEXT")

    # Page 4 - Layer 2 Failure Envelope
    pdf.add_page(orientation="P")
    _bap_section(pdf,
                 "Layer 2 - Failure Envelope (diagnostic middle)")
    aoe = envelope.get("approved_operating_envelope", {})
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Approved Operating Envelope (AOE)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    _kv_row(pdf, "Target system",
            aoe.get("target_system") or "-")
    _kv_row(pdf, "Deployment region",
            aoe.get("deployment_region", "-"))
    in_scope = aoe.get("in_scope_actions", [])
    out_scope = aoe.get("out_of_scope_actions", [])
    _kv_row(pdf, "In-scope actions (sample)",
            ", ".join(in_scope[:5]) +
            (f"  (+{len(in_scope)-5} more)"
             if len(in_scope) > 5 else ""))
    _kv_row(pdf, "Out-of-scope actions",
            ", ".join(out_scope[:5]) +
            (f"  (+{len(out_scope)-5} more)"
             if len(out_scope) > 5 else ""))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6,
             "Scenario Coverage (4-bucket classification)",
             new_x="LMARGIN", new_y="NEXT")
    for bucket in envelope.get("scenario_coverage", []):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 6,
                 _safe(f"{bucket['bucket']} "
                       f"({bucket['count']})"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_TEXT)
        for ex in bucket.get("examples", [])[:5]:
            pdf.multi_cell(0, 4, _safe(f"   - {ex}"),
                           new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # Page 5 - Layer 2 continued
    pdf.add_page(orientation="P")
    _bap_section(pdf,
                 "Layer 2 - Open Hazards and Automation Bias")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6,
             "Open hazards (named, not yet controlled)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    open_hazards = envelope.get("open_hazards", [])
    if open_hazards:
        for h in open_hazards:
            pdf.multi_cell(0, 5, _safe(f"- {h}"),
                           new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5, "(none identified at this tier)",
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Automation-bias indicators (structural)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for ind in envelope.get("automation_bias_indicators", []):
        pdf.multi_cell(0, 5, _safe(f"- {ind}"),
                       new_x="LMARGIN", new_y="NEXT")

    # Page 6 - Layer 3 Control Sustainability
    pdf.add_page(orientation="P")
    _bap_section(pdf,
                 "Layer 3 - Control Sustainability")
    _kv_row(pdf, "Capability score",
            f"{sustainability.get('capability_score', 0)} / 100")
    _kv_row(pdf, "Corpus owner named",
            "Yes" if sustainability.get("corpus_owner_named")
            else "No")
    _kv_row(pdf, "Vendor change-control armed",
            "Yes" if sustainability.get(
                "vendor_model_change_control_armed") else "No")
    _kv_row(pdf, "Reviewer qualification documented",
            "Yes" if sustainability.get(
                "reviewer_qualification_documented") else "No")
    _kv_row(pdf, "Drift monitoring active",
            "Yes" if sustainability.get(
                "drift_monitoring_active") else "No")
    lat = sustainability.get("deviation_handling_latency_days")
    _kv_row(pdf, "Deviation->CAPA latency",
            f"{lat} days" if lat is not None else "Not measured")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Named gaps", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    gaps = sustainability.get("gaps", [])
    if gaps:
        for g in gaps:
            pdf.multi_cell(0, 5, _safe(f"- {g}"),
                           new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5,
                 "(no gaps - capability matches required tier)",
                 new_x="LMARGIN", new_y="NEXT")

    # Page 7 - Assurance Argument Q1-Q4
    pdf.add_page(orientation="P")
    _bap_q_block(pdf, "Q1 - Approved Purpose",
                 str(argument.get("q1_approved_purpose", "")))
    _bap_q_block_list(pdf, "Q2 - Explicitly Out of Scope",
                      argument.get("q2_out_of_scope", []))
    _bap_q_block_list(pdf, "Q3 - Hazard Mechanisms",
                      argument.get("q3_hazard_mechanisms", []))
    _bap_section(pdf, "Q4 - Controls per Hazard")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for c in argument.get("q4_controls_per_hazard", []):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ACCENT)
        pdf.multi_cell(0, 5,
                       _safe(f"Hazard: {c.get('hazard', '-')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5,
                       _safe(f"   Control: "
                             f"{c.get('control', '-')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # Page 8 - Assurance Argument Q5-Q6
    pdf.add_page(orientation="P")
    _bap_section(pdf, "Q5 - Evidence per Control")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for e in argument.get("q5_evidence_per_control", []):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ACCENT)
        pdf.multi_cell(0, 5,
                       _safe(f"Control: {e.get('control', '-')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5,
                       _safe(f"   Evidence: "
                             f"{e.get('evidence', '-')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    _bap_section(pdf, "Q6 - Residual Risk Owners")
    for r in argument.get("q6_residual_risk_owners", []):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ACCENT)
        pdf.multi_cell(0, 5,
                       _safe(f"Residual risk: "
                             f"{r.get('residual_risk', '-')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5,
                       _safe(f"   Owner role: "
                             f"{r.get('owner_role', '-')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # Page 9 - Q7 Fragility Markers (differentiator)
    pdf.add_page(orientation="P")
    _bap_section(pdf,
                 "Q7 - Fragility Markers (what would have to "
                 "change for this argument to break)")
    _para(pdf,
          "A safety argument that doesn't name its own "
          "fragility is mostly a sales document. Each Fragility "
          "Marker below names a standing assumption, the "
          "consequence if the assumption breaks, what to watch "
          "for, and who owns that watch.")
    pdf.ln(2)
    for i, fm in enumerate(
        argument.get("q7_fragility_markers", []), start=1,
    ):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 6,
                 _safe(f"Marker {i} - assumption"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(0, 5, _safe(fm.get("assumption", "-")),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        for lbl, key in [
            ("If broken then:", "if_broken_then"),
            ("Watch signal:",   "watch_signal"),
            ("Owner role:",     "owner_role"),
        ]:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*NAVY)
            pdf.cell(0, 5, lbl, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK_TEXT)
            pdf.multi_cell(0, 5, _safe(fm.get(key, "-")),
                           new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        pdf.ln(2)

    # Page 10 - Required Controls + Next Actions
    pdf.add_page(orientation="P")
    _bap_section(pdf, f"Required Controls at {tier_id}")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    for c in required_controls:
        pdf.multi_cell(0, 5, _safe(f"- {c}"),
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    _bap_section(pdf, "Next Actions")
    for a in next_actions:
        pdf.multi_cell(0, 5, _safe(f"- {a}"),
                       new_x="LMARGIN", new_y="NEXT")

    # Final page - Manifestation of Signature
    _bap_5_signer_page(pdf, profile_id, tier_id, signers, meaning)

    return pdf.output()
