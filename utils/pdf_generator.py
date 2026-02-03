"""
URS PDF Generator.

Converts an approved URS dictionary into a professional PDF
with a Manifestation of Signature page for 21 CFR Part 11
compliance.

:requirement: URS-7.3 - Output URS as formatted document.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

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
            0, 10, "TRUSTME AI  |  CSV Engine", align="L",
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
        "This document was generated by the Trustme AI "
        "CSV Engine. Per 21 CFR Part 11, electronic "
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
