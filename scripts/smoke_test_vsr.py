#!/usr/bin/env python3
"""
Smoke test for _generate_vsr_pdf.

Extracts the function from frontend/app.py, executes it with
representative test data — including bullet •, em-dash —, smart
quotes, and ellipsis … to verify Helvetica encoding safety — and
writes the PDF to output/smoke_vsr_test.pdf.

Run from project root:
    python scripts/smoke_test_vsr.py
"""
import sys
import textwrap
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 1. Extract _generate_vsr_pdf from app.py ──────────────────────
APP_PY = PROJECT_ROOT / "frontend" / "app.py"
src_lines = APP_PY.read_text(
    encoding="utf-8", errors="replace"
).splitlines()

fn_start = next(
    i for i, ln in enumerate(src_lines)
    if ln.strip().startswith("def _generate_vsr_pdf(")
)
fn_end = next(
    i for i, ln in enumerate(src_lines)
    if "return bytes(pdf.output())" in ln and i > fn_start
) + 1  # inclusive

fn_src = textwrap.dedent(
    "\n".join(src_lines[fn_start:fn_end])
)

_ns: dict = {"datetime": datetime}
exec(compile(fn_src, "<_generate_vsr_pdf>", "exec"), _ns)
_generate_vsr_pdf = _ns["_generate_vsr_pdf"]

print(f"Extracted _generate_vsr_pdf "
      f"(lines {fn_start + 1}–{fn_end}).")

# ── 2. Test data — covers all paths incl. adversarial ─────────────
TS_NOW = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

TEST_UR_FR = {
    "urs_id": "URS-SMOKE-1",
    "requirement_summary": (
        "System shall track warehouse temperature."
    ),
    "category": "Environmental Monitoring",
    "user_requirement": {
        "ur_id": "UR-1",
        "statement": (
            "As a Lab Technician, the system shall "
            "track warehouse temperature so that "
            "cold-chain integrity is assured."
        ),
        "risk_assessment": "GxP Indirect",
        "implementation_method": "Configured",
        "risk_level": "High",
        "test_strategy": "OQ and/or UAT",
        "risk_note": "Final risk profiling subject to QA sign-off.",
    },
    "functional_requirements": [
        {
            "fr_id": "FR-1",
            "parent_ur_id": "UR-1",
            "statement": (
                "The system shall record temperature "
                "readings every 15 minutes."
            ),
            "acceptance_criteria": [
                "Given a sensor is active, "
                "When 15 minutes elapse, "
                "Then a timestamped reading is logged."
            ],
        },
        {
            "fr_id": "FR-2",
            "parent_ur_id": "UR-1",
            "statement": (
                "The system shall alert if temperature "
                "exceeds the configured threshold."
            ),
            "acceptance_criteria": [
                "Given threshold is 8°C, "
                "When temp > 8°C, "
                "Then an alert is raised within 60s."
            ],
        },
    ],
    "compliance_notes": [
        "Cross-reference SOP-436231.",
        "21 CFR Part 11 audit trail required.",
        "GAMP 5 Rev 2 \u00a7 7.4 temperature monitoring.",
    ],
    "reg_versions_cited": ["GAMP5_Rev2"],
    "assumptions_and_dependencies": [
        "Sensor hardware calibrated per SOP-112.",
    ],
}

