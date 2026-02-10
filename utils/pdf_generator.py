"""
PDF Generators for the EVOLV Engine.

Converts approved URS dictionaries and Validation Reports
into professional PDFs with a Manifestation of Signature
page for 21 CFR Part 11 compliance.

:requirement: URS-7.3 - Output URS as formatted document.
:requirement: URS-18.1 - Generate combined Validation Report.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from fpdf import FPDF


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
            0, 10, "EVOLV  |  Validation Engine", align="L",
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
    # Page 1 — URS Document
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
    # Page 2 — Manifestation of Signature
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
            0, 10, "EVOLV  |  Validation Engine",
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
    # Page 1 — Cover (Portrait)
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
    # Page 2 — UR/FR Table (Landscape)
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
    # Page 3 — Test Script Table (Landscape)
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
    # Page 4 — Regulatory Justification (Portrait)
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
    # Page 5 — Manifestation of Signature (Portrait)
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
