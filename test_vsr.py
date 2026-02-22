"""
VSR end-to-end smoke test.
Exercises data pipeline, badge logic, and full PDF generation.
Run: python test_vsr.py
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ── Demo data mirroring app.py DEMO_DATA ─────────────────────────
DEMO_UR_FR = {
    "urs_id": "URS-7.1",
    "requirement_summary": "Track warehouse temperature.",
    "category": "General",
    "user_requirement": {
        "ur_id": "UR-1",
        "statement": (
            "As a Lab Technician, the system shall track "
            "warehouse temperature so that GxP compliance "
            "is maintained."
        ),
        "risk_assessment": "GxP Indirect",
        "implementation_method": "Configured",
        "risk_level": "High",
        "test_strategy": "OQ and/or UAT",
        "risk_note": "Final risk profiling with stakeholders.",
    },
    "functional_requirements": [
        {
            "fr_id": "FR-1",
            "parent_ur_id": "UR-1",
            "statement": "The system shall record temperature readings.",
            "acceptance_criteria": [
                "Given a sensor reading, when logged, "
                "then the value is stored with timestamp."
            ],
        },
        {
            "fr_id": "FR-2",
            "parent_ur_id": "UR-1",
            "statement": "The system shall alert on threshold breach.",
            "acceptance_criteria": [
                "Given temp > 25C, when detected, "
                "then alert is raised within 60s."
            ],
        },
    ],
    "assumptions_and_dependencies": [
        "Sensor hardware is calibrated.",
        "Network connectivity is available.",
    ],
    "compliance_notes": [
        "Cross-reference SOP-436231.",
        "21 CFR Part 11 audit trail required.",
    ],
    "implementation_notes": ["Configured via admin panel."],
    "reg_versions_cited": ["GAMP5_Rev2"],
}

DEMO_TS = {
    "script_id": "TS-URS-7.1",
    "urs_id": "URS-7.1",
    "ur_id": "UR-1",
    "test_type": "Informal",
    "risk_level": "High",
    "test_strategy": "OQ and/or UAT",
    "generated_at": datetime.utcnow().isoformat(),
    "steps": [
        {
            "step_type": "Setup", "step_number": 1,
            "step_title": "Login as System Owner",
            "step_instruction": "Log into the application.",
            "expected_result": "", "test_case_type": "",
            "requirement_reference": "",
        },
        {
            "step_type": "Execution", "step_number": 1,
            "step_title": "Verify FR-1 Positive",
            "step_instruction": "Record a valid temperature.",
            "expected_result": "Value stored with timestamp.",
            "test_case_type": "Positive",
            "requirement_reference": "UR-1 / FR-1",
        },
        {
            "step_type": "Execution", "step_number": 2,
            "step_title": "Verify FR-1 Negative",
            "step_instruction": "Submit empty value.",
            "expected_result": "Validation error shown.",
            "test_case_type": "Negative",
            "requirement_reference": "UR-1 / FR-1",
        },
        {
            "step_type": "Execution", "step_number": 3,
            "step_title": "Verify FR-2 Edge Case",
            "step_instruction": "Set temp exactly at 25C.",
            "expected_result": "No alert raised (boundary).",
            "test_case_type": "Edge_Case",
            "requirement_reference": "UR-1 / FR-2",
        },
        {
            "step_type": "Execution", "step_number": 4,
            "step_title": "Verify FR-2 Positive",
            "step_instruction": "Set temp to 26C.",
            "expected_result": "Alert raised within 60s.",
            "test_case_type": "Positive",
            "requirement_reference": "UR-1 / FR-2",
        },
    ],
    "quality_checklist": {
        "steps_clear_and_sequential": True,
        "expected_results_observable": True,
        "execution_steps_have_references": True,
        "test_types_assigned": True,
        "no_redundant_steps": True,
    },
}

DEMO_RTM = {
    "rtm_id": "RTM-URS-7.1",
    "urs_id": "URS-7.1",
    "test_script_id": "TS-URS-7.1",
    "risk_level": "High",
    "total_requirements": 2,
    "covered_requirements": 2,
    "gap_requirements": 0,
    "coverage_percentage": 100,
    "rows": [
        {
            "urs_id": "URS-7.1", "ur_id": "UR-1",
            "fr_id": "FR-1",
            "requirement_statement": "Record temperature readings.",
            "test_script_id": "TS-URS-7.1",
            "test_steps": 2,
            "test_case_types": ["Positive", "Negative"],
            "coverage_status": "Covered",
        },
        {
            "urs_id": "URS-7.1", "ur_id": "UR-1",
            "fr_id": "FR-2",
            "requirement_statement": "Alert on threshold breach.",
            "test_script_id": "TS-URS-7.1",
            "test_steps": 2,
            "test_case_types": ["Positive", "Edge_Case"],
            "coverage_status": "Covered",
        },
    ],
}


# ── 1. Derived values (mirrors Page 10 logic) ─────────────────────
def test_derived_values():
    print("=== 1. Derived Values ===")
    _risk    = DEMO_UR_FR["user_requirement"]["risk_level"]
    _is_high = _risk.lower() == "high"
    _cov     = DEMO_RTM["coverage_percentage"]
    _steps   = DEMO_TS["steps"]
    _pos     = sum(1 for s in _steps if s.get("test_case_type") == "Positive")
    _neg     = sum(1 for s in _steps if s.get("test_case_type") == "Negative")
    _edge    = sum(1 for s in _steps if s.get("test_case_type") == "Edge_Case")
    _setup   = sum(1 for s in _steps if s.get("step_type") == "Setup")
    _exec    = len(_steps) - _setup
    _adv     = round((_neg + _edge) / max(_exec, 1) * 100)

    print(f"  Risk level      : {_risk}")
    print(f"  Is High Risk    : {_is_high}")
    print(f"  Coverage        : {_cov}%")
    print(f"  Total steps     : {len(_steps)}")
    print(f"  Positive        : {_pos}")
    print(f"  Negative        : {_neg}")
    print(f"  Edge cases      : {_edge}")
    print(f"  Adversarial cov : {_adv}%")

    assert _is_high, "Expected High risk"
    assert _cov == 100, "Expected 100% coverage"
    assert _pos == 2, f"Expected 2 positive, got {_pos}"
    assert _neg == 1, f"Expected 1 negative, got {_neg}"
    assert _edge == 1, f"Expected 1 edge case, got {_edge}"
    assert _adv == 50, f"Expected 50% adversarial, got {_adv}"
    print("  [PASS]")
    return _risk, _is_high, _cov


# ── 2. Section registry + badge logic ─────────────────────────────
def test_section_registry(risk, is_high, cov):
    print("\n=== 2. Section Registry & Badge Logic ===")
    sections = [
        ("validation-summary", "Validation Summary",
         DEMO_UR_FR is not None),
        ("traceability",       "Traceability Coverage",
         DEMO_RTM is not None and cov >= 80),
        ("performance",        "Performance Baseline",
         DEMO_TS is not None),
        ("drift",              "Drift Thresholds",      True),
        ("pccp",               "PCCP Roadmap",          True),
    ]
    if is_high:
        sections += [
            ("model-card",    "Model Card",          True),
            ("health-check",  "90-Day Health Check", True),
        ]

    for sid, lbl, ok in sections:
        badge = "VERIFIED        " if ok else "REVIEW REQUIRED "
        print(f"  [{badge}]  {lbl}")

    assert len(sections) == 7, (
        f"Expected 7 sections (High Risk), got {len(sections)}"
    )
    assert all(ok for _, _, ok in sections), (
        "Some sections show Review Required with full demo data"
    )
    print("  [PASS] All 7 sections present, all VERIFIED")
    return sections


# ── 3. GxP PDF generation ─────────────────────────────────────────
def _make_pdf(vsr_ur_fr, vsr_ts, vsr_rtm):
    _risk2   = (vsr_ur_fr or {}).get("user_requirement", {}).get("risk_level", "Unknown")
    _urs_id2 = (vsr_ur_fr or {}).get("urs_id", "-")
    _ts_now2 = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    class _VSRPDF(FPDF):
        def header(self):
            _eff = self.w - self.l_margin - self.r_margin
            _hw  = _eff / 2
            _hy  = self.get_y()
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(5, 102, 150)
            self.set_xy(self.l_margin, _hy)
            self.cell(_hw, 6, "EVOLV | The Validation Factory",
                      new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(120, 120, 120)
            self.set_xy(self.l_margin + _hw, _hy)
            self.cell(_hw, 6, f"VSR - {_urs_id2} | {_ts_now2}",
                      align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_draw_color(5, 102, 150)
            self.line(self.l_margin, self.get_y(),
                      self.w - self.r_margin, self.get_y())
            self.ln(3)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8,
                      f"Page {self.page_no()} | EVOLV | CONFIDENTIAL",
                      align="C")

    pdf = _VSRPDF(orientation="P", unit="mm", format="A4")
    pdf.compress = False          # keep streams readable for byte assertions
    pdf.set_margins(18, 24, 18)
    pdf.set_auto_page_break(True, margin=18)

    def _h1(t):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(5, 102, 150)
        pdf.cell(0, 8, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(5, 102, 150)
        pdf.line(pdf.l_margin, pdf.get_y(),
                 pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 10)

    def _h2(t):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 9)

    def _kv(k, v):
        _kw = 52
        _vw = pdf.w - pdf.l_margin - pdf.r_margin - _kw
        _x0, _y0 = pdf.l_margin, pdf.get_y()
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(_x0, _y0)
        pdf.multi_cell(_kw, 5.5, k + ":")
        _y1 = pdf.get_y()
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(_x0 + _kw, _y0)
        pdf.multi_cell(_vw, 5.5, str(v))
        pdf.set_y(max(_y1, pdf.get_y()))

    def _body(t):
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 5, str(t))
        pdf.ln(1)

    pages = []

    # Cover
    pdf.add_page(); pages.append("Cover")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(5, 102, 150)
    pdf.ln(12)
    pdf.cell(0, 11, "Validation Summary Report",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, "Record of Assurance",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.set_text_color(30, 30, 30)
    _kv("URS ID", _urs_id2)
    _kv("Risk Level", _risk2)
    _kv("Framework", "GAMP 5 Rev 2 | 21 CFR Part 11 | CSA")
    _kv("Generated", _ts_now2)

    # Validation Summary
    pdf.add_page(); pages.append("Validation Summary")
    _h1("1. Validation Summary")
    if vsr_ur_fr:
        _ur = vsr_ur_fr.get("user_requirement", {})
        _kv("UR ID", _ur.get("ur_id", "-"))
        _kv("Risk Assessment", _ur.get("risk_assessment", "-"))
        _kv("Implementation", _ur.get("implementation_method", "-"))
        _kv("Test Strategy", _ur.get("test_strategy", "-"))
        _body(f"Statement: {_ur.get('statement', '-')}")
        _h2("Functional Requirements")
        for fr in vsr_ur_fr.get("functional_requirements", []):
            _body(f"  {fr.get('fr_id','')}: {fr.get('statement','')}")
        _h2("Compliance Notes")
        for n in vsr_ur_fr.get("compliance_notes", []):
            _body(f"  {n}")

    # Traceability
    pdf.add_page(); pages.append("Traceability Coverage")
    _h1("2. Traceability Coverage")
    if vsr_rtm:
        _kv("RTM ID",    vsr_rtm.get("rtm_id", "-"))
        _kv("Coverage",  f"{vsr_rtm.get('coverage_percentage', 0)}%")
        _kv("Total FRs", str(vsr_rtm.get("total_requirements", 0)))
        _kv("Covered",   str(vsr_rtm.get("covered_requirements", 0)))
        _kv("Gaps",      str(vsr_rtm.get("gap_requirements", 0)))

    # Performance Baseline
    pdf.add_page(); pages.append("Performance Baseline")
    _h1("3. Performance Baseline")
    if vsr_ts:
        _st2  = vsr_ts.get("steps", [])
        _p2   = sum(1 for s in _st2 if s.get("test_case_type") == "Positive")
        _n2   = sum(1 for s in _st2 if s.get("test_case_type") == "Negative")
        _e2   = sum(1 for s in _st2 if s.get("test_case_type") == "Edge_Case")
        _su2  = sum(1 for s in _st2 if s.get("step_type") == "Setup")
        _ex2  = len(_st2) - _su2
        _ad2  = round((_n2 + _e2) / max(_ex2, 1) * 100)
        _kv("Script ID",   vsr_ts.get("script_id", "-"))
        _kv("Total Steps", str(len(_st2)))
        _kv("Positive",    str(_p2))
        _kv("Negative",    str(_n2))
        _kv("Edge Cases",  str(_e2))
        _kv("Adversarial", f"{_ad2}%")
        _h2("Quality Checklist")
        for qk, qv in vsr_ts.get("quality_checklist", {}).items():
            _body(f"[{'PASS' if qv else 'FAIL'}] "
                  f"{qk.replace('_', ' ').title()}")

    # Drift Thresholds
    pdf.add_page(); pages.append("Drift Thresholds")
    _h1("4. Drift Thresholds")
    _cw2 = [28, 28, 30, 54]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(225, 238, 248)
    for i, h in enumerate(
        ["Risk Level", "Drift Limit", "Re-validate", "Strategy"]
    ):
        pdf.cell(_cw2[i], 6, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for rl, dl, rv, st in [
        ("High",   "<=5%",  "90 days",  "Rigorous"),
        ("Medium", "<=10%", "180 days", "Hybrid"),
        ("Low",    "<=20%", "365 days", "Unscripted"),
    ]:
        if rl.lower() == _risk2.lower():
            pdf.set_fill_color(195, 228, 248)
        else:
            pdf.set_fill_color(255, 255, 255)
        for i, cv in enumerate([rl, dl, rv, st]):
            pdf.cell(_cw2[i], 6, cv, border=1, fill=True)
        pdf.ln()

    # PCCP Roadmap
    pdf.add_page(); pages.append("PCCP Roadmap")
    _h1("5. PCCP Roadmap")
    for mq, md in [
        ("Q1 - Month 1", "Baseline validation, UAT sign-off"),
        ("Q2", "Drift assessment, CAPA if threshold breached"),
        ("Q3", "Mid-cycle audit, corrective action review"),
        ("Q4", "Annual re-validation, PCCP update"),
    ]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(pdf.l_margin, pdf.get_y())
        pdf.cell(34, 5.5, mq + ":",
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 8)
        _vw2 = pdf.w - pdf.l_margin - pdf.r_margin - 34
        _y02 = pdf.get_y()
        _x02 = pdf.get_x()
        pdf.set_xy(_x02, _y02)
        pdf.multi_cell(_vw2, 5.5, md)

    # Model Card + Health Check (High Risk only)
    if _risk2.lower() == "high":
        pdf.add_page(); pages.append("Model Card")
        _h1("6. Model Card")
        _kv("System",    "EVOLV Validation Factory")
        _kv("Version",   "0.1.0")
        _kv("Risk Class", f"{_risk2} (GAMP 5 Cat. 5)")
        _kv("Framework", "GAMP 5 Rev 2 | 21 CFR Part 11 | ICH Q10")
        _h2("Limitations")
        for lim in [
            "Output requires qualified human review before submission.",
            "Not a substitute for Qualified Person (QP) oversight.",
            "Re-ingest knowledge base after regulatory updates.",
        ]:
            _body(f"  {lim}")

        pdf.add_page(); pages.append("90-Day Health Check")
        _h1("7. 90-Day Health Check Schedule")
        for wk, wt in [
            ("Week 1",  "Establish performance baseline"),
            ("Week 4",  "First drift measurement (<=5%)"),
            ("Week 8",  "Corrective action review"),
            ("Week 12", "Full re-validation + new VSR for QA"),
        ]:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(pdf.l_margin, pdf.get_y())
            pdf.cell(26, 5.5, wk + ":",
                     new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Helvetica", "", 8)
            _vw3 = pdf.w - pdf.l_margin - pdf.r_margin - 26
            pdf.set_xy(pdf.get_x(), pdf.get_y())
            pdf.multi_cell(_vw3, 5.5, wt)

    # E-Signature Placeholders
    pdf.add_page(); pages.append("E-Signature")
    _h1("Electronic Signature - Manifestation")
    _body(
        "In accordance with 21 CFR Part 11, the following "
        "signatures constitute legally binding approval of "
        "this Validation Summary Report."
    )
    pdf.ln(4)
    for sn, sr in [
        ("Document Author",     "Validation Engineer"),
        ("Quality Reviewer",    "Quality Assurance Lead"),
        ("System Owner",        "IT / Operations Lead"),
        ("Regulatory Approver", "Regulatory Affairs"),
    ]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, sn, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 5, f"Role: {sr}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(2)
        _sx2 = pdf.l_margin
        _sy2 = pdf.get_y() + 4
        pdf.set_draw_color(120, 120, 120)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(_sx2, pdf.get_y())
        pdf.cell(22, 5, "Signature:",
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.line(_sx2 + 22, _sy2, _sx2 + 90, _sy2)
        pdf.set_xy(_sx2 + 95, pdf.get_y())
        pdf.cell(16, 5, "Date:",
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.line(_sx2 + 111, _sy2, _sx2 + 150, _sy2)
        pdf.ln(10)

    return bytes(pdf.output()), pages


def test_pdf_generation():
    print("\n=== 3. GxP PDF Generation ===")
    result, pages = _make_pdf(DEMO_UR_FR, DEMO_TS, DEMO_RTM)

    print(f"  Pages built     : {len(pages)}")
    for p in pages:
        print(f"    - {p}")
    print(f"  PDF size        : {len(result):,} bytes")

    assert result[:4] == b"%PDF", "Not a valid PDF"
    assert b"EVOLV" in result
    assert b"Validation Summary Report" in result
    assert b"PCCP Roadmap" in result
    assert b"90-Day Health Check" in result
    assert b"Model Card" in result
    assert b"Signature:" in result
    assert len(pages) == 9, (
        f"Expected 9 pages (High Risk), got {len(pages)}: {pages}"
    )
    print("  Content checks  : brand, all sections, sig page [OK]")

    import tempfile
    tmp = tempfile.mktemp(suffix=".pdf")
    with open(tmp, "wb") as f:
        f.write(result)
    print(f"  Saved to        : {tmp}")
    return tmp


# ── 4. Edge case: Low Risk (no Model Card / Health Check) ─────────
def test_low_risk_pdf():
    print("\n=== 4. Low Risk PDF (no auto-attach sections) ===")
    low_ur_fr = {
        **DEMO_UR_FR,
        "user_requirement": {
            **DEMO_UR_FR["user_requirement"],
            "risk_level": "Low",
        },
    }
    result, pages = _make_pdf(low_ur_fr, DEMO_TS, DEMO_RTM)
    assert b"Model Card" not in result, (
        "Model Card should NOT appear for Low Risk"
    )
    assert b"90-Day Health Check" not in result, (
        "Health Check should NOT appear for Low Risk"
    )
    print(f"  Pages built     : {len(pages)}")
    print("  Model Card absent for Low Risk     [OK]")
    print("  90-Day Health Check absent         [OK]")


# ── 5. Edge case: missing RTM (partial data) ──────────────────────
def test_missing_rtm():
    print("\n=== 5. Partial Data (no RTM) ===")
    result, pages = _make_pdf(DEMO_UR_FR, DEMO_TS, None)
    assert result[:4] == b"%PDF"
    print(f"  PDF generated with no RTM: {len(result):,} bytes [OK]")


# ── Run all ───────────────────────────────────────────────────────
if __name__ == "__main__":
    risk, is_high, cov = test_derived_values()
    test_section_registry(risk, is_high, cov)
    pdf_path = test_pdf_generation()
    test_low_risk_pdf()
    test_missing_rtm()
    print("\n" + "=" * 44)
    print("  ALL TESTS PASSED")
    print("=" * 44)
    print(f"\n  Open the PDF to visually inspect:")
    print(f"  {pdf_path}")