TEST_SCRIPT = {
    "script_id": "TS-URS-SMOKE-1",
    "urs_id": "URS-SMOKE-1",
    "ur_id": "UR-1",
    "test_type": "Informal",
    "risk_level": "High",
    "test_strategy": "OQ and/or UAT",
    "generated_at": TS_NOW,
    "steps": [
        {
            "step_type": "Setup",
            "step_number": 1,
            "step_title": "Login as System Owner",
            "step_instruction": "Log into the application.",
            "expected_result": "",
            "test_case_type": "",
            "requirement_reference": "",
        },
        {
            "step_type": "Execution",
            "step_number": 1,
            "step_title": "Verify FR-1 \u2014 Positive",
            "step_instruction": (
                "Connect sensor \u2022 wait 15 min "
                "\u2026 verify log entry."
            ),
            "expected_result": (
                "Temperature reading logged with "
                "timestamp \u2265 current UTC."
            ),
            "test_case_type": "Positive",
            "requirement_reference": "UR-1 / FR-1",
        },
        {
            "step_type": "Execution",
            "step_number": 2,
            "step_title": "Verify FR-1 \u2014 Negative",
            "step_instruction": (
                "Disconnect sensor; attempt to submit "
                "reading with null value."
            ),
            "expected_result": (
                "System rejects with CSV-001 "
                "validation error."
            ),
            "test_case_type": "Negative",
            "requirement_reference": "UR-1 / FR-1",
        },
        {
            "step_type": "Execution",
            "step_number": 3,
            "step_title": "Verify FR-2 \u2014 Edge Case",
            "step_instruction": (
                "Set threshold to 8\u00b0C; inject "
                "8.001\u00b0C reading."
            ),
            "expected_result": (
                "Alert fires within 60 seconds."
            ),
            "test_case_type": "Edge_Case",
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

TEST_RTM = {
    "rtm_id": "RTM-SMOKE-1",
    "coverage_percentage": 100,
    "total_requirements": 2,
    "covered_requirements": 2,
    "gap_requirements": 0,
}

# Adversarial data with Unicode traps to exercise _sanitize()
TEST_ADVERSARIAL = {
    "adversarial_mode": True,
    "stress_tests": [
        {
            "scenario_id": "ST-1",
            "type": "Boundary Analysis",
            "title": (
                "Null / Empty Input for: "
                "record temperature readings \u2022 every 15 min"
            ),
            "description": "Submit null\u2026 empty\u2026 max-length.",
            "failure_mode": (
                "Silent acceptance \u2014 corrupts "
                "audit trail completeness."
            ),
        },
        {
            "scenario_id": "ST-2",
            "type": "Adversarial Input",
            "title": "Corrupted / Biased Data Injection",
            "description": (
                "Inject SQL escapes \u201cor\u201d Unicode surrogates."
            ),
            "failure_mode": (
                "Unsanitised input violates "
                "21 CFR Part 11 audit integrity."
            ),
        },
        {
            "scenario_id": "ST-3",
            "type": "Failure Mode",
            "title": (
                "Model Confidence Degradation \u2013 High Load"
            ),
            "description": "Contradictory statements under load.",
            "failure_mode": (
                "Risk misclassification \u2265 threshold "
                "reaches production."
            ),
        },
        {
            "scenario_id": "NEG-1",
            "type": "Negative Testing",
            "title": "System Rejection of Invalid Input",
            "description": (
                "Invalid field combinations \u2026 missing mandatory "
                "fields \u2022 type mismatches."
            ),
            "failure_mode": (
                "Partial acceptance violates "
                "21 CFR Part 11 data integrity."
            ),
        },
        {
            "scenario_id": "DRIFT-1",
            "type": "Data Drift",
            "title": "Out-of-Range Value Handling",
            "description": (
                "Values \u2265 acceptable range for "
                "temperature tracking."
            ),
            "failure_mode": (
                "Silent drift invalidates calibration "
                "records \u2264 QC threshold."
            ),
        },
    ],
    "assurance_confidence_score": 90,
    "score_rationale": (
        "Base 60 + High risk path (+10) "
        "\u22652 FRs (+10) + AC present (+10) "
        "\u2192 capped at 95 \u21920 90"
    ),
    "generated_at": TS_NOW,
}

# ── 3. Run the generator — three variants ─────────────────────────
OUT_DIR = PROJECT_ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

tests = [
    (
        "standard (no adversarial)",
        TEST_UR_FR, TEST_SCRIPT, TEST_RTM, None,
        OUT_DIR / "smoke_vsr_standard.pdf",
    ),
    (
        "with adversarial data",
        TEST_UR_FR, TEST_SCRIPT, TEST_RTM, TEST_ADVERSARIAL,
        OUT_DIR / "smoke_vsr_adversarial.pdf",
    ),
    (
        "minimal (None inputs)",
        None, None, None, None,
        OUT_DIR / "smoke_vsr_minimal.pdf",
    ),
]

def _p(msg: str) -> None:
    """Print safely on Windows cp1252 terminals."""
    sys.stdout.buffer.write(
        (msg + "\n").encode("utf-8", errors="replace")
    )
    sys.stdout.buffer.flush()


all_ok = True
for label, ur_fr, ts, rtm, adv, out_path in tests:
    try:
        pdf_bytes = _generate_vsr_pdf(
            ur_fr, ts, rtm,
            adversarial_result=adv,
        )
        out_path.write_bytes(pdf_bytes)
        _p(f"  PASS  [{label}]  "
           f"{len(pdf_bytes):,} bytes  ->  {out_path.name}")
    except Exception as exc:
        import traceback
        _p(f"  FAIL  [{label}]  "
           f"{type(exc).__name__}: "
           f"{ascii(str(exc))}")
        _p(traceback.format_exc())
        all_ok = False

_p("")
if all_ok:
    _p("All variants passed. PDFs written to output/.")
else:
    _p("One or more variants FAILED -- see above.")
    sys.exit(1)
