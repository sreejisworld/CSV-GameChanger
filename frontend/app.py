"""
Trustme AI - CSV-GameChanger Frontend.

Streamlit dashboard for the GAMP 5 / CSA compliant CSV Engine.
Provides a professional enterprise UI for document ingestion,
requirements generation, risk assessment, and audit log review.

:requirement: URS-1.1 - System shall accept change requests.
"""
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from datetime import datetime

# -------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Trustme AI - CSV Engine",
    page_icon="\u2666",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# Enterprise theme CSS
# -------------------------------------------------------------------
NAVY = "#1B2A4A"
NAVY_LIGHT = "#2C3E6B"
ACCENT = "#3B82F6"
BORDER = "#D1D5DB"
BG_CARD = "#F8F9FB"

st.markdown(
    f"""
    <style>
    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {{
        background-color: {NAVY};
    }}
    section[data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.15);
    }}
    section[data-testid="stSidebar"]
        div[data-testid="stRadio"] label {{
        font-size: 0.95rem;
    }}
    section[data-testid="stSidebar"]
        div[data-testid="stRadio"]
        div[role="radiogroup"] label[data-baseweb="radio"]
        div:first-child {{
        background-color: {NAVY_LIGHT};
        border-color: rgba(255,255,255,0.3);
    }}

    /* ---- Main content cards ---- */
    div.stMetric {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 1rem;
    }}

    /* ---- Header bar ---- */
    .main-header {{
        background: linear-gradient(135deg, {NAVY}, {NAVY_LIGHT});
        padding: 1.2rem 1.6rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }}
    .main-header h2 {{
        color: #FFFFFF;
        margin: 0;
        font-weight: 600;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.75);
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }}

    /* ---- Status badges ---- */
    .badge {{
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    .badge-high {{
        background-color: #FEE2E2;
        color: #991B1B;
    }}
    .badge-medium {{
        background-color: #FEF3C7;
        color: #92400E;
    }}
    .badge-low {{
        background-color: #D1FAE5;
        color: #065F46;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
AUDIT_CSV = PROJECT_ROOT / "output" / "audit_trail.csv"
URS_DIR = PROJECT_ROOT / "output" / "urs"
VENDOR_DIR = PROJECT_ROOT / "input" / "vendor_docs"

# -------------------------------------------------------------------
# Demo Mode: sample LIMS data (no API/Pinecone calls needed)
# -------------------------------------------------------------------
DEMO_DATA = {
    "ingest_result": {
        "title": "LabCore LIMS v4.2 — Functional Specification",
        "total_pages": 87,
        "sections": [
            {
                "section_index": 1,
                "heading": "Sample Management",
                "page_number": 5,
                "content": (
                    "The system shall register, track, and "
                    "dispose of laboratory samples with full "
                    "chain-of-custody from receipt to disposal."
                ),
            },
            {
                "section_index": 2,
                "heading": "Instrument Integration",
                "page_number": 18,
                "content": (
                    "Bi-directional interfaces with analytical "
                    "instruments (HPLC, GC-MS, ICP) shall "
                    "capture raw data automatically."
                ),
            },
            {
                "section_index": 3,
                "heading": "Audit Trail",
                "page_number": 34,
                "content": (
                    "An append-only, tamper-evident audit trail "
                    "shall record every data creation, "
                    "modification, and deletion event per "
                    "21 CFR Part 11."
                ),
            },
            {
                "section_index": 4,
                "heading": "Electronic Signatures",
                "page_number": 41,
                "content": (
                    "The system shall support two-component "
                    "electronic signatures (user ID + password) "
                    "with configurable signature meanings."
                ),
            },
            {
                "section_index": 5,
                "heading": "Results Entry & Review",
                "page_number": 52,
                "content": (
                    "Analysts shall enter results which are "
                    "routed to a second reviewer for approval "
                    "before release."
                ),
            },
            {
                "section_index": 6,
                "heading": "Stability Studies",
                "page_number": 63,
                "content": (
                    "The module shall schedule pull dates, "
                    "track storage conditions, and flag "
                    "out-of-trend results automatically."
                ),
            },
        ],
        "requirements": [
            "Full chain-of-custody tracking for all samples",
            "Bi-directional instrument data capture",
            "21 CFR Part 11 compliant audit trail",
            "Two-component electronic signatures",
            "Dual-review workflow for results release",
            "Automated stability study scheduling",
        ],
    },
    "gap_result": {
        "total_categories": 8,
        "covered": 4,
        "gaps": 4,
        "summary": (
            "LabCore LIMS v4.2 covers core data integrity and "
            "audit trail requirements but has gaps in change "
            "control documentation, user access governance, "
            "and disaster recovery procedures."
        ),
        "findings": [
            {
                "category": "Change Control",
                "status": "Missing",
                "vendor_evidence": (
                    "No change control SOP referenced in "
                    "vendor documentation."
                ),
                "gamp5_reference": (
                    "GAMP 5 Appendix M4 — Change control "
                    "processes shall be documented and approved."
                ),
                "recommendation": (
                    "Request vendor change control SOP and "
                    "map to internal change management process."
                ),
            },
            {
                "category": "Audit Trail",
                "status": "Covered",
                "vendor_evidence": (
                    "Section 3 describes append-only audit "
                    "trail with user, timestamp, old/new values."
                ),
                "gamp5_reference": (
                    "GAMP 5 Appendix D7 — Audit trail shall "
                    "capture who, what, when, and why."
                ),
                "recommendation": "No action required.",
            },
            {
                "category": "Validation",
                "status": "Partial",
                "vendor_evidence": (
                    "Vendor provides IQ/OQ protocols but no "
                    "PQ template."
                ),
                "gamp5_reference": (
                    "GAMP 5 Section 7 — Validation activities "
                    "shall include IQ, OQ, and PQ."
                ),
                "recommendation": (
                    "Develop PQ protocol internally; request "
                    "vendor support for PQ test cases."
                ),
            },
            {
                "category": "User Access",
                "status": "Missing",
                "vendor_evidence": (
                    "Role-based access mentioned but no "
                    "privilege matrix provided."
                ),
                "gamp5_reference": (
                    "GAMP 5 Appendix D4 — Access controls "
                    "shall restrict functionality by role."
                ),
                "recommendation": (
                    "Request detailed role/privilege matrix "
                    "from vendor."
                ),
            },
            {
                "category": "Data Integrity",
                "status": "Covered",
                "vendor_evidence": (
                    "ALCOA+ principles referenced; data "
                    "checksums implemented."
                ),
                "gamp5_reference": (
                    "GAMP 5 Appendix D7 — Data shall be "
                    "attributable, legible, contemporaneous, "
                    "original, and accurate."
                ),
                "recommendation": "No action required.",
            },
            {
                "category": "Training",
                "status": "Covered",
                "vendor_evidence": (
                    "Vendor offers role-based training and "
                    "competency assessment."
                ),
                "gamp5_reference": (
                    "GAMP 5 Section 10 — Personnel shall be "
                    "trained and competency documented."
                ),
                "recommendation": "No action required.",
            },
            {
                "category": "Risk Management",
                "status": "Partial",
                "vendor_evidence": (
                    "Risk assessment mentioned in overview "
                    "but no FMEA or risk matrix provided."
                ),
                "gamp5_reference": (
                    "GAMP 5 Section 5 — A documented risk "
                    "management process shall be applied."
                ),
                "recommendation": (
                    "Perform independent risk assessment "
                    "using FMEA methodology."
                ),
            },
            {
                "category": "Backup & Recovery",
                "status": "Covered",
                "vendor_evidence": (
                    "Daily encrypted backups with documented "
                    "RTO of 4 hours and RPO of 1 hour."
                ),
                "gamp5_reference": (
                    "GAMP 5 Appendix D5 — Backup and "
                    "restore procedures shall be validated."
                ),
                "recommendation": "No action required.",
            },
        ],
    },
    "generated_urs": {
        "URS_ID": "URS-9.1",
        "Requirement_Statement": (
            "The LIMS shall maintain a complete, immutable "
            "chain-of-custody record for every laboratory "
            "sample from receipt through testing, storage, "
            "and disposal, including custodian identity, "
            "timestamp, location, and condition at each "
            "transfer point."
        ),
        "Criticality": "High",
        "Regulatory_Rationale": (
            "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.38): "
            "'Records that support product quality decisions "
            "shall be controlled to ensure integrity and "
            "traceability.' Chain-of-custody is a patient-"
            "safety-critical function as sample mix-ups can "
            "lead to incorrect release decisions."
        ),
        "Reg_Versions_Cited": ["GAMP5_Rev2"],
    },
    "risk_result": {
        "severity": "HIGH",
        "occurrence": "OCCASIONAL",
        "detectability": "MEDIUM",
        "rpn": 12,
        "risk_level": "High",
        "testing_strategy": "Rigorous Scripted Testing",
        "patient_safety_override": True,
    },
    "ur_fr": {
        "urs_id": "URS-9.1",
        "requirement_summary": (
            "The LIMS shall maintain a complete, immutable "
            "chain-of-custody record for every laboratory "
            "sample from receipt through disposal."
        ),
        "category": "Sample Management",
        "user_requirement": {
            "ur_id": "UR-1",
            "statement": (
                "As a Lab Technician, there will be a "
                "complete chain-of-custody record for every "
                "laboratory sample so that the requirement "
                "is fulfilled."
            ),
            "risk_assessment": "GxP Direct",
            "implementation_method": "Configured",
            "risk_level": "High",
            "test_strategy": "OQ and/or UAT",
            "risk_note": (
                "Final Risk Profiling will be decided "
                "with stakeholders during the validation "
                "planning phase."
            ),
        },
        "functional_requirements": [
            {
                "fr_id": "FR-1",
                "parent_ur_id": "UR-1",
                "statement": (
                    "The system shall register each "
                    "incoming sample with a unique ID, "
                    "custodian, timestamp, and condition."
                ),
                "acceptance_criteria": [
                    "Given a new sample arrives, "
                    "When the technician scans the barcode, "
                    "Then the system records sample ID, "
                    "custodian, timestamp, and condition.",
                ],
            },
            {
                "fr_id": "FR-2",
                "parent_ur_id": "UR-1",
                "statement": (
                    "The system shall log every custody "
                    "transfer with source, destination, "
                    "timestamp, and authorising user."
                ),
                "acceptance_criteria": [
                    "Given a sample is transferred, "
                    "When the transfer is confirmed, "
                    "Then the system logs source, "
                    "destination, timestamp, and user.",
                ],
            },
            {
                "fr_id": "FR-3",
                "parent_ur_id": "UR-1",
                "statement": (
                    "The system shall prevent sample "
                    "disposal without a completed "
                    "chain-of-custody record."
                ),
                "acceptance_criteria": [
                    "Given a sample is marked for disposal, "
                    "When the chain-of-custody is incomplete, "
                    "Then the system blocks disposal and "
                    "alerts the supervisor.",
                ],
            },
        ],
        "assumptions_and_dependencies": [
            "Barcode scanners are available at all "
            "sample handling stations.",
            "User authentication is managed by the "
            "enterprise SSO system.",
        ],
        "compliance_notes": [
            "Cross-reference SOP-436231 for sample "
            "handling procedures.",
            "21 CFR Part 11 electronic records apply.",
        ],
        "implementation_notes": [
            "Configured workflow in LabCore LIMS v4.2.",
        ],
        "reg_versions_cited": ["GAMP5_Rev2"],
    },
    "test_script": {
        "script_id": "TS-URS-9.1",
        "urs_id": "URS-9.1",
        "ur_id": "UR-1",
        "test_type": "Informal",
        "risk_level": "High",
        "test_strategy": "OQ and/or UAT",
        "regulatory_justification": (
            "Per FDA General Principles of Software "
            "Validation and GAMP 5 risk-based approach, "
            "high-risk functions with direct GxP impact "
            "require rigorous scripted testing with "
            "documented evidence. "
            "EMA Annex 11 mandates that test records "
            "demonstrate complete verification of "
            "intended use for systems affecting patient "
            "safety or data integrity."
        ),
        "generated_at": "2026-02-03T08:30:00Z",
        "steps": [
            {
                "step_type": "Setup",
                "step_number": 1,
                "step_title": "Login as System Owner",
                "step_instruction": (
                    "Log into the application with valid "
                    "System Owner credentials."
                ),
                "expected_result": "",
                "test_case_type": "",
                "requirement_reference": "",
            },
            {
                "step_type": "Setup",
                "step_number": 2,
                "step_title": (
                    "Navigate to Sample Management module"
                ),
                "step_instruction": (
                    "Navigate to the Sample Management "
                    "module from the main menu."
                ),
                "expected_result": "",
                "test_case_type": "",
                "requirement_reference": "",
            },
            {
                "step_type": "Setup",
                "step_number": 3,
                "step_title": "Prepare test data",
                "step_instruction": (
                    "Ensure at least one test sample is "
                    "available for chain-of-custody testing."
                ),
                "expected_result": "",
                "test_case_type": "",
                "requirement_reference": "",
            },
            {
                "step_type": "Execution",
                "step_number": 1,
                "step_title": "Verify FR-1 - Positive",
                "step_instruction": (
                    "Scan a new sample barcode and verify "
                    "the system records sample ID, custodian, "
                    "timestamp, and condition."
                ),
                "expected_result": (
                    "System registers sample with all "
                    "required fields populated."
                ),
                "test_case_type": "Positive",
                "requirement_reference": "UR-1 / FR-1",
            },
            {
                "step_type": "Execution",
                "step_number": 2,
                "step_title": "Verify FR-1 - Negative",
                "step_instruction": (
                    "Attempt to register a sample without "
                    "scanning a barcode."
                ),
                "expected_result": (
                    "System rejects registration and "
                    "displays a validation error."
                ),
                "test_case_type": "Negative",
                "requirement_reference": "UR-1 / FR-1",
            },
            {
                "step_type": "Execution",
                "step_number": 3,
                "step_title": "Verify FR-2 - Positive",
                "step_instruction": (
                    "Transfer a sample to another custodian "
                    "and confirm the transfer log entry."
                ),
                "expected_result": (
                    "System logs source, destination, "
                    "timestamp, and authorising user."
                ),
                "test_case_type": "Positive",
                "requirement_reference": "UR-1 / FR-2",
            },
            {
                "step_type": "Execution",
                "step_number": 4,
                "step_title": "Verify FR-2 - Negative",
                "step_instruction": (
                    "Attempt to transfer a sample without "
                    "selecting a destination custodian."
                ),
                "expected_result": (
                    "System prevents transfer and shows "
                    "mandatory field error."
                ),
                "test_case_type": "Negative",
                "requirement_reference": "UR-1 / FR-2",
            },
            {
                "step_type": "Execution",
                "step_number": 5,
                "step_title": "Verify FR-3 - Positive",
                "step_instruction": (
                    "Mark a sample with a complete "
                    "chain-of-custody for disposal."
                ),
                "expected_result": (
                    "System allows disposal and records "
                    "the disposal event."
                ),
                "test_case_type": "Positive",
                "requirement_reference": "UR-1 / FR-3",
            },
            {
                "step_type": "Execution",
                "step_number": 6,
                "step_title": "Verify FR-3 - Negative",
                "step_instruction": (
                    "Attempt to dispose a sample with an "
                    "incomplete chain-of-custody record."
                ),
                "expected_result": (
                    "System blocks disposal and alerts "
                    "the supervisor."
                ),
                "test_case_type": "Negative",
                "requirement_reference": "UR-1 / FR-3",
            },
        ],
        "quality_checklist": {
            "steps_clear_and_sequential": True,
            "expected_results_observable": True,
            "execution_steps_have_references": True,
            "test_types_assigned": True,
            "no_redundant_steps": True,
        },
    },
    "rtm": {
        "rtm_id": "RTM-URS-9.1",
        "generated_at": "2026-02-03T08:30:00Z",
        "urs_id": "URS-9.1",
        "ur_id": "UR-1",
        "test_script_id": "TS-URS-9.1",
        "risk_level": "High",
        "test_strategy": "OQ and/or UAT",
        "total_requirements": 3,
        "covered_requirements": 3,
        "gap_requirements": 0,
        "coverage_percentage": 100.0,
        "rows": [
            {
                "urs_id": "URS-9.1",
                "ur_id": "UR-1",
                "fr_id": "FR-1",
                "requirement_statement": (
                    "The system shall register each "
                    "incoming sample with a unique ID, "
                    "custodian, timestamp, and condition."
                ),
                "test_script_id": "TS-URS-9.1",
                "test_steps": (
                    "1 (Positive), 2 (Negative)"
                ),
                "test_case_types": [
                    "Negative", "Positive",
                ],
                "coverage_status": "Covered",
            },
            {
                "urs_id": "URS-9.1",
                "ur_id": "UR-1",
                "fr_id": "FR-2",
                "requirement_statement": (
                    "The system shall log every custody "
                    "transfer with source, destination, "
                    "timestamp, and authorising user."
                ),
                "test_script_id": "TS-URS-9.1",
                "test_steps": (
                    "3 (Positive), 4 (Negative)"
                ),
                "test_case_types": [
                    "Negative", "Positive",
                ],
                "coverage_status": "Covered",
            },
            {
                "urs_id": "URS-9.1",
                "ur_id": "UR-1",
                "fr_id": "FR-3",
                "requirement_statement": (
                    "The system shall prevent sample "
                    "disposal without a completed "
                    "chain-of-custody record."
                ),
                "test_script_id": "TS-URS-9.1",
                "test_steps": (
                    "5 (Positive), 6 (Negative)"
                ),
                "test_case_types": [
                    "Negative", "Positive",
                ],
                "coverage_status": "Covered",
            },
        ],
    },
    "audit_df": pd.DataFrame(
        {
            "Timestamp": [
                "2026-02-03T08:12:33Z",
                "2026-02-03T08:14:07Z",
                "2026-02-03T08:15:42Z",
                "2026-02-03T08:17:19Z",
                "2026-02-03T08:19:55Z",
                "2026-02-03T08:22:30Z",
            ],
            "Agent_Name": [
                "IngestorAgent",
                "IngestorAgent",
                "RequirementArchitect",
                "VerificationAgent",
                "RiskStrategist",
                "IntegrityManager",
            ],
            "Action_Performed": [
                "DOCUMENT_INGESTED",
                "GAP_ANALYSIS_COMPLETED",
                "URS_GENERATED",
                "URS_VERIFIED",
                "RISK_ASSESSMENT_COMPLETED",
                "LOGIC_ARCHIVE_WRITTEN",
            ],
            "User_ID": [
                "demo_user",
                "demo_user",
                "demo_user",
                "demo_user",
                "demo_user",
                "SYSTEM",
            ],
            "Decision_Logic": [
                "Ingested LabCore LIMS v4.2 spec (87 pages)",
                "8 GAMP 5 categories assessed; 4 covered, "
                "2 partial, 2 missing",
                "Generated URS-9.1 for sample chain-of-custody",
                "URS-9.1 APPROVED — all 3 checks passed",
                "RPN=12, High risk, patient safety override",
                "Archive .URS_GENERATED_20260203T081542Z.json",
            ],
            "Compliance_Impact": [
                "Regulatory Compliance",
                "Regulatory Compliance",
                "Regulatory Compliance",
                "Regulatory Compliance",
                "Regulatory Compliance",
                "Regulatory Compliance",
            ],
            "Reasoning_Hash": [
                "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
                "e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7"
                "f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
                "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"
                "a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
                "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9"
                "b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5",
                "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
                "c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
                "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1"
                "d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
            ],
        }
    ),
}

# -------------------------------------------------------------------
# Sidebar: Logo + Navigation
# -------------------------------------------------------------------
with st.sidebar:
    # Logo block
    st.markdown(
        f"""
        <div style="text-align:center; padding:1.2rem 0 0.6rem 0;">
            <div style="
                display:inline-flex; align-items:center;
                justify-content:center;
                width:56px; height:56px;
                background:linear-gradient(135deg,
                    {ACCENT}, {NAVY_LIGHT});
                border-radius:12px; margin-bottom:0.6rem;
            ">
                <span style="font-size:1.6rem;
                    color:#FFF; font-weight:700;">T</span>
            </div>
            <h3 style="margin:0; font-weight:700;
                letter-spacing:0.5px;">TRUSTME AI</h3>
            <p style="margin:0; font-size:0.75rem;
                opacity:0.65; letter-spacing:1px;">
                CSV ENGINE</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "1. Ingest Vendor Docs",
            "2. Generate Requirements",
            "3. Risk Assessment (Delta)",
            "4. Gap Analysis",
            "5. Audit Logs",
            "6. Validation Factory",
            "7. Traceability",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Environment status
    st.caption("System Status")
    api_ok = True
    try:
        from API.agent_controller import AgentController
    except Exception:
        api_ok = False

    st.markdown(
        f"API Controller: &ensp;"
        f"{'**Online**' if api_ok else '**Offline**'}"
    )
    st.markdown(
        f"Audit Trail: &ensp;"
        f"{'**Active**' if AUDIT_CSV.exists() else '**Missing**'}"
    )
    st.caption("v0.1.0")

    # ---- Demo Mode Toggle ----
    st.markdown("---")
    demo_on = st.toggle("Demo Mode", key="demo_mode")
    if demo_on:
        st.caption("Showing sample LIMS data")

    # ---- Expert Mode Toggle ----
    expert_on = st.toggle(
        "Expert Mode", key="expert_mode",
    )
    if expert_on:
        st.caption(
            "Skip doc lookup \u2014 use custom logic"
        )

    # ---- Compliance Monitor: Live Audit Feed ----
    st.markdown("---")
    st.caption("Compliance Monitor")
    st.markdown(
        '<p style="font-size:0.7rem; opacity:0.55; '
        'margin:0 0 0.4rem 0;">'
        "21 CFR Part 11 &bull; Live Audit Feed</p>",
        unsafe_allow_html=True,
    )

    if AUDIT_CSV.exists():
        try:
            _audit_df = pd.read_csv(AUDIT_CSV)
            _latest = _audit_df.tail(5).iloc[::-1]
            for _, _row in _latest.iterrows():
                _ts = str(
                    _row.get("Timestamp", "")
                )[:19]
                _agent = _row.get("Agent_Name", "-")
                _action = _row.get(
                    "Action_Performed", "-"
                )
                st.markdown(
                    f'<div style="'
                    f"background:rgba(255,255,255,0.07);"
                    f"border-left:3px solid "
                    f"rgba(59,130,246,0.6);"
                    f"border-radius:4px;"
                    f"padding:0.35rem 0.5rem;"
                    f"margin-bottom:0.35rem;"
                    f"font-size:0.72rem;"
                    f'">'
                    f"<strong>{_action}</strong><br/>"
                    f'<span style="opacity:0.7;">'
                    f"{_agent} &bull; {_ts}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            st.markdown(
                '<span style="font-size:0.75rem; '
                'opacity:0.6;">Unable to read audit trail'
                "</span>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<span style="font-size:0.75rem; '
            'opacity:0.6;">No entries yet</span>',
            unsafe_allow_html=True,
        )


# -------------------------------------------------------------------
# Helper: page header
# -------------------------------------------------------------------
def _page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="main-header">
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# Helper: build PDF from table data
# -------------------------------------------------------------------
def _build_table_pdf(
    title: str,
    columns: list,
    rows: list,
) -> bytes:
    """Build a landscape PDF with branded header.

    :param title: Table title for the PDF.
    :param columns: List of column header strings.
    :param rows: List of row tuples/lists.
    :return: PDF as bytes.
    :requirement: URS-17.5 - Produce tabular test steps.
    """
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(orientation="L", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Header
    pdf.set_fill_color(27, 42, 74)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(
        0, 12, "TRUSTME AI  |  CSV Engine",
        fill=True,
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0, 8, title, fill=True,
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(4)

    # Timestamp
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(
        0, 6,
        f"Generated: "
        f"{datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(2)

    # Column widths: distribute evenly
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    n_cols = len(columns)
    col_w = page_w / n_cols

    # Table header
    pdf.set_fill_color(27, 42, 74)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    for hdr in columns:
        pdf.cell(
            col_w, 7, hdr, border=1, fill=True,
        )
    pdf.ln()

    # Table rows
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 7)
    for row in rows:
        max_lines = 1
        cell_texts = []
        for val in row:
            txt = str(val) if val else ""
            lines = max(
                1,
                int(
                    pdf.get_string_width(txt)
                    / (col_w - 2)
                ) + 1,
            )
            max_lines = max(max_lines, lines)
            cell_texts.append(txt)
        row_h = max(6, max_lines * 5)
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        if y_start + row_h > pdf.h - 15:
            pdf.add_page()
            y_start = pdf.get_y()
        for idx, txt in enumerate(cell_texts):
            pdf.set_xy(
                x_start + idx * col_w, y_start,
            )
            pdf.multi_cell(
                col_w, 5, txt, border=1,
            )
        pdf.set_xy(
            x_start,
            max(pdf.get_y(), y_start + row_h),
        )

    # Footer
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(
        0, 5,
        "21 CFR Part 11 compliant  |  "
        "GAMP 5 / CSA Validation Engine",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    return bytes(pdf.output())


# ===================================================================
# Page 1 — Ingest Vendor Docs
# ===================================================================
if page.startswith("1"):
    _page_header(
        "Ingest Vendor Documents",
        "Upload vendor documentation for GAMP 5 gap analysis",
    )

    if st.session_state.get("demo_mode", False):
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )
        st.session_state.ingest_result = (
            DEMO_DATA["ingest_result"]
        )
        st.session_state.gap_result = (
            DEMO_DATA["gap_result"]
        )

    # Persistent state for results across reruns
    if "ingest_result" not in st.session_state:
        st.session_state.ingest_result = None
    if "gap_result" not in st.session_state:
        st.session_state.gap_result = None
    if "ingest_path" not in st.session_state:
        st.session_state.ingest_path = None

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            "Upload a vendor document",
            type=["pdf", "docx"],
            help="Accepts .pdf and .docx files. The document "
                 "will be ingested and analysed against GAMP 5.",
        )

        if uploaded is not None:
            # Save file locally
            dest = VENDOR_DIR / uploaded.name
            VENDOR_DIR.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(uploaded.getvalue())

            st.success(
                f"Uploaded **{uploaded.name}** "
                f"({uploaded.size / 1024:.1f} KB)"
            )

            # Clear stale results when a new file is uploaded
            if st.session_state.ingest_path != str(dest):
                st.session_state.ingest_result = None
                st.session_state.gap_result = None
                st.session_state.ingest_path = str(dest)

            # ---- Step 1: Ingest ----
            btn_cols = st.columns(2)
            with btn_cols[0]:
                run_ingest = st.button(
                    "Ingest Document", type="primary"
                )
            with btn_cols[1]:
                run_gap = st.button("Run Gap Analysis")

            if run_ingest:
                with st.spinner("Ingesting document..."):
                    try:
                        ctrl = AgentController()
                        st.session_state.ingest_result = (
                            ctrl.ingest_vendor_document(
                                str(dest)
                            )
                        )
                    except Exception as exc:
                        st.error(f"Ingestion failed: {exc}")

            if run_gap:
                with st.spinner(
                    "Running GAMP 5 gap analysis..."
                ):
                    try:
                        ctrl = AgentController()
                        st.session_state.gap_result = (
                            ctrl.analyze_vendor_gaps(str(dest))
                        )
                    except Exception as exc:
                        st.error(f"Gap analysis failed: {exc}")

    with col2:
        st.markdown("##### Accepted Formats")
        st.markdown(
            "- **PDF** &mdash; vendor SOPs, manuals\n"
            "- **DOCX** &mdash; specifications, protocols"
        )
        existing = (
            sorted(VENDOR_DIR.glob("*"))
            if VENDOR_DIR.exists() else []
        )
        if existing:
            st.markdown("##### Previously Uploaded")
            for f in existing[:10]:
                st.text(f.name)

    # ---- Ingestion Results ----
    ingest = st.session_state.ingest_result
    if ingest is not None:
        st.markdown("---")
        st.markdown("### Document Structure")
        im1, im2, im3 = st.columns(3)
        im1.metric("Title", ingest.get("title", "-"))
        im2.metric(
            "Pages", ingest.get("total_pages", "-")
        )
        im3.metric(
            "Sections",
            len(ingest.get("sections", [])),
        )

        sections = ingest.get("sections", [])
        if sections:
            with st.expander(
                f"Extracted Sections ({len(sections)})",
                expanded=True,
            ):
                sec_df = pd.DataFrame(sections)
                display_cols = [
                    c for c in [
                        "section_index",
                        "heading",
                        "page_number",
                        "content",
                    ]
                    if c in sec_df.columns
                ]
                if display_cols:
                    st.dataframe(
                        sec_df[display_cols],
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.dataframe(
                        sec_df,
                        use_container_width=True,
                        hide_index=True,
                    )

        reqs = ingest.get("requirements", [])
        if reqs:
            with st.expander(
                f"Extracted Requirements ({len(reqs)})"
            ):
                for i, r in enumerate(reqs, 1):
                    st.markdown(f"{i}. {r}")

        with st.expander("Raw JSON"):
            st.json(ingest)

    # ---- Gap Analysis Results ----
    gap = st.session_state.gap_result
    if gap is not None:
        st.markdown("---")
        st.markdown("### GAMP 5 Gap Analysis")

        # Summary metrics
        gm1, gm2, gm3 = st.columns(3)
        total_cat = gap.get("total_categories", 0)
        covered = gap.get("covered", 0)
        gaps_count = gap.get("gaps", 0)
        gm1.metric("Categories Assessed", total_cat)
        gm2.metric("Covered", covered)
        gm3.metric("Gaps Found", gaps_count)

        # Coverage bar
        if total_cat > 0:
            pct = int((covered / total_cat) * 100)
            bar_color = (
                "#065F46" if pct >= 80
                else "#92400E" if pct >= 50
                else "#991B1B"
            )
            st.markdown(
                f"""
                <div style="
                    background:{BORDER};
                    border-radius:6px;
                    height:24px;
                    margin:0.5rem 0 1rem 0;
                    overflow:hidden;">
                    <div style="
                        width:{pct}%;
                        height:100%;
                        background:{bar_color};
                        border-radius:6px;
                        text-align:center;
                        color:#FFF;
                        font-size:0.75rem;
                        line-height:24px;
                        font-weight:600;">
                        {pct}% covered
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        summary = gap.get("summary", "")
        if summary:
            st.info(summary)

        findings = gap.get("findings", [])
        if findings:
            with st.expander(
                f"Detailed Findings ({len(findings)})",
                expanded=True,
            ):
                # Status badge helper
                def _status_badge(status: str) -> str:
                    s = status.lower()
                    if s in ("covered", "pass", "met"):
                        cls = "badge-low"
                    elif s in ("partial", "warning"):
                        cls = "badge-medium"
                    else:
                        cls = "badge-high"
                    return (
                        f'<span class="badge {cls}">'
                        f"{status}</span>"
                    )

                for i, f in enumerate(findings):
                    cat = f.get("category", "Unknown")
                    status = f.get("status", "-")
                    badge = _status_badge(status)

                    with st.expander(
                        f"{cat}  |  {status}", expanded=False
                    ):
                        st.markdown(
                            f"**Status:** {badge}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"**Vendor Evidence:** "
                            f"{f.get('vendor_evidence', '-')}"
                        )
                        st.markdown(
                            f"**GAMP 5 Reference:** "
                            f"{f.get('gamp5_reference', '-')}"
                        )
                        st.markdown(
                            f"**Recommendation:** "
                            f"{f.get('recommendation', '-')}"
                        )

            # Downloadable findings table
            findings_df = pd.DataFrame(findings)
            st.download_button(
                "Download Findings CSV",
                data=findings_df.to_csv(index=False),
                file_name=(
                    f"gap_analysis_"
                    f"{datetime.utcnow():%Y%m%d_%H%M%S}"
                    f".csv"
                ),
                mime="text/csv",
            )

        with st.expander("Raw JSON"):
            st.json(gap)


# ===================================================================
# Page 2 — Generate Requirements
# ===================================================================
elif page.startswith("2"):
    _page_header(
        "Generate Requirements (URS)",
        "Describe a requirement in plain English "
        "and the engine produces a GAMP 5 compliant URS",
    )

    if st.session_state.get("demo_mode", False):
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )
        st.session_state.generated_urs = (
            DEMO_DATA["generated_urs"]
        )

    requirement = st.text_area(
        "Requirement description",
        placeholder="e.g. The system shall monitor warehouse "
                    "temperature in real time.",
        height=120,
    )
    min_score = st.slider(
        "Minimum similarity score",
        min_value=0.20,
        max_value=0.80,
        value=0.35,
        step=0.05,
        help="Lower values return more results but may "
             "reduce relevance.",
    )

    if "generated_urs" not in st.session_state:
        st.session_state.generated_urs = None

    if st.button("Generate URS", type="primary"):
        if not requirement.strip():
            st.warning("Please enter a requirement description.")
        else:
            with st.spinner("Generating URS..."):
                try:
                    ctrl = AgentController()
                    st.session_state.generated_urs = (
                        ctrl.generate_urs(
                            requirement=requirement.strip(),
                            min_score=min_score,
                        )
                    )
                except Exception as exc:
                    st.error(f"URS generation failed: {exc}")

    urs = st.session_state.generated_urs
    if urs is not None:
        st.markdown("#### Generated URS")

        # Summary metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("URS ID", urs.get("URS_ID", "-"))
        crit = urs.get("Criticality", "-")
        c2.metric("Criticality", crit)
        versions = urs.get(
            "Reg_Versions_Cited", []
        )
        c3.metric(
            "Reg Versions",
            ", ".join(versions) if versions else "-",
        )

        st.markdown("**Requirement Statement**")
        st.info(
            urs.get("Requirement_Statement", "-")
        )
        st.markdown("**Regulatory Rationale**")
        st.markdown(
            urs.get("Regulatory_Rationale", "-")
        )
        st.markdown("---")
        with st.expander("Raw JSON"):
            st.json(urs)

        # ---- PDF Download ------------------------------------
        st.markdown("#### Download Approved URS")
        signer_name = st.text_input(
            "Signer Name",
            placeholder="e.g. Jane Smith",
            help="Name that will appear on the "
                 "Manifestation of Signature page.",
        )
        sig_meaning = st.text_input(
            "Signature Meaning",
            value="Approval of Requirements",
        )

        if signer_name.strip():
            from utils.pdf_generator import (
                generate_urs_pdf,
            )

            pdf_bytes = generate_urs_pdf(
                urs=urs,
                signer_name=signer_name.strip(),
                meaning=sig_meaning.strip(),
            )
            urs_id = urs.get("URS_ID", "URS")
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"{urs_id}.pdf",
                mime="application/pdf",
                type="primary",
            )
        else:
            st.caption(
                "Enter a signer name to enable "
                "PDF download."
            )


# ===================================================================
# Page 3 — Risk Assessment (Delta)
# ===================================================================
elif page.startswith("3"):
    _page_header(
        "Risk Assessment (Delta Agent)",
        "GAMP 5 risk evaluation with CSA testing strategy",
    )

    _demo_risk = st.session_state.get("demo_mode", False)
    if _demo_risk:
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )

    col_l, col_r = st.columns(2)

    with col_l:
        criticality = st.selectbox(
            "System Criticality",
            ["high", "critical", "medium",
             "moderate", "low", "minor"],
            index=2,
        )
    with col_r:
        change_type = st.selectbox(
            "Change Type",
            ["emergency", "expedited", "normal",
             "standard", "routine"],
            index=2,
        )

    if not _demo_risk:
        if st.button("Assess Risk", type="primary"):
            with st.spinner("Running GAMP 5 assessment..."):
                try:
                    ctrl = AgentController()
                    result = ctrl.assess_risk(
                        system_criticality=criticality,
                        change_type=change_type,
                    )

                    # Badge helper
                    level = result.get("risk_level", "")
                    badge_cls = {
                        "High": "badge-high",
                        "Medium": "badge-medium",
                        "Low": "badge-low",
                    }.get(level, "")

                    st.markdown(
                        f'### Risk Level: '
                        f'<span class="badge {badge_cls}">'
                        f'{level}</span>',
                        unsafe_allow_html=True,
                    )

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric(
                        "RPN", result.get("rpn", "-")
                    )
                    m2.metric(
                        "Severity",
                        result.get("severity", "-"),
                    )
                    m3.metric(
                        "Occurrence",
                        result.get("occurrence", "-"),
                    )
                    m4.metric(
                        "Detectability",
                        result.get("detectability", "-"),
                    )

                    st.markdown("---")
                    st.markdown(
                        f"**CSA Testing Strategy:** "
                        f"`{result.get('testing_strategy', '-')}`"
                    )
                    if result.get("patient_safety_override"):
                        st.warning(
                            "Patient Safety Override is ACTIVE"
                            " -- severity forced risk to HIGH."
                        )

                    with st.expander("Raw JSON"):
                        st.json(result)
                except Exception as exc:
                    st.error(
                        f"Risk assessment failed: {exc}"
                    )
    else:
        # Demo mode: show pre-built risk result
        result = DEMO_DATA["risk_result"]
        level = result.get("risk_level", "")
        badge_cls = {
            "High": "badge-high",
            "Medium": "badge-medium",
            "Low": "badge-low",
        }.get(level, "")

        st.markdown(
            f'### Risk Level: '
            f'<span class="badge {badge_cls}">'
            f'{level}</span>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("RPN", result.get("rpn", "-"))
        m2.metric(
            "Severity", result.get("severity", "-")
        )
        m3.metric(
            "Occurrence",
            result.get("occurrence", "-"),
        )
        m4.metric(
            "Detectability",
            result.get("detectability", "-"),
        )

        st.markdown("---")
        st.markdown(
            f"**CSA Testing Strategy:** "
            f"`{result.get('testing_strategy', '-')}`"
        )
        if result.get("patient_safety_override"):
            st.warning(
                "Patient Safety Override is ACTIVE "
                "-- severity forced risk to HIGH."
            )

        with st.expander("Raw JSON"):
            st.json(result)


# ===================================================================
# Page 4 — Gap Analysis Dashboard
# ===================================================================
elif page.startswith("4"):
    _page_header(
        "Gap Analysis Dashboard",
        "Vendor document compliance review against GAMP 5",
    )

    if st.session_state.get("demo_mode", False):
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )
        st.session_state.gap_result = (
            DEMO_DATA["gap_result"]
        )

    # Additional CSS for color-coded gap table
    st.markdown(
        """
        <style>
        .gap-row-missing {
            background-color: #FEE2E2 !important;
        }
        .gap-row-partial {
            background-color: #FEF3C7 !important;
        }
        .gap-row-covered {
            background-color: #D1FAE5 !important;
        }
        .gap-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }
        .gap-table th {
            background-color: #1B2A4A;
            color: #FFFFFF;
            padding: 0.6rem 0.8rem;
            text-align: left;
            font-weight: 600;
        }
        .gap-table td {
            padding: 0.55rem 0.8rem;
            border-bottom: 1px solid #E5E7EB;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    gap = st.session_state.get("gap_result")

    if gap is None:
        st.info(
            "No gap analysis results available. "
            "Upload a vendor document on the **Ingest Vendor "
            "Docs** page and run **Gap Analysis** first."
        )
    else:
        findings = gap.get("findings", [])
        total = len(findings)

        # Derive counts by status
        missing = sum(
            1 for f in findings
            if f.get("status", "").lower()
            in ("missing", "gap", "fail", "not met")
        )
        partial = sum(
            1 for f in findings
            if f.get("status", "").lower()
            in ("partial", "warning")
        )
        covered = sum(
            1 for f in findings
            if f.get("status", "").lower()
            in ("covered", "pass", "met")
        )
        critical = missing  # missing items are critical gaps
        compliance_pct = (
            int((covered / total) * 100) if total else 0
        )

        # ---- KPI metrics row ----
        k1, k2, k3 = st.columns(3)
        k1.metric(
            "Total Requirements Found",
            total,
        )
        k2.metric(
            "Critical Gaps",
            critical,
            delta=(
                f"-{critical}" if critical else "0"
            ),
            delta_color="inverse",
        )
        k3.metric(
            "Compliance Score",
            f"{compliance_pct}%",
        )

        st.markdown("---")

        # ---- Color-coded findings table ----
        if findings:
            st.markdown("#### Detailed Findings")

            # Build HTML table
            rows_html = ""
            for f in findings:
                status = f.get("status", "-")
                s_lower = status.lower()
                if s_lower in (
                    "missing", "gap", "fail", "not met"
                ):
                    row_cls = "gap-row-missing"
                elif s_lower in ("partial", "warning"):
                    row_cls = "gap-row-partial"
                else:
                    row_cls = "gap-row-covered"

                category = f.get("category", "-")
                vendor_ev = f.get(
                    "vendor_evidence", "-"
                )
                gamp_ref = f.get(
                    "gamp5_reference", "-"
                )
                rec = f.get("recommendation", "-")

                rows_html += (
                    f'<tr class="{row_cls}">'
                    f"<td>{category}</td>"
                    f"<td><strong>{status}</strong></td>"
                    f"<td>{vendor_ev}</td>"
                    f"<td>{gamp_ref}</td>"
                    f"<td>{rec}</td>"
                    f"</tr>"
                )

            st.markdown(
                f"""
                <table class="gap-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Status</th>
                            <th>Vendor Evidence</th>
                            <th>GAMP 5 Reference</th>
                            <th>Recommendation</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")  # spacing

            # Legend
            st.markdown(
                '<div style="font-size:0.8rem; '
                'margin-top:0.5rem;">'
                '<span class="badge badge-high">'
                "Missing</span> &ensp; "
                '<span class="badge badge-medium">'
                "Partial</span> &ensp; "
                '<span class="badge badge-low">'
                "Covered</span>"
                "</div>",
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # Download
            findings_df = pd.DataFrame(findings)
            st.download_button(
                "Download Gap Analysis CSV",
                data=findings_df.to_csv(index=False),
                file_name=(
                    f"gap_analysis_"
                    f"{datetime.utcnow():%Y%m%d_%H%M%S}"
                    f".csv"
                ),
                mime="text/csv",
            )

        with st.expander("Raw JSON"):
            st.json(gap)


# ===================================================================
# Page 5 — Audit Logs
# ===================================================================
elif page.startswith("5"):
    _page_header(
        "Audit Trail",
        "21 CFR Part 11 compliant, append-only audit log",
    )

    _demo_audit = st.session_state.get(
        "demo_mode", False
    )
    if _demo_audit:
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )

    if not _demo_audit and not AUDIT_CSV.exists():
        st.info(
            "No audit trail found yet. Run an agent action "
            "to create the first entry."
        )
    else:
        df = (
            DEMO_DATA["audit_df"].copy()
            if _demo_audit
            else pd.read_csv(AUDIT_CSV)
        )

        # Summary row
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Events", len(df))
        m2.metric(
            "Agents",
            df["Agent_Name"].nunique()
            if "Agent_Name" in df.columns else "-",
        )
        m3.metric(
            "Latest Entry",
            str(df["Timestamp"].iloc[-1])[:19]
            if "Timestamp" in df.columns and len(df) else "-",
        )

        st.markdown("---")

        # Filters
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            agents = ["All"] + sorted(
                df["Agent_Name"].dropna().unique().tolist()
            ) if "Agent_Name" in df.columns else ["All"]
            agent_filter = st.selectbox(
                "Filter by Agent", agents
            )
        with fcol2:
            actions = ["All"] + sorted(
                df["Action_Performed"].dropna().unique().tolist()
            ) if "Action_Performed" in df.columns else ["All"]
            action_filter = st.selectbox(
                "Filter by Action", actions
            )

        filtered = df.copy()
        if agent_filter != "All":
            filtered = filtered[
                filtered["Agent_Name"] == agent_filter
            ]
        if action_filter != "All":
            filtered = filtered[
                filtered["Action_Performed"] == action_filter
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Filtered CSV",
            data=filtered.to_csv(index=False),
            file_name=(
                f"audit_export_"
                f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                f".csv"
            ),
            mime="text/csv",
        )


# ===================================================================
# Page 6 — Validation Factory
# ===================================================================
elif page.startswith("6"):
    _page_header(
        "Validation Factory",
        "End-to-end: requirement \u2192 UR/FR \u2192 CSA test script",
    )

    # ---- CSS for Validation Factory tables ----
    st.markdown(
        """
        <style>
        .vf-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        .vf-table th {
            background-color: #1B2A4A;
            color: #FFFFFF;
            padding: 0.55rem 0.7rem;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }
        .vf-table td {
            padding: 0.5rem 0.7rem;
            border-bottom: 1px solid #E5E7EB;
            vertical-align: top;
        }
        .vf-table tr:nth-child(even) {
            background-color: #F8F9FB;
        }
        .vf-section-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #1B2A4A;
            margin: 0.8rem 0 0.4rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _demo_vf = st.session_state.get("demo_mode", False)
    _expert_vf = st.session_state.get(
        "expert_mode", False,
    )
    if _demo_vf:
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )
    if _expert_vf and not _demo_vf:
        st.info(
            "Expert Mode \u2014 skipping external "
            "document lookup; using custom UR/FR logic"
        )

    # ---- Input controls ----
    vf_requirement = st.text_area(
        "Requirement description",
        placeholder=(
            "e.g. The LIMS shall maintain a complete "
            "chain-of-custody record for every sample."
        ),
        height=100,
        key="vf_requirement",
    )

    pc1, pc2, pc3, pc4, pc5 = st.columns(5)
    with pc1:
        vf_role = st.text_input(
            "Role",
            value="Lab Technician",
            key="vf_role",
        )
    with pc2:
        vf_category = st.text_input(
            "Category",
            value="Sample Management",
            key="vf_category",
        )
    with pc3:
        vf_risk_assessment = st.selectbox(
            "Risk Assessment",
            ["GxP Direct", "GxP Indirect", "GxP None"],
            key="vf_risk_assessment",
        )
    with pc4:
        vf_impl_method = st.selectbox(
            "Implementation Method",
            ["Out of the Box", "Configured", "Custom"],
            index=1,
            key="vf_impl_method",
        )
    with pc5:
        vf_test_type = st.selectbox(
            "Test Type",
            ["Informal", "Formal OQ", "Formal UAT"],
            key="vf_test_type",
        )

    # ---- Session state init ----
    if "vf_ur_fr" not in st.session_state:
        st.session_state.vf_ur_fr = None
    if "vf_test_script" not in st.session_state:
        st.session_state.vf_test_script = None

    # ---- Action buttons ----
    btn1, btn2 = st.columns(2)
    with btn1:
        gen_req = st.button(
            "Generate Requirements",
            type="primary",
            key="vf_gen_req",
        )
    with btn2:
        draft_test = st.button(
            "Draft Test Scripts",
            disabled=(
                st.session_state.vf_ur_fr is None
                and not _demo_vf
            ),
            key="vf_draft_test",
        )

    # ---- Generate Requirements logic ----
    if gen_req:
        if _demo_vf:
            st.session_state.vf_ur_fr = (
                DEMO_DATA["ur_fr"]
            )
            st.session_state.vf_test_script = None
        else:
            if not vf_requirement.strip():
                st.warning(
                    "Please enter a requirement "
                    "description."
                )
            else:
                with st.spinner(
                    "Generating UR/FR document..."
                ):
                    try:
                        from Agents.requirement_architect \
                            import RequirementArchitect
                        architect = RequirementArchitect()
                        urs = architect.generate_urs(
                            vf_requirement.strip(),
                            expert_mode=_expert_vf,
                        )
                        ur_fr = (
                            architect.transform_urs_to_ur_fr(
                                urs=urs,
                                role=vf_role.strip(),
                                category=(
                                    vf_category.strip()
                                ),
                                risk_assessment=(
                                    vf_risk_assessment
                                ),
                                implementation_method=(
                                    vf_impl_method
                                ),
                            )
                        )
                        st.session_state.vf_ur_fr = ur_fr
                        st.session_state.vf_test_script = (
                            None
                        )
                    except Exception as exc:
                        st.error(
                            f"UR/FR generation failed: "
                            f"{exc}"
                        )

    # ---- Draft Test Scripts logic ----
    if draft_test:
        if _demo_vf:
            st.session_state.vf_test_script = (
                DEMO_DATA["test_script"]
            )
        else:
            ur_fr = st.session_state.vf_ur_fr
            if ur_fr is None:
                st.warning(
                    "Generate requirements first."
                )
            else:
                with st.spinner(
                    "Drafting CSA test script..."
                ):
                    try:
                        from Agents.delta_agent import (
                            DeltaAgent,
                        )
                        delta = DeltaAgent()
                        script = (
                            delta
                            .generate_csa_test_from_ur_fr(
                                ur_fr, vf_test_type
                            )
                        )
                        st.session_state.vf_test_script = (
                            script
                        )
                    except Exception as exc:
                        st.error(
                            f"Test script generation "
                            f"failed: {exc}"
                        )

    # ---- Display results side-by-side ----
    st.markdown("---")
    left_col, right_col = st.columns(2)

    # ---- Left: UR/FR Table ----
    with left_col:
        ur_fr = st.session_state.vf_ur_fr
        if ur_fr is not None:
            st.markdown(
                '<p class="vf-section-title">'
                "User Requirement / Functional Requirements"
                "</p>",
                unsafe_allow_html=True,
            )

            ur = ur_fr.get("user_requirement", {})
            rl = ur.get("risk_level", "-")
            rl_lower = rl.lower()
            rl_badge = (
                "badge-high" if rl_lower == "high"
                else "badge-medium"
                if rl_lower == "medium"
                else "badge-low"
            )

            # UR summary table
            ur_html = f"""
            <table class="vf-table">
                <thead><tr>
                    <th>Field</th><th>Value</th>
                </tr></thead>
                <tbody>
                <tr>
                    <td><strong>URS ID</strong></td>
                    <td>{ur_fr.get('urs_id', '-')}</td>
                </tr>
                <tr>
                    <td><strong>UR ID</strong></td>
                    <td>{ur.get('ur_id', '-')}</td>
                </tr>
                <tr>
                    <td><strong>Statement</strong></td>
                    <td>{ur.get('statement', '-')}</td>
                </tr>
                <tr>
                    <td><strong>Risk Assessment</strong></td>
                    <td>{ur.get('risk_assessment', '-')}</td>
                </tr>
                <tr>
                    <td><strong>Implementation</strong></td>
                    <td>{ur.get(
                        'implementation_method', '-'
                    )}</td>
                </tr>
                <tr>
                    <td><strong>Risk Level</strong></td>
                    <td><span class="badge {rl_badge}"
                        >{rl}</span></td>
                </tr>
                <tr>
                    <td><strong>Test Strategy</strong></td>
                    <td>{ur.get(
                        'test_strategy', '-'
                    )}</td>
                </tr>
                </tbody>
            </table>
            """
            st.markdown(ur_html, unsafe_allow_html=True)
            st.markdown("")

            # FR table
            frs = ur_fr.get(
                "functional_requirements", []
            )
            if frs:
                fr_rows = ""
                for fr in frs:
                    ac = fr.get(
                        "acceptance_criteria", []
                    )
                    ac_text = "; ".join(ac) if ac else "-"
                    fr_rows += (
                        f"<tr>"
                        f"<td>{fr.get('fr_id', '-')}</td>"
                        f"<td>{fr.get('statement', '-')}"
                        f"</td>"
                        f"<td>{ac_text}</td>"
                        f"</tr>"
                    )

                fr_html = f"""
                <table class="vf-table">
                    <thead><tr>
                        <th>FR ID</th>
                        <th>Statement</th>
                        <th>Acceptance Criteria</th>
                    </tr></thead>
                    <tbody>{fr_rows}</tbody>
                </table>
                """
                st.markdown(
                    fr_html, unsafe_allow_html=True
                )

            st.markdown("")

            # ---- UR/FR Downloads ----
            dl1, dl2 = st.columns(2)

            # CSV download
            ur_csv_rows = []
            ur_csv_rows.append({
                "Type": "UR",
                "ID": ur.get("ur_id", ""),
                "Statement": ur.get("statement", ""),
                "Risk Assessment": ur.get(
                    "risk_assessment", ""
                ),
                "Implementation": ur.get(
                    "implementation_method", ""
                ),
                "Risk Level": ur.get(
                    "risk_level", ""
                ),
                "Test Strategy": ur.get(
                    "test_strategy", ""
                ),
            })
            for fr in frs:
                ac = fr.get(
                    "acceptance_criteria", []
                )
                ur_csv_rows.append({
                    "Type": "FR",
                    "ID": fr.get("fr_id", ""),
                    "Statement": fr.get(
                        "statement", ""
                    ),
                    "Risk Assessment": "",
                    "Implementation": "",
                    "Risk Level": "",
                    "Test Strategy": "; ".join(ac),
                })
            ur_df = pd.DataFrame(ur_csv_rows)

            with dl1:
                st.download_button(
                    "Download UR/FR CSV",
                    data=ur_df.to_csv(index=False),
                    file_name=(
                        f"ur_fr_"
                        f"{ur_fr.get('urs_id', 'doc')}"
                        f".csv"
                    ),
                    mime="text/csv",
                    key="vf_ur_csv",
                )

            # PDF download
            with dl2:
                pdf_cols = [
                    "Type", "ID", "Statement",
                    "Risk/Criteria",
                ]
                pdf_rows = []
                pdf_rows.append((
                    "UR",
                    ur.get("ur_id", ""),
                    ur.get("statement", ""),
                    f"{ur.get('risk_level', '')} / "
                    f"{ur.get('test_strategy', '')}",
                ))
                for fr in frs:
                    ac = fr.get(
                        "acceptance_criteria", []
                    )
                    pdf_rows.append((
                        "FR",
                        fr.get("fr_id", ""),
                        fr.get("statement", ""),
                        "; ".join(ac),
                    ))
                ur_pdf = _build_table_pdf(
                    f"UR/FR Document - "
                    f"{ur_fr.get('urs_id', '')}",
                    pdf_cols,
                    pdf_rows,
                )
                st.download_button(
                    "Download UR/FR PDF",
                    data=ur_pdf,
                    file_name=(
                        f"ur_fr_"
                        f"{ur_fr.get('urs_id', 'doc')}"
                        f".pdf"
                    ),
                    mime="application/pdf",
                    key="vf_ur_pdf",
                )

            with st.expander("UR/FR Raw JSON"):
                st.json(ur_fr)
        else:
            st.info(
                "Generate requirements to see the "
                "UR/FR document here."
            )

    # ---- Right: Test Script Table ----
    with right_col:
        ts = st.session_state.vf_test_script
        if ts is not None:
            st.markdown(
                '<p class="vf-section-title">'
                "CSA Test Script</p>",
                unsafe_allow_html=True,
            )

            # Script metadata
            ts_rl = ts.get("risk_level", "-")
            ts_badge = (
                "badge-high"
                if ts_rl.lower() == "high"
                else "badge-medium"
                if ts_rl.lower() == "medium"
                else "badge-low"
            )
            st.markdown(
                f"**Script:** {ts.get('script_id', '-')}"
                f" &ensp;|&ensp; "
                f"**Risk:** "
                f'<span class="badge {ts_badge}">'
                f"{ts_rl}</span>"
                f" &ensp;|&ensp; "
                f"**Type:** {ts.get('test_type', '-')}",
                unsafe_allow_html=True,
            )
            st.markdown("")

            # ---- Show Justification toggle ----
            show_just = st.toggle(
                "Show Justification",
                key="vf_show_justification",
            )
            if show_just:
                just_text = ts.get(
                    "regulatory_justification", "",
                )
                if just_text:
                    st.markdown(
                        f'<div style="'
                        f"background:#F0F4FF;"
                        f"border-left:4px solid "
                        f"{ACCENT};"
                        f"border-radius:6px;"
                        f"padding:0.7rem 1rem;"
                        f"margin-bottom:0.8rem;"
                        f"font-size:0.85rem;"
                        f"color:#1B2A4A;"
                        f'">'
                        f"<strong>Regulatory "
                        f"Justification</strong>"
                        f"<br/>{just_text}</div>",
                        unsafe_allow_html=True,
                    )

            # Steps table
            steps = ts.get("steps", [])
            if steps:
                step_rows = ""
                for s in steps:
                    tc = s.get("test_case_type", "")
                    tc_badge = ""
                    if tc:
                        tc_cls = (
                            "badge-low"
                            if tc == "Positive"
                            else "badge-high"
                            if tc == "Negative"
                            else "badge-medium"
                        )
                        tc_badge = (
                            f'<span class="badge '
                            f'{tc_cls}">{tc}</span>'
                        )
                    step_rows += (
                        f"<tr>"
                        f"<td>{s.get('step_type', '')}"
                        f"</td>"
                        f"<td>{s.get('step_number', '')}"
                        f"</td>"
                        f"<td>{s.get('step_title', '')}"
                        f"</td>"
                        f"<td>{s.get('step_instruction', '')}"
                        f"</td>"
                        f"<td>{s.get('expected_result', '')}"
                        f"</td>"
                        f"<td>{tc_badge}</td>"
                        f"<td>{s.get('requirement_reference', '')}"
                        f"</td>"
                        f"</tr>"
                    )

                ts_html = f"""
                <table class="vf-table">
                    <thead><tr>
                        <th>Type</th>
                        <th>#</th>
                        <th>Title</th>
                        <th>Instruction</th>
                        <th>Expected Result</th>
                        <th>Case</th>
                        <th>Ref</th>
                    </tr></thead>
                    <tbody>{step_rows}</tbody>
                </table>
                """
                st.markdown(
                    ts_html, unsafe_allow_html=True
                )

            st.markdown("")

            # ---- Test Script Downloads ----
            dl3, dl4 = st.columns(2)

            # CSV
            steps_df = pd.DataFrame(steps)
            with dl3:
                st.download_button(
                    "Download Test CSV",
                    data=steps_df.to_csv(index=False),
                    file_name=(
                        f"test_script_"
                        f"{ts.get('script_id', 'doc')}"
                        f".csv"
                    ),
                    mime="text/csv",
                    key="vf_ts_csv",
                )

            # PDF
            with dl4:
                ts_pdf_cols = [
                    "Type", "#", "Title",
                    "Instruction",
                    "Expected Result", "Case", "Ref",
                ]
                ts_pdf_rows = []
                for s in steps:
                    ts_pdf_rows.append((
                        s.get("step_type", ""),
                        str(s.get("step_number", "")),
                        s.get("step_title", ""),
                        s.get("step_instruction", ""),
                        s.get("expected_result", ""),
                        s.get("test_case_type", ""),
                        s.get(
                            "requirement_reference", ""
                        ),
                    ))
                ts_pdf = _build_table_pdf(
                    f"CSA Test Script - "
                    f"{ts.get('script_id', '')}",
                    ts_pdf_cols,
                    ts_pdf_rows,
                )
                st.download_button(
                    "Download Test PDF",
                    data=ts_pdf,
                    file_name=(
                        f"test_script_"
                        f"{ts.get('script_id', 'doc')}"
                        f".pdf"
                    ),
                    mime="application/pdf",
                    key="vf_ts_pdf",
                )

            with st.expander("Test Script Raw JSON"):
                st.json(ts)
        else:
            st.info(
                "Draft test scripts to see the "
                "CSA test script here."
            )


# ===================================================================
# Page 7 — Traceability
# ===================================================================
elif page.startswith("7"):
    _page_header(
        "Requirements Traceability Matrix",
        "End-to-end mapping from Functional Requirements "
        "to Test Steps",
    )

    # ---- CSS for RTM table ----
    st.markdown(
        """
        <style>
        .rtm-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        .rtm-table th {
            background-color: #1B2A4A;
            color: #FFFFFF;
            padding: 0.55rem 0.7rem;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }
        .rtm-table td {
            padding: 0.5rem 0.7rem;
            border-bottom: 1px solid #E5E7EB;
            vertical-align: top;
        }
        .rtm-table tr:nth-child(even) {
            background-color: #F8F9FB;
        }
        .rtm-covered {
            background-color: #D1FAE5 !important;
        }
        .rtm-gap {
            background-color: #FEE2E2 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _demo_rtm = st.session_state.get(
        "demo_mode", False,
    )
    if _demo_rtm:
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )

    # ---- Session state init ----
    if "rtm_result" not in st.session_state:
        st.session_state.rtm_result = None

    # ---- Determine data availability ----
    has_ur_fr = (
        st.session_state.get("vf_ur_fr") is not None
    )
    has_test = (
        st.session_state.get("vf_test_script")
        is not None
    )
    data_ready = (has_ur_fr and has_test) or _demo_rtm

    if not data_ready:
        st.info(
            "Generate requirements **and** test scripts "
            "in the **Validation Factory** tab first, "
            "then return here to build the RTM."
        )
    else:
        gen_rtm = st.button(
            "Generate RTM",
            type="primary",
            key="rtm_generate",
        )

        if gen_rtm:
            if _demo_rtm:
                st.session_state.rtm_result = (
                    DEMO_DATA["rtm"]
                )
            else:
                with st.spinner("Building RTM..."):
                    try:
                        from Agents.auditor_agent import (
                            AuditorAgent,
                        )
                        auditor = AuditorAgent()
                        st.session_state.rtm_result = (
                            auditor.generate_rtm(
                                ur_fr=(
                                    st.session_state
                                    .vf_ur_fr
                                ),
                                test_script=(
                                    st.session_state
                                    .vf_test_script
                                ),
                            )
                        )
                    except Exception as exc:
                        st.error(
                            f"RTM generation failed: "
                            f"{exc}"
                        )

    rtm = st.session_state.rtm_result
    if rtm is not None:
        st.markdown("---")

        # ---- KPI metrics row ----
        k1, k2, k3, k4 = st.columns(4)
        total_fr = rtm.get(
            "total_requirements", 0,
        )
        covered_fr = rtm.get(
            "covered_requirements", 0,
        )
        gap_fr = rtm.get("gap_requirements", 0)
        cov_pct = rtm.get(
            "coverage_percentage", 0,
        )

        k1.metric("Total FRs", total_fr)
        k2.metric("Covered", covered_fr)
        k3.metric(
            "Gaps",
            gap_fr,
            delta=(
                f"-{gap_fr}" if gap_fr else "0"
            ),
            delta_color="inverse",
        )
        k4.metric("Coverage", f"{cov_pct}%")

        # ---- Coverage progress bar ----
        pct_int = int(cov_pct)
        bar_color = (
            "#065F46" if pct_int >= 80
            else "#92400E" if pct_int >= 50
            else "#991B1B"
        )
        st.markdown(
            f"""
            <div style="
                background:{BORDER};
                border-radius:6px;
                height:24px;
                margin:0.5rem 0 1rem 0;
                overflow:hidden;">
                <div style="
                    width:{pct_int}%;
                    height:100%;
                    background:{bar_color};
                    border-radius:6px;
                    text-align:center;
                    color:#FFF;
                    font-size:0.75rem;
                    line-height:24px;
                    font-weight:600;">
                    {pct_int}% covered
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- RTM metadata ----
        st.markdown(
            f"**RTM:** {rtm.get('rtm_id', '-')}"
            f" &ensp;|&ensp; "
            f"**URS:** {rtm.get('urs_id', '-')}"
            f" &ensp;|&ensp; "
            f"**Script:** "
            f"{rtm.get('test_script_id', '-')}"
            f" &ensp;|&ensp; "
            f"**Risk:** "
            f"<span class=\"badge "
            f"{'badge-high' if rtm.get('risk_level', '').lower() == 'high' else 'badge-medium' if rtm.get('risk_level', '').lower() == 'medium' else 'badge-low'}\">"
            f"{rtm.get('risk_level', '-')}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        # ---- RTM table ----
        rows = rtm.get("rows", [])
        if rows:
            st.markdown(
                "#### Traceability Matrix"
            )

            rtm_rows_html = ""
            for r in rows:
                status = r.get(
                    "coverage_status", "-",
                )
                row_cls = (
                    "rtm-covered"
                    if status == "Covered"
                    else "rtm-gap"
                )
                status_icon = (
                    "&#9989;"
                    if status == "Covered"
                    else "&#10060;"
                )
                case_types = r.get(
                    "test_case_types", [],
                )
                cases_html = ""
                for ct in case_types:
                    ct_cls = (
                        "badge-low"
                        if ct == "Positive"
                        else "badge-high"
                        if ct == "Negative"
                        else "badge-medium"
                    )
                    cases_html += (
                        f'<span class="badge '
                        f'{ct_cls}">{ct}</span> '
                    )
                if not cases_html:
                    cases_html = "-"

                rtm_rows_html += (
                    f'<tr class="{row_cls}">'
                    f"<td><strong>"
                    f"{r.get('fr_id', '-')}"
                    f"</strong></td>"
                    f"<td>"
                    f"{r.get('requirement_statement', '-')}"
                    f"</td>"
                    f"<td>"
                    f"{r.get('test_script_id', '-')}"
                    f"</td>"
                    f"<td>"
                    f"{r.get('test_steps', '-')}"
                    f"</td>"
                    f"<td>{cases_html}</td>"
                    f"<td>{status_icon} "
                    f"<strong>{status}</strong></td>"
                    f"</tr>"
                )

            st.markdown(
                f"""
                <table class="rtm-table">
                    <thead><tr>
                        <th>FR ID</th>
                        <th>Requirement</th>
                        <th>Test Script</th>
                        <th>Test Steps</th>
                        <th>Case Types</th>
                        <th>Status</th>
                    </tr></thead>
                    <tbody>{rtm_rows_html}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            # Legend
            st.markdown(
                '<div style="font-size:0.8rem; '
                'margin-top:0.5rem;">'
                '<span class="badge badge-low">'
                "Covered</span> &ensp; "
                '<span class="badge badge-high">'
                "Gap</span>"
                "</div>",
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # ---- Downloads ----
            dl1, dl2 = st.columns(2)

            # CSV download
            rtm_csv_rows = []
            for r in rows:
                rtm_csv_rows.append({
                    "URS ID": r.get("urs_id", ""),
                    "UR ID": r.get("ur_id", ""),
                    "FR ID": r.get("fr_id", ""),
                    "Requirement": r.get(
                        "requirement_statement", "",
                    ),
                    "Test Script": r.get(
                        "test_script_id", "",
                    ),
                    "Test Steps": r.get(
                        "test_steps", "",
                    ),
                    "Case Types": ", ".join(
                        r.get("test_case_types", []),
                    ),
                    "Status": r.get(
                        "coverage_status", "",
                    ),
                })
            rtm_df = pd.DataFrame(rtm_csv_rows)

            with dl1:
                st.download_button(
                    "Download RTM CSV",
                    data=rtm_df.to_csv(index=False),
                    file_name=(
                        f"rtm_"
                        f"{rtm.get('rtm_id', 'doc')}"
                        f".csv"
                    ),
                    mime="text/csv",
                    key="rtm_csv_dl",
                )

            # PDF download
            with dl2:
                rtm_pdf_cols = [
                    "FR ID", "Requirement",
                    "Script", "Steps",
                    "Cases", "Status",
                ]
                rtm_pdf_rows = []
                for r in rows:
                    rtm_pdf_rows.append((
                        r.get("fr_id", ""),
                        r.get(
                            "requirement_statement",
                            "",
                        ),
                        r.get(
                            "test_script_id", "",
                        ),
                        r.get("test_steps", ""),
                        ", ".join(
                            r.get(
                                "test_case_types",
                                [],
                            ),
                        ),
                        r.get(
                            "coverage_status", "",
                        ),
                    ))
                rtm_pdf = _build_table_pdf(
                    f"Requirements Traceability "
                    f"Matrix - "
                    f"{rtm.get('rtm_id', '')}",
                    rtm_pdf_cols,
                    rtm_pdf_rows,
                )
                st.download_button(
                    "Download RTM PDF",
                    data=rtm_pdf,
                    file_name=(
                        f"rtm_"
                        f"{rtm.get('rtm_id', 'doc')}"
                        f".pdf"
                    ),
                    mime="application/pdf",
                    key="rtm_pdf_dl",
                )

        with st.expander("RTM Raw JSON"):
            st.json(rtm)
