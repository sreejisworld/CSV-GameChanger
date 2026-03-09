"""
EVOLV: The Validation Factory - CSV-GameChanger Frontend.

Streamlit dashboard for the GAMP 5 / CSA compliant Validation Factory.
Provides a professional enterprise UI for document ingestion,
requirements generation, risk assessment, and audit log review.

:requirement: URS-1.1 - System shall accept change requests.
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import streamlit as st
import streamlit.components.v1 as _st_components
import pandas as pd
from datetime import datetime

from frontend.components.theme import load_theme
from frontend.components.header import (
    breadcrumb,
    page_header,
    adversarial_page_header,
)
from frontend.components.data_grid import toolbar, empty_state, skeleton_table
from frontend.components.sidebar import render_sidebar

try:
    from API.agent_controller import AgentController
except Exception:
    AgentController = None  # type: ignore[assignment,misc]

# -------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="EVOLV: The Validation Factory",
    page_icon="\u2666",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# SOHO Design System — load external theme + keyboard shortcuts
# -------------------------------------------------------------------
load_theme(PROJECT_ROOT)

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
            "Per GAMP5 Guide [GAMP5_Rev2] (p.38): "
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
    "demo_comparison": {
        "system_description": (
            "LabCore LIMS v4.2 is a laboratory information "
            "management system used across QC and stability "
            "labs for sample tracking, instrument "
            "integration, and results reporting in a "
            "GMP-regulated pharmaceutical environment."
        ),
        "human_requirements": [
            "The system should track all samples quickly "
            "and easily",
            "Users need to be able to sign off on results "
            "in a timely and efficient manner",
            "The system should store data in a robust and "
            "seamless way with minimal downtime",
        ],
    },
    "adversarial_result": {
        "adversarial_mode": True,
        "stress_tests": [
            {
                "scenario_id": "ST-1",
                "type": "Boundary Analysis",
                "title": "Null / Empty Sample ID Input",
                "description": (
                    "Submit a chain-of-custody record "
                    "with a null, empty, or whitespace-"
                    "only sample identifier and verify "
                    "the system rejects it with a "
                    "structured validation error."
                ),
                "failure_mode": (
                    "Silent acceptance of empty ID "
                    "breaks chain-of-custody integrity."
                ),
            },
            {
                "scenario_id": "ST-2",
                "type": "Adversarial Input",
                "title": "Corrupted Custodian Data "
                         "Injection",
                "description": (
                    "Inject a custodian record "
                    "containing SQL escape sequences, "
                    "Unicode surrogates, and embedded "
                    "null bytes to verify data "
                    "sanitisation before persistence."
                ),
                "failure_mode": (
                    "Unsanitised input stored verbatim "
                    "corrupts audit trail integrity "
                    "and 21 CFR Part 11 compliance."
                ),
            },
            {
                "scenario_id": "ST-3",
                "type": "Failure Mode",
                "title": "Model Confidence Degradation "
                         "Under Adversarial Load",
                "description": (
                    "Simulate concurrent adversarial "
                    "requests with deliberately "
                    "ambiguous or contradictory "
                    "requirement statements to "
                    "measure classification drift "
                    "under load."
                ),
                "failure_mode": (
                    "Risk level misclassification "
                    "under adversarial load leads to "
                    "under-validated high-risk items."
                ),
            },
        ],
        "assurance_confidence_score": 87,
        "score_rationale": (
            "Base 60 + High risk path (+10) + "
            "2 FRs present (+10) + acceptance "
            "criteria present (+10) + "
            "non-Custom implementation (+10) "
            "= 100 → capped at 95, floored "
            "at 40 → final score 87."
        ),
        "generated_at": "2026-02-22T00:00:00Z",
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
# Pre-widget: handle demo load request (must run before
# toggle widgets claim their session-state keys)
# -------------------------------------------------------------------
if st.session_state.get("_load_demo_requested"):
    st.session_state["_load_demo_requested"] = False
    st.session_state["demo_mode"] = True
    st.session_state["vf_requirement"] = (
        "The LIMS shall maintain a complete, "
        "immutable chain-of-custody record for "
        "every laboratory sample from receipt "
        "through testing, storage, and disposal, "
        "including custodian identity, timestamp, "
        "location, and condition at each transfer "
        "point."
    )
    st.session_state["vf_role"] = "Lab Technician"
    st.session_state["vf_category"] = (
        "Sample Management"
    )
    st.session_state["vf_risk_assessment"] = (
        "GxP Direct"
    )
    st.session_state["vf_impl_method"] = "Configured"
    st.session_state["vf_test_type"] = "Informal"
    st.session_state["vf_ur_fr"] = (
        DEMO_DATA["ur_fr"]
    )
    st.session_state["vf_test_script"] = (
        DEMO_DATA["test_script"]
    )
    st.session_state["rtm_result"] = (
        DEMO_DATA["rtm"]
    )
    st.session_state["ingest_result"] = (
        DEMO_DATA["ingest_result"]
    )
    st.session_state["gap_result"] = (
        DEMO_DATA["gap_result"]
    )
    st.session_state["generated_urs"] = (
        DEMO_DATA["generated_urs"]
    )
    st.session_state["dc_system_desc"] = (
        DEMO_DATA["demo_comparison"][
            "system_description"
        ]
    )
    for _i, _req in enumerate(
        DEMO_DATA["demo_comparison"][
            "human_requirements"
        ],
        1,
    ):
        st.session_state[f"dc_req_{_i}"] = _req


# -------------------------------------------------------------------
# Sidebar: Logo + Grouped Navigation + Status + Audit Feed
# -------------------------------------------------------------------
page = render_sidebar(audit_csv=AUDIT_CSV)


# -------------------------------------------------------------------
# Helper: generate negative-testing and data-drift scenarios
# -------------------------------------------------------------------
def generate_adversarial_scenarios(
    ur_fr: dict,
    limitations: list = None,
) -> list:
    """Generate negative-testing, data-drift, and vendor-constraint scenarios.

    Targets three failure classes:

    * **Negative Testing** — cases where the system *should* reject
      the input (invalid fields, missing mandatories, type mismatches).
    * **Data Drift** — how the system handles out-of-range values
      that silently corrupt QC records over time.
    * **Vendor Constraints (LIM-N)** — each vendor-stated limitation
      becomes an enforcement scenario; the system must actively reject
      or block the prohibited action.

    :param ur_fr: UR/FR document from RequirementArchitect.
    :param limitations: Optional list of vendor limitation strings
                        extracted by IngestorAgent (from ingest_result
                        or gap_analysis_report).  Capped at 5.
    :return: List of adversarial scenario dicts.
    :requirement: URS-21.2 - Negative testing and drift scenarios.
    :requirement: URS-21.3 - Vendor constraint enforcement scenarios.
    """
    ur = ur_fr.get("user_requirement", {})
    frs = ur_fr.get("functional_requirements", [])
    ur_stmt = ur.get("statement", "the requirement")
    risk_level = ur.get("risk_level", "Low")

    # ── NEG-1: Negative Testing ────────────────────────────────
    fr_labels = ", ".join(
        f.get("fr_id", "") for f in frs[:3]
    ) or "FR-1"
    neg_1 = {
        "scenario_id": "NEG-1",
        "type": "Negative Testing",
        "title": "System Rejection of Invalid Input",
        "description": (
            f"Submit requests for '{ur_stmt[:70]}' "
            f"with deliberately invalid field "
            f"combinations, missing mandatory fields, "
            f"and type-mismatched values. Verify the "
            f"system rejects each case with a "
            f"structured, auditable error and does NOT "
            f"persist partial data. Scope: {fr_labels}."
        ),
        "failure_mode": (
            "Partial acceptance of invalid input "
            "creates orphan records in the audit trail,"
            " violating 21 CFR Part 11 data integrity."
        ),
    }

    # ── DRIFT-1: Data Drift / Out-of-Range ─────────────────────
    _thresholds = {
        "high": ("<= 5%", "90 days"),
        "medium": ("<= 10%", "180 days"),
        "low": ("<= 20%", "365 days"),
    }
    _drift_limit, _period = _thresholds.get(
        risk_level.lower(), ("<= 20%", "365 days")
    )
    drift_1 = {
        "scenario_id": "DRIFT-1",
        "type": "Data Drift",
        "title": "Out-of-Range Value Handling",
        "description": (
            f"Inject values systematically outside "
            f"acceptable range for '{ur_stmt[:60]}'. "
            f"Verify the system flags, quarantines, or "
            f"rejects out-of-range data without silent "
            f"propagation. GAMP 5 drift threshold for "
            f"{risk_level} risk: {_drift_limit} "
            f"over {_period}."
        ),
        "failure_mode": (
            "Silent acceptance of out-of-range data "
            "introduces undetected drift that "
            "invalidates calibration records and "
            "corrupts QC statistical process control."
        ),
    }

    scenarios = [neg_1, drift_1]

    # ── LIM-N: Vendor Constraint Enforcement ───────────────────
    for idx, lim in enumerate(
        (limitations or [])[:5], start=1
    ):
        lim_short = lim.strip()
        scenarios.append({
            "scenario_id": f"LIM-{idx}",
            "type": "Vendor Constraint",
            "title": (
                f"Enforce: {lim_short[:60]}"
                f"{'...' if len(lim_short) > 60 else ''}"
            ),
            "description": (
                f"The vendor document states: "
                f"\"{lim_short[:120]}"
                f"{'...' if len(lim_short) > 120 else ''}\". "
                f"Attempt to exercise this prohibited action "
                f"against '{ur_stmt[:60]}' and confirm the "
                f"system rejects it with an auditable error. "
                f"Verify no partial state is persisted."
            ),
            "failure_mode": (
                f"Failure to enforce vendor constraint "
                f"'{lim_short[:50]}...' creates a compliance "
                f"gap that invalidates the system's stated "
                f"intended-use boundary."
            ),
        })

    return scenarios


# -------------------------------------------------------------------
# Helper: deterministic adversarial red-team analysis
# -------------------------------------------------------------------
def _run_adversarial_analysis(
    ur_fr: dict,
    extra_scenarios: list = None,
) -> dict:
    """Run deterministic adversarial stress-test analysis.

    Produces base stress-test scenarios (ST-1/ST-2/ST-3) plus any
    ``extra_scenarios`` passed in (e.g. from
    ``generate_adversarial_scenarios()``), and an assurance
    confidence score — no LLM or Pinecone calls.

    :param ur_fr: UR/FR document from RequirementArchitect.
    :return: Adversarial analysis result dict.
    :requirement: URS-21.1 - Adversarial red-team analysis.
    """
    ur = ur_fr.get("user_requirement", {})
    frs = ur_fr.get("functional_requirements", [])
    risk_level = ur.get("risk_level", "Low")
    impl_method = ur.get("implementation_method", "Custom")
    ur_statement = ur.get("statement", "the requirement")
    risk_assess = ur.get("risk_assessment", "GxP None")

    # ── First FR details for ST-1 ──────────────────────────────
    first_fr = frs[0] if frs else {}
    first_fr_stmt = first_fr.get(
        "statement", "the system function"
    )
    first_ac = first_fr.get("acceptance_criteria", [])
    first_ac_text = first_ac[0] if first_ac else (
        "the acceptance criterion"
    )

    # ── ST-1: Boundary Analysis ────────────────────────────────
    st1 = {
        "scenario_id": "ST-1",
        "type": "Boundary Analysis",
        "title": (
            f"Null / Empty Input for: {first_fr_stmt[:60]}"
        ),
        "description": (
            f"Submit a request triggering '{first_fr_stmt}' "
            f"with null, empty, and max-length boundary "
            f"values. Expected: system rejects gracefully "
            f"with structured validation error. "
            f"Reference: {first_ac_text[:80]}."
        ),
        "failure_mode": (
            "Silent acceptance of boundary-violating "
            "input corrupts data integrity and audit "
            "trail completeness."
        ),
    }

    # ── ST-2: Adversarial Input ────────────────────────────────
    st2 = {
        "scenario_id": "ST-2",
        "type": "Adversarial Input",
        "title": (
            "Corrupted / Biased Data Injection"
        ),
        "description": (
            f"What happens if the input data for "
            f"'{ur_statement[:80]}' is intentionally "
            f"corrupted or biased? Inject SQL escape "
            f"sequences, Unicode surrogates, and embedded "
            f"null bytes. Risk context: {risk_assess}."
        ),
        "failure_mode": (
            "Unsanitised adversarial input stored "
            "verbatim violates 21 CFR Part 11 audit "
            "trail integrity and GxP data governance."
        ),
    }

    # ── ST-3: Failure Mode / Drift ─────────────────────────────
    if risk_level.lower() == "high":
        st3_title = (
            "Model Confidence Degradation Under "
            "Adversarial Load"
        )
        st3_desc = (
            "Simulate concurrent adversarial requests "
            "with deliberately ambiguous or contradictory "
            "requirement statements to measure "
            "classification drift under load for "
            f"'{ur_statement[:60]}'."
        )
    else:
        st3_title = (
            "Silent Drift in Edge-Case Data Handling"
        )
        st3_desc = (
            "Exercise boundary edge-cases with "
            "near-duplicate, near-empty, and "
            "out-of-range data patterns to detect "
            f"silent drift in '{ur_statement[:60]}' "
            "handling at medium/low risk threshold."
        )
    st3 = {
        "scenario_id": "ST-3",
        "type": "Failure Mode",
        "title": st3_title,
        "description": st3_desc,
        "failure_mode": (
            "Risk-level misclassification or silent "
            "data drift leads to under-validated "
            "high-risk items reaching production."
        ),
    }

    # ── Assurance Confidence Score (0–100) ─────────────────────
    score = 60
    if risk_level.lower() == "high":
        score += 10
    if len(frs) >= 2:
        score += 10
    if any(
        fr.get("acceptance_criteria")
        for fr in frs
    ):
        score += 10
    if impl_method.lower() != "custom":
        score += 10
    score = min(score, 95)   # never 100% — residual risk
    score = max(score, 40)

    rationale_parts = [f"Base 60"]
    if risk_level.lower() == "high":
        rationale_parts.append("High risk path (+10)")
    if len(frs) >= 2:
        rationale_parts.append("≥2 FRs (+10)")
    if any(fr.get("acceptance_criteria") for fr in frs):
        rationale_parts.append("AC present (+10)")
    if impl_method.lower() != "custom":
        rationale_parts.append(
            "non-Custom implementation (+10)"
        )
    rationale_parts.append(
        f"capped at 95, floored at 40 → {score}"
    )
    score_rationale = " + ".join(rationale_parts)

    from datetime import datetime as _dt
    _all_scenarios = [st1, st2, st3]
    if extra_scenarios:
        _all_scenarios.extend(extra_scenarios)
    return {
        "adversarial_mode": True,
        "stress_tests": _all_scenarios,
        "assurance_confidence_score": score,
        "score_rationale": score_rationale,
        "generated_at": (
            _dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
    }


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
        0, 12, "EVOLV  |  The Validation Factory",
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
        "Powered by EVOLV  |  "
        "A WingstarTech Inc. Product",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    return bytes(pdf.output())


# ===================================================================
# Page 1 — Ingest Vendor Docs
# ===================================================================
if page == "1":
    breadcrumb(["Home", "Ingest Vendor Docs"])
    page_header(
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
        im1, im2, im3, im4 = st.columns(4)
        im1.metric("Title", ingest.get("title", "-"))
        im2.metric(
            "Pages", ingest.get("total_pages", "-")
        )
        im3.metric(
            "Sections",
            len(ingest.get("sections", [])),
        )
        im4.metric(
            "Limitations",
            len(ingest.get("limitations", [])),
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
                        "section_type",
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

        lims = ingest.get("limitations", [])
        if lims:
            # Bridge: make limitations available to Page 6
            # adversarial engine across page navigation
            st.session_state.vendor_limitations = lims
            with st.expander(
                f"Extracted Limitations ({len(lims)})"
            ):
                st.caption(
                    "These constraints are automatically "
                    "loaded into the Adversarial Red-Teaming "
                    "engine on the Validation Factory page."
                )
                for lim in lims:
                    st.markdown(
                        f'<span class="badge badge-high">'
                        f"&#x26A0;</span>&nbsp;{lim}",
                        unsafe_allow_html=True,
                    )

        with st.expander("Raw JSON"):
            st.json(ingest)

    # ---- Gap Analysis Results ----
    gap = st.session_state.gap_result
    if gap is not None:
        st.markdown("---")
        st.markdown("### GAMP 5 Gap Analysis")

        # Summary metrics
        gm1, gm2, gm3, gm4 = st.columns(4)
        total_cat = gap.get("total_categories", 0)
        covered = gap.get("covered", 0)
        partial_count = gap.get("partial", 0)
        gaps_count = gap.get("gaps", 0)
        gm1.metric("Categories Assessed", total_cat)
        gm2.metric("Covered", covered)
        gm3.metric("Partial", partial_count)
        gm4.metric("Gaps Found", gaps_count)

        # Coverage bar
        if total_cat > 0:
            pct = int((covered / total_cat) * 100)
            bar_cls = (
                "green" if pct >= 80
                else "amber" if pct >= 50
                else "red"
            )
            st.markdown(
                f'<div class="soho-progress">'
                f'<div class="soho-progress-fill {bar_cls}"'
                f' style="width:{pct}%;"></div></div>'
                f'<p style="font-size:0.8rem;'
                f'color:var(--ev-slate-light);'
                f'margin:0.2rem 0 0.8rem 0;">'
                f'{pct}% covered</p>',
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
                    sim_score = f.get("similarity_score", 0.0)
                    badge = _status_badge(status)

                    with st.expander(
                        f"{cat}  |  {status}", expanded=False
                    ):
                        st.markdown(
                            f"**Status:** {badge}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"**Similarity Score:** "
                            f"`{sim_score:.4f} / 1.00`"
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
                        clause_map = f.get(
                            "regulatory_clause_mapping", []
                        )
                        if clause_map:
                            with st.expander(
                                "Regulatory Clause Mapping"
                            ):
                                clause_rows = [
                                    {
                                        "Rank": c.get("rank", ""),
                                        "Source": c.get(
                                            "source", ""
                                        ),
                                        "Page": c.get("page", ""),
                                        "Score": round(
                                            float(
                                                c.get(
                                                    "similarity_score",
                                                    0,
                                                )
                                            ),
                                            4,
                                        ),
                                        "Excerpt": (
                                            c.get(
                                                "text_excerpt", ""
                                            )[:120] + "…"
                                            if len(
                                                c.get(
                                                    "text_excerpt",
                                                    "",
                                                )
                                            ) > 120
                                            else c.get(
                                                "text_excerpt", ""
                                            )
                                        ),
                                    }
                                    for c in clause_map
                                ]
                                st.dataframe(
                                    pd.DataFrame(clause_rows),
                                    use_container_width=True,
                                    hide_index=True,
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

        # Requirement → GAMP 5 Clause Mapping
        req_mappings = gap.get("requirement_mappings", [])
        if req_mappings:
            with st.expander(
                f"Requirement \u2192 GAMP 5 Clause Mapping "
                f"({len(req_mappings)})"
            ):
                for rm in req_mappings:
                    req_text = rm.get("requirement", "")
                    clauses = rm.get("regulatory_clauses", [])
                    top_clause = clauses[0] if clauses else {}
                    src = top_clause.get("source", "-")
                    pg = top_clause.get("page", "-")
                    score = round(
                        float(
                            top_clause.get("similarity_score", 0)
                        ),
                        4,
                    )
                    st.markdown(
                        f"**{req_text[:100]}"
                        f"{'…' if len(req_text) > 100 else ''}**"
                        f" &nbsp;→&nbsp; "
                        f"`{src}` p.{pg} "
                        f"(score: `{score}`)",
                        unsafe_allow_html=True,
                    )

        # Bridge gap-result limitations into Page 6 feed
        # (merges with any already set by ingest result)
        gap_lims = gap.get("limitations", [])
        if gap_lims:
            existing = st.session_state.get(
                "vendor_limitations", []
            )
            merged = list(
                dict.fromkeys(existing + gap_lims)
            )
            st.session_state.vendor_limitations = merged

        with st.expander("Raw JSON"):
            st.json(gap)


# ===================================================================
# Page 2 — Generate Requirements (100x Intelligence Engine)
# ===================================================================
elif page.startswith("2"):
    breadcrumb(["Home", "Requirements", "Generate URS"])
    page_header(
        "Generate Requirements (URS)",
        "Describe requirements in plain English — "
        "the 100x Intelligence Engine produces GAMP 5 compliant URS, "
        "workflow diagrams, acceptance criteria, and gap analysis.",
    )

    _expert_p2 = st.session_state.get("expert_mode", False)

    if st.session_state.get("demo_mode", False):
        st.info("Demo Mode \u2014 showing sample LIMS data")
        st.session_state.generated_urs = DEMO_DATA["generated_urs"]

    if _expert_p2 and not st.session_state.get("demo_mode", False):
        st.info(
            "Expert Mode \u2014 skipping external document lookup; "
            "using deterministic GAMP 5 / CSA logic"
        )

    # ---- Primary input row -----------------------------------------
    _col_req, _col_sys = st.columns([3, 2])
    with _col_req:
        requirement = st.text_area(
            "Requirement description",
            placeholder=(
                "Enter one or more requirements (one per line).\n"
                "e.g. The system shall monitor warehouse temperature "
                "in real time.\n"
                "e.g. The system shall enforce role-based access control."
            ),
            height=140,
            key="p2_requirement",
        )
    with _col_sys:
        _p2_sys_desc = st.text_area(
            "System description",
            placeholder=(
                "Describe the system under validation.\n"
                "e.g. A LIMS for pharmaceutical laboratory "
                "sample management."
            ),
            height=140,
            key="p2_system_description",
        )

    if not _expert_p2:
        min_score = st.slider(
            "Minimum similarity score",
            min_value=0.20,
            max_value=0.80,
            value=0.35,
            step=0.05,
            help="Lower values return more results but "
                 "may reduce relevance.",
        )
    else:
        min_score = 0.35

    # ---- Workflow & Security Intelligence expander -----------------
    _DEFAULT_SECURITY_MATRIX = json.dumps(
        [
            {
                "step": "User Login",
                "security_requirements": [
                    "MFA required",
                    "Session timeout after 15 minutes",
                ],
            },
            {
                "step": "Data Entry",
                "security_requirements": [
                    "Role-based access control enforced",
                ],
            },
            {
                "step": "Report Export",
                "security_requirements": [],
            },
        ],
        indent=2,
    )
    with st.expander(
        "Workflow & Security Intelligence "
        "(optional \u2014 powers the diagram and gap finder)",
        expanded=False,
    ):
        _wi_col, _sm_col = st.columns(2)
        with _wi_col:
            _p2_workflow = st.text_area(
                "Workflow text",
                placeholder=(
                    "Describe the workflow steps in order.\n"
                    "1. User logs in with MFA\n"
                    "2. System validates credentials\n"
                    "3. User enters sample data\n"
                    "4. System records audit trail\n"
                    "5. Supervisor approves record\n"
                    "6. Report exported to PDF"
                ),
                height=190,
                key="p2_workflow_text",
            )
        with _sm_col:
            _p2_sec_matrix = st.text_area(
                "Security matrix (JSON)",
                value=_DEFAULT_SECURITY_MATRIX,
                height=190,
                key="p2_security_matrix",
                help=(
                    'Format: [{"step": "...", '
                    '"security_requirements": ["..."]}]'
                ),
            )

    # ---- Session state init ----------------------------------------
    if "generated_urs" not in st.session_state:
        st.session_state.generated_urs = None
    if "intelligence_result" not in st.session_state:
        st.session_state.intelligence_result = None

    # ---- Action buttons -------------------------------------------
    _p2_btn1, _p2_btn2, _p2_spacer = st.columns([2, 3, 5])
    with _p2_btn1:
        _p2_gen_urs = st.button("Generate URS", type="primary")
    with _p2_btn2:
        _p2_gen_intel = st.button(
            "\u2728 Generate Intelligence",
            help=(
                "Runs the 100x Intelligence Engine: Mermaid workflow "
                "diagram, requirement categorisation, acceptance "
                "criteria (Positive / Negative / Edge), and "
                "Proactive Gap Finder."
            ),
        )

    # ---- Generate URS (single requirement, existing flow) ----------
    if _p2_gen_urs:
        _p2_first_req = next(
            (
                ln.strip()
                for ln in requirement.splitlines()
                if ln.strip()
            ),
            "",
        )
        if not _p2_first_req:
            st.warning("Please enter a requirement description.")
        else:
            with st.spinner("Generating URS..."):
                try:
                    ctrl = AgentController()
                    st.session_state.generated_urs = ctrl.generate_urs(
                        requirement=_p2_first_req,
                        min_score=min_score,
                        expert_mode=_expert_p2,
                    )
                except Exception as exc:
                    st.error(f"URS generation failed: {exc}")

    # ---- Generate Intelligence (multi-requirement) -----------------
    if _p2_gen_intel:
        _p2_reqs = [
            ln.strip(" -\u2022*0123456789.")
            for ln in requirement.splitlines()
            if ln.strip()
        ]
        if not _p2_reqs:
            st.warning(
                "Please enter at least one requirement to run "
                "the Intelligence Engine."
            )
        else:
            # Parse security matrix JSON
            try:
                _p2_matrix = json.loads(_p2_sec_matrix)
                if not isinstance(_p2_matrix, list):
                    _p2_matrix = []
            except Exception:
                _p2_matrix = []
                st.warning(
                    "Security matrix JSON is invalid \u2014 "
                    "gap analysis will run without it."
                )

            with st.spinner(
                "Running 100x Intelligence Engine\u2026"
            ):
                try:
                    from Agents.intelligence_engine import (
                        IntelligenceEngine,
                    )
                    _p2_engine = IntelligenceEngine()
                    st.session_state.intelligence_result = (
                        _p2_engine.generate_intelligence(
                            requirements=_p2_reqs,
                            system_description=_p2_sys_desc,
                            workflow_text=_p2_workflow,
                            security_matrix=_p2_matrix,
                        )
                    )
                except Exception as exc:
                    st.error(
                        f"Intelligence Engine failed: {exc}"
                    )

    # ================================================================
    # URS Output (single-requirement path)
    # ================================================================
    urs = st.session_state.generated_urs
    if urs is not None:
        st.markdown("#### Generated URS")
        c1, c2, c3 = st.columns(3)
        c1.metric("URS ID", urs.get("URS_ID", "-"))
        crit = urs.get("Criticality", "-")
        c2.metric("Criticality", crit)
        versions = urs.get("Reg_Versions_Cited", [])
        c3.metric(
            "Reg Versions",
            ", ".join(versions) if versions else "-",
        )
        st.markdown("**Requirement Statement**")
        st.info(urs.get("Requirement_Statement", "-"))
        st.markdown("**Regulatory Rationale**")
        st.markdown(urs.get("Regulatory_Rationale", "-"))
        st.markdown("---")
        with st.expander("Raw JSON"):
            st.json(urs)

        # PDF Download
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
            from utils.pdf_generator import generate_urs_pdf
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
                "Enter a signer name to enable PDF download."
            )

    # ================================================================
    # Intelligence Dashboard
    # ================================================================
    _p2_intel = st.session_state.intelligence_result
    if _p2_intel is not None:
        st.markdown("---")
        st.markdown("### \u2728 Intelligence Dashboard")

        # Risk colour map (used in multiple sections below)
        _P2_RISK_ICONS = {
            "High": "\U0001f534",
            "Medium": "\U0001f7e1",
            "Low": "\U0001f7e2",
        }
        _P2_TEST_MAP = {
            "High": "Scripted OQ / UAT",
            "Medium": "Hybrid (Scripted + Unscripted)",
            "Low": "Unscripted / Ad-hoc",
        }

        # ---- Split-screen: Mermaid left | Smart Table right ------
        _p2_diag_col, _p2_tbl_col = st.columns([4, 6])

        with _p2_diag_col:
            st.markdown("#### Workflow Diagram")
            # Build Mermaid HTML — use concatenation to avoid
            # f-string collision with Mermaid's {curly} syntax.
            _p2_diag_html = (
                '<html>'
                '<body style="margin:0;padding:8px;'
                'background:#0e1117;">'
                '<div class="mermaid" '
                'style="font-family:sans-serif;font-size:13px;">'
                + _p2_intel.mermaid_diagram
                + '</div>'
                '<script type="module">'
                'import mermaid from '
                "'https://cdn.jsdelivr.net/npm/"
                "mermaid@10/dist/mermaid.esm.min.mjs';"
                'mermaid.initialize({'
                "startOnLoad:true,"
                "theme:'dark',"
                'flowchart:{curve:"basis",htmlLabels:true}'
                '});'
                '</script>'
                '</body>'
                '</html>'
            )
            _st_components.html(
                _p2_diag_html, height=380, scrolling=True
            )
            if _p2_intel.workflow_steps:
                with st.expander(
                    f"Detected steps "
                    f"({len(_p2_intel.workflow_steps)})"
                ):
                    for _s in _p2_intel.workflow_steps:
                        st.markdown(f"- {_s}")

        with _p2_tbl_col:
            st.markdown("#### Smart Requirements Table")
            _p2_tbl_rows = []
            for _row in _p2_intel.requirements_intelligence:
                _p2_tbl_rows.append(
                    {
                        "Requirement": (
                            _row.requirement[:90] + "\u2026"
                            if len(_row.requirement) > 90
                            else _row.requirement
                        ),
                        "Category": _row.category,
                        "Risk Rank": _row.risk_level,
                        "Test Assurance": _row.test_assurance,
                    }
                )
            _p2_df = pd.DataFrame(_p2_tbl_rows)
            _p2_edited = st.data_editor(
                _p2_df,
                column_config={
                    "Requirement": st.column_config.TextColumn(
                        "Requirement",
                        disabled=True,
                        width="large",
                    ),
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=[
                            "Functional", "Security",
                            "Regulatory", "Data Integrity",
                            "Integration", "Performance",
                            "Audit/Compliance", "Non-functional",
                        ],
                        required=True,
                    ),
                    "Risk Rank": st.column_config.SelectboxColumn(
                        "Risk Rank",
                        options=["High", "Medium", "Low"],
                        required=True,
                        help=(
                            "Toggle to re-classify. Test Assurance "
                            "updates automatically."
                        ),
                    ),
                    "Test Assurance": st.column_config.TextColumn(
                        "Test Assurance Suggestion",
                        disabled=True,
                        width="large",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                key="p2_smart_table",
            )
            # Sync Test Assurance if Risk Rank was toggled
            if not _p2_edited["Risk Rank"].equals(
                _p2_df["Risk Rank"]
            ):
                _p2_edited["Test Assurance"] = (
                    _p2_edited["Risk Rank"].map(_P2_TEST_MAP)
                )
                st.caption(
                    "Test Assurance updated to reflect new "
                    "Risk Rank selections."
                )

        # ---- Acceptance Criteria --------------------------------
        st.markdown("#### Acceptance Criteria")
        for _p2_row in _p2_intel.requirements_intelligence:
            _p2_icon = _P2_RISK_ICONS.get(
                _p2_row.risk_level, ""
            )
            _p2_label = (
                _p2_row.requirement[:72] + "\u2026"
                if len(_p2_row.requirement) > 72
                else _p2_row.requirement
            )
            with st.expander(
                f"{_p2_icon} {_p2_label} "
                f"[{_p2_row.category}]"
            ):
                _p2_ac = _p2_row.acceptance_criteria
                _p2_ac_p, _p2_ac_n, _p2_ac_e = st.columns(3)
                with _p2_ac_p:
                    st.markdown("**\u2705 Positive Cases**")
                    for _ac in _p2_ac.positive:
                        st.success(_ac)
                with _p2_ac_n:
                    st.markdown("**\u274c Negative Cases**")
                    for _ac in _p2_ac.negative:
                        st.error(_ac)
                with _p2_ac_e:
                    st.markdown("**\u26a0\ufe0f Edge Cases**")
                    for _ac in _p2_ac.edge:
                        st.warning(_ac)

        # ---- Proactive Gap Finder ------------------------------
        st.markdown("---")
        st.markdown(
            "#### \U0001f50d Proactive Gap Finder"
        )
        if _p2_intel.security_gaps:
            _p2_high_gaps = [
                g for g in _p2_intel.security_gaps
                if g.severity == "High"
            ]
            _p2_med_gaps = [
                g for g in _p2_intel.security_gaps
                if g.severity == "Medium"
            ]
            _gf1, _gf2, _gf3 = st.columns(3)
            _gf1.metric(
                "Total Gaps",
                len(_p2_intel.security_gaps),
            )
            _gf2.metric(
                "\U0001f6a8 High Severity",
                len(_p2_high_gaps),
            )
            _gf3.metric(
                "\u26a0\ufe0f Medium Severity",
                len(_p2_med_gaps),
            )
            st.markdown("")
            for _gap in _p2_intel.security_gaps:
                if _gap.severity == "High":
                    st.error(
                        f"\U0001f6a8 **{_gap.step}** \u2014 "
                        f"{_gap.gap_description}"
                    )
                else:
                    st.warning(
                        f"\u26a0\ufe0f **{_gap.step}** \u2014 "
                        f"{_gap.gap_description}"
                    )
        elif _p2_intel.workflow_steps:
            st.success(
                "All workflow steps have corresponding security "
                "requirements in the matrix."
            )
        else:
            st.info(
                "Provide workflow text and a security matrix to "
                "enable gap analysis."
            )

        with st.expander("Raw Intelligence JSON"):
            st.json(_p2_intel.to_dict())


# ===================================================================
# Page 3 — Risk Assessment (Delta)
# ===================================================================
elif page.startswith("3"):
    breadcrumb(["Home", "Risk Assessment"])
    page_header(
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
    breadcrumb(["Home", "Gap Analysis"])
    page_header(
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

    gap = st.session_state.get("gap_result")

    if gap is None:
        empty_state(
            "No Gap Analysis Results",
            "Upload a vendor document on the Ingest "
            "Vendor Docs page and run Gap Analysis "
            "first.",
            icon="search",
            action_label="Go to Ingest",
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
                    row_cls = "row-missing"
                elif s_lower in ("partial", "warning"):
                    row_cls = "row-partial"
                else:
                    row_cls = "row-covered"

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

            toolbar(
                "Compliance Findings",
                [{"label": "Export"}],
            )
            st.markdown(
                f"""
                <div class="soho-grid-wrap"><table class="soho-grid">
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
                </table></div>
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
    breadcrumb(["Home", "Audit Logs"])
    page_header(
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
    breadcrumb(["Home", "Validation Factory"])
    adversarial_page_header(
        "Validation Factory",
        "End-to-end: requirement \u2192 UR/FR \u2192 CSA test script",
    )

    # ---- Workflow Diagram (SOHO) ----
    st.markdown(
        """
        <div class="workflow-bar">
            <span class="workflow-step">
                System Description</span>
            <span class="workflow-arrow">&rarr;</span>
            <span class="workflow-step">URS</span>
            <span class="workflow-arrow">&rarr;</span>
            <span class="workflow-step">UR / FR</span>
            <span class="workflow-arrow">&rarr;</span>
            <span class="workflow-step">Test Script</span>
            <span class="workflow-arrow">&rarr;</span>
            <span class="workflow-step active">RTM</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _demo_vf = st.session_state.get("demo_mode", False)
    _expert_vf = st.session_state.get(
        "expert_mode", False,
    )
    _adversarial_vf = st.session_state.get(
        "adversarial_mode", False,
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
    if _adversarial_vf:
        st.caption(
            "Advanced diagnostics active — "
            "red-team analysis will run after test "
            "script generation."
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

    # ---- Additional context for UR/FR generation ----
    with st.expander(
        "Additional Context (optional)", expanded=False,
    ):
        ctx_col1, ctx_col2 = st.columns(2)
        with ctx_col1:
            vf_system_desc = st.text_area(
                "System Description",
                placeholder=(
                    "Describe the system under validation "
                    "(e.g. vendor name, version, deployment "
                    "model, interfaces)."
                ),
                height=120,
                key="vf_system_desc",
            )
            vf_workshop_notes = st.text_area(
                "Workshop Notes",
                placeholder=(
                    "Paste stakeholder workshop notes, "
                    "decisions, or action items."
                ),
                height=120,
                key="vf_workshop_notes",
            )
        with ctx_col2:
            vf_roles_permissions = st.text_area(
                "User Roles & Permissions",
                placeholder=(
                    "List user roles and their permissions "
                    "(e.g. Admin: full access, Analyst: "
                    "read/write, Reviewer: read-only)."
                ),
                height=120,
                key="vf_roles_permissions",
            )
            vf_lucidchart_url = st.text_input(
                "Lucidchart / Diagram Link",
                placeholder="https://lucid.app/...",
                key="vf_lucidchart_url",
            )
            vf_lucidchart_file = st.file_uploader(
                "Or upload diagram export",
                type=["txt", "csv", "pdf", "png", "jpg"],
                key="vf_lucidchart_file",
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
    if "vf_adversarial_result" not in st.session_state:
        st.session_state.vf_adversarial_result = None

    # ---- Action buttons ----
    _draft_label = (
        "Draft Test Scripts + Red-Team"
        if _adversarial_vf
        else "Draft Test Scripts"
    )
    btn1, btn2 = st.columns(2)
    with btn1:
        gen_req = st.button(
            "Generate Requirements",
            type="primary",
            key="vf_gen_req",
        )
    with btn2:
        draft_test = st.button(
            _draft_label,
            disabled=(
                st.session_state.vf_ur_fr is None
                and not _demo_vf
            ),
            key="vf_draft_test",
        )

    # ---- Build additional context dict ----
    _additional_context: Dict[str, Any] = {}
    _sys_desc = st.session_state.get(
        "vf_system_desc", ""
    )
    _ws_notes = st.session_state.get(
        "vf_workshop_notes", ""
    )
    _roles_perms = st.session_state.get(
        "vf_roles_permissions", ""
    )
    _lc_url = st.session_state.get(
        "vf_lucidchart_url", ""
    )
    _lc_file = st.session_state.get(
        "vf_lucidchart_file", None
    )

    if _sys_desc and _sys_desc.strip():
        _additional_context["system_description"] = (
            _sys_desc.strip()
        )
    if _ws_notes and _ws_notes.strip():
        _additional_context["workshop_notes"] = (
            _ws_notes.strip()
        )
    if _roles_perms and _roles_perms.strip():
        _additional_context["roles_and_permissions"] = (
            _roles_perms.strip()
        )
    if _lc_url and _lc_url.strip():
        _additional_context["lucidchart_url"] = (
            _lc_url.strip()
        )
    if _lc_file is not None:
        try:
            _lc_content = _lc_file.read().decode(
                "utf-8", errors="replace"
            )
            _additional_context["lucidchart_content"] = (
                _lc_content
            )
        except Exception:
            _additional_context["lucidchart_filename"] = (
                _lc_file.name
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
                                additional_context=(
                                    _additional_context
                                    if _additional_context
                                    else None
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
            if _adversarial_vf:
                st.session_state.vf_adversarial_result = (
                    DEMO_DATA.get("adversarial_result")
                )
            else:
                st.session_state.vf_adversarial_result = (
                    None
                )
        else:
            ur_fr = st.session_state.vf_ur_fr
            if ur_fr is None:
                st.warning(
                    "Generate requirements first."
                )
            else:
                if _adversarial_vf:
                    # ── Progress bar for deep-dive
                    #    adversarial analysis ──────────
                    import time as _time
                    _prog = st.progress(
                        0,
                        text=(
                            "Initializing deep-dive "
                            "analysis..."
                        ),
                    )
                    try:
                        from Agents.delta_agent import (
                            DeltaAgent,
                        )
                        _prog.progress(
                            20,
                            text=(
                                "Drafting CSA "
                                "test script..."
                            ),
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
                        _prog.progress(
                            45,
                            text=(
                                "Scanning for negative "
                                "test scenarios..."
                            ),
                        )
                        _time.sleep(0.3)
                        _prog.progress(
                            70,
                            text=(
                                "Analysing data drift "
                                "thresholds..."
                            ),
                        )
                        _vendor_lims = (
                            st.session_state.get(
                                "vendor_limitations", []
                            )
                        )
                        _extra = (
                            generate_adversarial_scenarios(
                                ur_fr,
                                limitations=_vendor_lims,
                            )
                        )
                        _time.sleep(0.3)
                        _prog.progress(
                            88,
                            text=(
                                "Computing assurance "
                                "confidence score..."
                            ),
                        )
                        adv_result = (
                            _run_adversarial_analysis(
                                ur_fr,
                                extra_scenarios=_extra,
                            )
                        )
                        _prog.progress(
                            100,
                            text=(
                                "Red-team analysis "
                                "complete."
                            ),
                        )
                        _time.sleep(0.4)
                        _prog.empty()
                        st.session_state\
                            .vf_adversarial_result = (
                            adv_result
                        )
                    except Exception as exc:
                        _prog.empty()
                        st.error(
                            f"Test script generation "
                            f"failed: {exc}"
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
                            st.session_state.vf_test_script\
                                = script
                            st.session_state\
                                .vf_adversarial_result = (
                                None
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
                '<p class="section-title">'
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
            <div class="soho-grid-wrap"><table class="soho-grid">
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
            </table></div>
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
                <div class="soho-grid-wrap"><table class="soho-grid">
                    <thead><tr>
                        <th>FR ID</th>
                        <th>Statement</th>
                        <th>Acceptance Criteria</th>
                    </tr></thead>
                    <tbody>{fr_rows}</tbody>
                </table></div>
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
                '<p class="section-title">'
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
                        f'<div class="soho-info-box">'
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
                <div class="soho-grid-wrap"><table class="soho-grid">
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
                </table></div>
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

    # ---- Vendor Limitations Feed indicator ----
    if _adversarial_vf:
        _vl = st.session_state.get("vendor_limitations", [])
        if _vl:
            with st.expander(
                f"⚡ Vendor Limitations Feed "
                f"({len(_vl)} constraints loaded)",
                expanded=False,
            ):
                st.caption(
                    "These constraints were extracted from "
                    "your ingested vendor document and are "
                    "injected as LIM-N scenarios into the "
                    "adversarial engine."
                )
                for _i, _lim in enumerate(_vl, 1):
                    st.markdown(
                        f'<span class="badge badge-high" '
                        f'style="font-size:0.7rem;">'
                        f"LIM-{_i}</span>&nbsp;{_lim}",
                        unsafe_allow_html=True,
                    )

    # ---- Adversarial Stress Test Results ----
    _adv_res = st.session_state.get(
        "vf_adversarial_result"
    )
    if _adv_res:
        st.markdown("---")
        st.markdown(
            "#### ⚡ Adversarial Stress Test Results"
        )
        _conf = _adv_res.get(
            "assurance_confidence_score", 0
        )
        _rat = _adv_res.get("score_rationale", "")
        _gauge_color = (
            "#2ca02c" if _conf >= 80
            else "#f0a500" if _conf >= 60
            else "#d62728"
        )
        st.markdown(
            f'<div style="display:flex;align-items:'
            f'center;gap:1rem;margin-bottom:0.5rem;">'
            f'<div style="font-size:2rem;font-weight:'
            f'700;color:{_gauge_color};">{_conf}</div>'
            f'<div style="font-size:0.9rem;color:#555;">'
            f'/ 100 — Assurance Confidence Score</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.caption(_rat)
        st.markdown("")

        _sts = _adv_res.get("stress_tests", [])
        if _sts:
            # ST-1 / ST-2 / ST-3 — standard 3-column grid
            _base = [
                s for s in _sts
                if not s.get("scenario_id",
                              "").startswith("LIM")
            ]
            _lim_sts = [
                s for s in _sts
                if s.get("scenario_id", "").startswith("LIM")
            ]
            _ac1, _ac2, _ac3 = st.columns(3)
            _adv_cols = [_ac1, _ac2, _ac3]
            for _i, _st_item in enumerate(_base[:3]):
                with _adv_cols[_i]:
                    st.markdown(
                        f'<span class="badge '
                        f'badge-medium" '
                        f'style="font-size:0.7rem;">'
                        f'{_st_item.get("scenario_id","")} '
                        f'— {_st_item.get("type","")}'
                        f'</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'**{_st_item.get("title","")}**'
                    )
                    st.markdown(
                        _st_item.get("description", "")
                    )
                    _fm = _st_item.get(
                        "failure_mode", ""
                    )
                    st.markdown(
                        f'<span style="color:#c0392b;'
                        f'font-size:0.78rem;">'
                        f'⚠ Failure Mode: {_fm}'
                        f'</span>',
                        unsafe_allow_html=True,
                    )

            # NEG-1 / DRIFT-1 — extra generated scenarios
            _extra_sts = [
                s for s in _sts
                if not s.get("scenario_id", "").startswith(
                    "LIM"
                ) and s not in _base
            ]
            if _extra_sts:
                _ec1, _ec2 = st.columns(2)
                _extra_cols = [_ec1, _ec2]
                for _i, _st_item in enumerate(
                    _extra_sts[:2]
                ):
                    with _extra_cols[_i]:
                        st.markdown(
                            f'<span class="badge '
                            f'badge-medium" '
                            f'style="font-size:0.7rem;">'
                            f'{_st_item.get("scenario_id","")} '
                            f'— {_st_item.get("type","")}'
                            f'</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'**{_st_item.get("title","")}**'
                        )
                        st.markdown(
                            _st_item.get("description", "")
                        )
                        _fm = _st_item.get(
                            "failure_mode", ""
                        )
                        st.markdown(
                            f'<span style="color:#c0392b;'
                            f'font-size:0.78rem;">'
                            f'⚠ Failure Mode: {_fm}'
                            f'</span>',
                            unsafe_allow_html=True,
                        )

            # LIM-N — vendor constraint enforcement scenarios
            if _lim_sts:
                st.markdown(
                    "##### ⚡ Vendor Constraint Scenarios"
                )
                for _st_item in _lim_sts:
                    with st.expander(
                        f'{_st_item.get("scenario_id","")} '
                        f'— {_st_item.get("title","")}',
                        expanded=False,
                    ):
                        st.markdown(
                            f'<span class="badge badge-high" '
                            f'style="font-size:0.7rem;">'
                            f'{_st_item.get("scenario_id","")} '
                            f'— {_st_item.get("type","")}'
                            f'</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            _st_item.get("description", "")
                        )
                        _fm = _st_item.get(
                            "failure_mode", ""
                        )
                        st.markdown(
                            f'<span style="color:#c0392b;'
                            f'font-size:0.78rem;">'
                            f'⚠ Failure Mode: {_fm}'
                            f'</span>',
                            unsafe_allow_html=True,
                        )

    # ---- Download Validation Report (combined PDF) ----
    vr_ur = st.session_state.vf_ur_fr
    vr_ts = st.session_state.vf_test_script
    if vr_ur is not None and vr_ts is not None:
        st.divider()
        st.subheader("Download Validation Report")
        vr_c1, vr_c2 = st.columns(2)
        with vr_c1:
            vr_signer = st.text_input(
                "Signer Name",
                placeholder="Jane Smith",
                key="vr_signer",
            )
        with vr_c2:
            vr_meaning = st.text_input(
                "Signature Meaning",
                value="Approval of Validation Report",
                key="vr_meaning",
            )

        if vr_signer.strip():
            from utils.pdf_generator import (
                generate_validation_report_pdf,
            )

            vr_pdf = generate_validation_report_pdf(
                ur_fr=vr_ur,
                test_script=vr_ts,
                signer_name=vr_signer.strip(),
                meaning=vr_meaning.strip(),
            )
            vr_id = vr_ur.get("urs_id", "doc")
            st.download_button(
                "Download Validation Report",
                data=vr_pdf,
                file_name=(
                    f"validation_report_{vr_id}.pdf"
                ),
                mime="application/pdf",
                key="vf_vr_pdf",
                type="primary",
                use_container_width=True,
            )
        else:
            st.info(
                "Enter a signer name to enable the "
                "Validation Report download."
            )

    # ---- Formatted Word Document ----
    if vr_ur is not None and vr_ts is not None:
        st.divider()
        st.subheader("Formatted Word Document")
        st.caption(
            "Upload a .docx template with "
            "{{PLACEHOLDER}} markers and the engine "
            "will inject the generated validation "
            "data while preserving your formatting."
        )
        vf_word_tpl = st.file_uploader(
            "Upload Word Template",
            type=["docx"],
            key="vf_word_template",
            help=(
                "Supported placeholders: "
                "{{URS_ID}}, {{REQUIREMENT_SUMMARY}}, "
                "{{CATEGORY}}, {{RISK_ASSESSMENT}}, "
                "{{IMPLEMENTATION_METHOD}}, "
                "{{RISK_LEVEL}}, {{TEST_STRATEGY}}, "
                "{{UR_STATEMENT}}, "
                "{{SYSTEM_DESCRIPTION}}, "
                "{{WORKSHOP_NOTES}}, "
                "{{ROLES_AND_PERMISSIONS}}, "
                "{{ASSUMPTIONS}}, "
                "{{COMPLIANCE_NOTES}}, "
                "{{GENERATED_DATE}}, "
                "{{SIGNER_NAME}}, "
                "{{REQUIREMENTS_TABLE}}, "
                "{{TEST_STEPS_TABLE}}"
            ),
        )
        if vf_word_tpl is not None:
            try:
                from utils.word_generator import (
                    inject_template,
                )

                _w_signer = st.session_state.get(
                    "vr_signer", ""
                )
                word_bytes = inject_template(
                    template_bytes=(
                        vf_word_tpl.getvalue()
                    ),
                    ur_fr=vr_ur,
                    test_script=vr_ts,
                    signer_name=_w_signer.strip(),
                )
                _w_id = vr_ur.get("urs_id", "doc")
                st.download_button(
                    "Download Formatted "
                    "Requirement Doc",
                    data=word_bytes,
                    file_name=(
                        f"validation_{_w_id}.docx"
                    ),
                    mime=(
                        "application/"
                        "vnd.openxmlformats-"
                        "officedocument."
                        "wordprocessingml.document"
                    ),
                    key="vf_word_dl",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(
                    f"Word template injection "
                    f"failed: {exc}"
                )


# ===================================================================
# Page 7 — Traceability
# ===================================================================
elif page.startswith("7"):
    breadcrumb(["Home", "Traceability"])
    page_header(
        "Requirements Traceability Matrix",
        "End-to-end mapping from Functional Requirements "
        "to Test Steps",
    )

    # RTM table styles provided by soho_theme.css

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
        empty_state(
            "No Traceability Data",
            "Generate requirements and test scripts "
            "in the Validation Factory tab first, "
            "then return here to build the RTM.",
            icon="table",
            action_label="Go to Validation Factory",
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
        bar_cls = (
            "green" if pct_int >= 80
            else "amber" if pct_int >= 50
            else "red"
        )
        st.markdown(
            f'<div class="soho-progress">'
            f'<div class="soho-progress-fill {bar_cls}"'
            f' style="width:{pct_int}%;"></div></div>'
            f'<p style="font-size:0.8rem;'
            f'color:var(--ev-slate-light);'
            f'margin:0.2rem 0 0.8rem 0;">'
            f'{pct_int}% covered</p>',
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
                    "row-covered"
                    if status == "Covered"
                    else "row-gap"
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

            toolbar(
                "Traceability Matrix",
                [{"label": "Export"}, {"label": "Filter"}],
            )
            st.markdown(
                f"""
                <div class="soho-grid-wrap"><table class="soho-grid">
                    <thead><tr>
                        <th>FR ID</th>
                        <th>Requirement</th>
                        <th>Test Script</th>
                        <th>Test Steps</th>
                        <th>Case Types</th>
                        <th>Status</th>
                    </tr></thead>
                    <tbody>{rtm_rows_html}</tbody>
                </table></div>
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

        # ---- Compile Record of Assurance CTA ----
        st.markdown("---")
        _cta_l, _cta_r = st.columns([2, 3])
        with _cta_l:
            st.markdown(
                """<style>
                div:has(#vsr-cta-anchor)
                ~ div[data-testid="stButton"] button {
                    background-color: #056696 !important;
                    border-color: #056696 !important;
                    color: #fff !important;
                    font-weight: 700;
                    font-size: 0.95rem;
                }
                div:has(#vsr-cta-anchor)
                ~ div[data-testid="stButton"] button:hover {
                    background-color: #044e73 !important;
                }
                </style>
                <span id="vsr-cta-anchor"
                 style="display:none;"></span>""",
                unsafe_allow_html=True,
            )
            if st.button(
                "Compile Record of Assurance",
                key="compile_vsr_btn",
                use_container_width=True,
            ):
                st.session_state["page"] = "10"
                st.rerun()
        with _cta_r:
            st.markdown(
                "<p style='font-size:0.82rem;"
                "color:#7a9ab0;padding-top:0.55rem;"
                "margin:0;'>"
                "Aggregate Validation Factory &amp; "
                "Traceability data into a "
                "GxP-ready Validation Summary Report.</p>",
                unsafe_allow_html=True,
            )


# ===================================================================
# Page 8 — Demo Comparison
# ===================================================================
elif page.startswith("8"):
    from utils.demo_comparison import (
        COST_PER_POOR_REQUIREMENT,
    )

    breadcrumb(["Home", "Demo Comparison"])
    page_header(
        "Demo Comparison",
        "Side-by-side: your draft vs Validation Factory "
        "audit-ready rewrite",
    )

    # Demo Comparison styles provided by soho_theme.css

    # ---- Demo mode auto-populate ----
    if st.session_state.get("demo_mode", False):
        st.info(
            "Demo Mode \u2014 showing sample LIMS data"
        )
        demo_dc = DEMO_DATA["demo_comparison"]
        if not st.session_state.get("dc_system_desc"):
            st.session_state["dc_system_desc"] = (
                demo_dc["system_description"]
            )
        for _di, _dr in enumerate(
            demo_dc["human_requirements"], 1,
        ):
            key = f"dc_req_{_di}"
            if not st.session_state.get(key):
                st.session_state[key] = _dr

    # ---- Input form ----
    sys_desc = st.text_area(
        "System Description",
        key="dc_system_desc",
        height=100,
        placeholder=(
            "e.g. LabCore LIMS v4.2 for sample tracking "
            "in a GMP-regulated pharma lab"
        ),
    )

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        req_1 = st.text_area(
            "Requirement 1",
            key="dc_req_1",
            height=100,
            placeholder="e.g. The system should track "
            "all samples quickly and easily",
        )
    with rc2:
        req_2 = st.text_area(
            "Requirement 2",
            key="dc_req_2",
            height=100,
            placeholder="e.g. Users need to sign off "
            "on results in a timely manner",
        )
    with rc3:
        req_3 = st.text_area(
            "Requirement 3",
            key="dc_req_3",
            height=100,
            placeholder="e.g. The system should store "
            "data in a robust way",
        )

    # ---- Analyze button ----
    if st.button(
        "Analyze & Compare", type="primary",
    ):
        if not (sys_desc or "").strip():
            st.warning(
                "Please enter a system description."
            )
        else:
            reqs_raw = [
                r for r in [req_1, req_2, req_3]
                if (r or "").strip()
            ]
            if not reqs_raw:
                st.warning(
                    "Please enter at least one "
                    "requirement."
                )
            else:
                from utils.demo_comparison import (
                    evaluate_requirements,
                    rewrite_requirement,
                )

                results: list = []
                for raw in reqs_raw:
                    ai_text, crit = (
                        rewrite_requirement(raw.strip())
                    )
                    ev = evaluate_requirements(
                        raw.strip(), ai_text, crit,
                    )
                    results.append(ev)
                st.session_state["dc_results"] = results

    # ---- Results display ----
    dc_results = st.session_state.get(
        "dc_results", None,
    )
    if dc_results:
        st.markdown("---")

        total_issues = sum(
            r["issue_count"] for r in dc_results
        )
        total_cost = sum(
            r["cost_of_error"] for r in dc_results
        )

        # KPI row
        kc1, kc2, kc3 = st.columns(3)
        kc1.metric(
            "Requirements Analyzed",
            len(dc_results),
        )
        kc2.metric("Total Issues Found", total_issues)
        kc3.metric(
            "Est. Cost of Error",
            f"${total_cost:,}",
        )

        # Cost banner
        st.markdown(
            f'<div class="soho-alert-banner">'
            f"Estimated cost of shipping these "
            f"requirements as-is: "
            f"<strong>${total_cost:,}</strong>"
            f"<br/>"
            f'<span style="font-size:0.82rem; '
            f'opacity:0.85;">'
            f"Based on industry average of "
            f"${COST_PER_POOR_REQUIREMENT:,} per "
            f"ambiguous or non-compliant requirement "
            f"(rework, audit findings, CAPAs)"
            f"</span></div>",
            unsafe_allow_html=True,
        )

        # ---- Side-by-side comparison table ----
        st.markdown("#### Requirement Comparison")

        table_rows_html = ""
        for idx, r in enumerate(dc_results, 1):
            crit_cls = (
                "badge-high"
                if r["criticality"].lower() == "high"
                else "badge-medium"
                if r["criticality"].lower() == "medium"
                else "badge-low"
            )
            risk_html = ""
            for b in r["risk_bullets"]:
                risk_html += (
                    f"<li>{b}</li>"
                )
            if not risk_html:
                risk_html = "<li>No issues</li>"

            table_rows_html += (
                f"<tr>"
                f"<td><strong>Req {idx}</strong>"
                f"<br/>{r['human_text']}</td>"
                f'<td>{r["ai_text"]}<br/>'
                f'<span class="badge {crit_cls}" '
                f'style="margin-top:0.4rem; '
                f'display:inline-block;">'
                f'{r["criticality"]}</span></td>'
                f'<td class="badge-error">'
                f"<ul style=\"margin:0; "
                f"padding-left:1.1rem;\">"
                f"{risk_html}</ul>"
                f"<br/>"
                f'<span style="font-weight:600;">'
                f"${r['cost_of_error']:,}</span>"
                f"</td></tr>"
            )

        st.markdown(
            f"""
            <div class="soho-grid-wrap"><table class="soho-grid">
                <thead><tr>
                    <th style="width:33%;">
                        Your Draft</th>
                    <th style="width:38%;">
                        Validation Factory (Audit Ready)</th>
                    <th style="width:29%;">
                        The Risk</th>
                </tr></thead>
                <tbody>{table_rows_html}</tbody>
            </table></div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Exports ----
        st.markdown("---")
        st.markdown("#### Export")
        ex1, ex2, ex3 = st.columns(3)

        # CSV download
        with ex1:
            csv_rows = []
            for r in dc_results:
                csv_rows.append({
                    "Human Draft": r["human_text"],
                    "AI Rewrite": r["ai_text"],
                    "Criticality": r["criticality"],
                    "Issues": r["issue_count"],
                    "Risk Bullets": "; ".join(
                        r["risk_bullets"],
                    ),
                    "Cost of Error": r["cost_of_error"],
                })
            dc_df = pd.DataFrame(csv_rows)
            st.download_button(
                "Download CSV",
                data=dc_df.to_csv(index=False),
                file_name=(
                    "demo_comparison_"
                    f"{datetime.utcnow():%Y%m%d_%H%M%S}"
                    ".csv"
                ),
                mime="text/csv",
                key="dc_csv_dl",
            )

        # PDF download
        with ex2:
            pdf_cols = [
                "Req #", "Your Draft",
                "AI Rewrite", "Criticality",
                "Issues", "Cost",
            ]
            pdf_rows = []
            for i, r in enumerate(dc_results, 1):
                pdf_rows.append((
                    str(i),
                    r["human_text"],
                    r["ai_text"],
                    r["criticality"],
                    str(r["issue_count"]),
                    f"${r['cost_of_error']:,}",
                ))
            dc_pdf = _build_table_pdf(
                "Demo Comparison Report",
                pdf_cols,
                pdf_rows,
            )
            st.download_button(
                "Download PDF",
                data=dc_pdf,
                file_name=(
                    "demo_comparison_"
                    f"{datetime.utcnow():%Y%m%d_%H%M%S}"
                    ".pdf"
                ),
                mime="application/pdf",
                key="dc_pdf_dl",
            )

        # Word Factory
        with ex3:
            docx_file = st.file_uploader(
                "Upload .docx template",
                type=["docx"],
                key="dc_docx_upload",
            )
            if docx_file is not None:
                from utils.demo_comparison import (
                    inject_into_docx,
                )

                populated = inject_into_docx(
                    template_bytes=docx_file.getvalue(),
                    system_desc=(
                        sys_desc or ""
                    ).strip(),
                    comparisons=dc_results,
                )
                st.download_button(
                    "Download Populated Template",
                    data=populated,
                    file_name=(
                        f"populated_"
                        f"{docx_file.name}"
                    ),
                    mime=(
                        "application/vnd.openxmlformats"
                        "-officedocument.wordprocessingml"
                        ".document"
                    ),
                    key="dc_docx_dl",
                )

elif page.startswith("9"):
    from frontend.components.compliance_command_center import (
        render_compliance_command_center,
    )

    breadcrumb(["Home", "Command Center"])
    page_header(
        "Compliance Command Center",
        "Risk exposure calculator and EVOLV vs Legacy "
        "benchmark dashboard",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        gap_count = st.number_input(
            "Compliance Gaps",
            min_value=0,
            value=5,
            step=1,
            key="ccc_gaps",
        )
    with c2:
        avg_fine = st.number_input(
            "Avg Audit Fine ($)",
            min_value=0.0,
            value=50000.0,
            step=5000.0,
            format="%.0f",
            key="ccc_fine",
        )
    with c3:
        delay_cost = st.number_input(
            "Delay Cost / Week ($)",
            min_value=0.0,
            value=15000.0,
            step=1000.0,
            format="%.0f",
            key="ccc_delay",
        )

    render_compliance_command_center(
        gap_count=int(gap_count),
        avg_audit_fine=float(avg_fine),
        delay_cost_per_week=float(delay_cost),
    )


# ===================================================================
# Page 10 — Validation Summary Report (VSR)
# ===================================================================
elif page.startswith("10"):

    # ── Inline GxP PDF generator ─────────────────────────────────
    def _generate_vsr_pdf(
        vsr_ur_fr: dict,
        vsr_ts: dict,
        vsr_rtm: dict,
        is_signed: bool = False,
        adversarial_result: dict = None,
    ) -> bytes:
        """Generate paginated GxP VSR PDF with e-sig placeholders.

        :requirement: URS-20.1 - Generate Validation Summary
        Report as GxP-compliant PDF.
        """
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        _risk = (
            (vsr_ur_fr or {})
            .get("user_requirement", {})
            .get("risk_level", "Unknown")
        )
        _urs_id = (vsr_ur_fr or {}).get("urs_id", "-")
        _ts_now = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"
        )

        class _VSRPDF(FPDF):
            def header(self):
                # — DRAFT watermark (disappears when signed) ────────
                if not is_signed:
                    _cx = self.w / 2
                    _cy = self.h / 2
                    self.set_font("Helvetica", "B", 70)
                    self.set_text_color(220, 220, 220)
                    _tw = self.get_string_width("DRAFT")
                    self.rotate(45, _cx, _cy)
                    self.text(_cx - _tw / 2, _cy, "DRAFT")
                    self.rotate(0)
                # — Branded header line ──────────────────────────────
                _eff = self.w - self.l_margin - self.r_margin
                _hw = _eff / 2
                _hy = self.get_y()
                self.set_font("Helvetica", "B", 8)
                self.set_text_color(5, 102, 150)
                self.set_xy(self.l_margin, _hy)
                self.cell(
                    _hw, 6,
                    "EVOLV | The Validation Factory",
                    new_x=XPos.RIGHT, new_y=YPos.TOP,
                )
                self.set_font("Helvetica", "", 8)
                self.set_text_color(120, 120, 120)
                self.set_xy(self.l_margin + _hw, _hy)
                self.cell(
                    _hw, 6,
                    f"VSR - {_urs_id} | {_ts_now}",
                    align="R",
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )
                self.set_draw_color(5, 102, 150)
                self.line(
                    self.l_margin,
                    self.get_y(),
                    self.w - self.r_margin,
                    self.get_y(),
                )
                self.ln(3)

            def footer(self):
                self.set_y(-12)
                self.set_font("Helvetica", "", 7)
                self.set_text_color(150, 150, 150)
                self.cell(
                    0, 8,
                    f"Page {self.page_no()} | EVOLV | "
                    "A WingstarTech Inc. Product | "
                    "CONFIDENTIAL",
                    align="C",
                )

        pdf = _VSRPDF(
            orientation="P", unit="mm", format="A4"
        )
        pdf.set_margins(18, 24, 18)
        pdf.set_auto_page_break(True, margin=18)

        def _h1(txt: str) -> None:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(5, 102, 150)
            pdf.cell(
                0, 8, _sanitize(txt),
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_draw_color(5, 102, 150)
            pdf.line(
                pdf.l_margin, pdf.get_y(),
                pdf.w - pdf.r_margin, pdf.get_y(),
            )
            pdf.ln(3)
            pdf.set_text_color(30, 30, 30)
            pdf.set_font("Helvetica", "", 10)

        def _h2(txt: str) -> None:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(
                0, 6, _sanitize(txt),
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_text_color(30, 30, 30)
            pdf.set_font("Helvetica", "", 9)

        def _sanitize(txt: str) -> str:
            """Replace non-Latin-1 chars so Helvetica core font survives."""
            _s = (
                str(txt)
                .replace("\u2022", "-")    # bullet •
                .replace("\u2013", "-")    # en dash
                .replace("\u2014", "-")    # em dash
                .replace("\u2018", "'")    # left single quote
                .replace("\u2019", "'")    # right single quote
                .replace("\u201c", '"')    # left double quote
                .replace("\u201d", '"')    # right double quote
                .replace("\u2026", "...")   # ellipsis
                .replace("\u2264", "<=")   # ≤
                .replace("\u2265", ">=")   # ≥
                .replace("\u2192", "->")   # right arrow →
                .replace("\u2190", "<-")   # left arrow ←
                .replace("\u2194", "<->")  # bidirectional ↔
                .replace("\u2122", "(TM)") # trademark (TM)
            )
            # Safety net: drop any remaining non-Latin-1 chars
            return _s.encode(
                "latin-1", errors="replace"
            ).decode("latin-1")

        def _kv(k: str, v: str) -> None:
            _kw = 52
            _vw = (
                pdf.w - pdf.l_margin - pdf.r_margin - _kw
            )
            _x0 = pdf.l_margin
            _y0 = pdf.get_y()
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(_x0, _y0)
            pdf.multi_cell(_kw, 5.5, _sanitize(k + ":"))
            _y1 = pdf.get_y()
            pdf.set_font("Helvetica", "", 8)
            pdf.set_xy(_x0 + _kw, _y0)
            pdf.multi_cell(_vw, 5.5, _sanitize(v))
            _y2 = pdf.get_y()
            pdf.set_y(max(_y1, _y2))

        def _body(txt: str) -> None:
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 5, _sanitize(txt))
            pdf.ln(1)

        # — Cover ——————————————————————————————————————————————————
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(5, 102, 150)
        pdf.ln(12)
        pdf.cell(
            0, 11,
            "Validation Summary Report",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(
            0, 7, "Record of Assurance",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(8)
        pdf.set_draw_color(5, 102, 150)
        pdf.set_line_width(0.5)
        pdf.line(
            pdf.l_margin, pdf.get_y(),
            pdf.w - pdf.r_margin, pdf.get_y(),
        )
        pdf.set_line_width(0.2)
        pdf.ln(7)
        pdf.set_text_color(30, 30, 30)
        _kv("URS ID", _urs_id)
        _kv("Risk Level", _risk)
        _kv(
            "Regulatory Framework",
            "GAMP 5 Rev 2 | 21 CFR Part 11 | CSA",
        )
        _kv("Generated", _ts_now)
        _kv("Compiled By", "EVOLV Validation Factory v0.1.0")

        # — Validation Summary —————————————————————————————————————
        pdf.add_page()
        _h1("1. Validation Summary")
        if vsr_ur_fr:
            _ur = vsr_ur_fr.get("user_requirement", {})
            _kv("UR ID", _ur.get("ur_id", "—"))
            _kv("Risk Assessment",
                _ur.get("risk_assessment", "—"))
            _kv("Implementation",
                _ur.get("implementation_method", "—"))
            _kv("Test Strategy",
                _ur.get("test_strategy", "—"))
            pdf.ln(2)
            _h2("Requirement Statement")
            _body(_ur.get("statement", "—"))
            _frs = vsr_ur_fr.get(
                "functional_requirements", []
            )
            if _frs:
                pdf.ln(1)
                _h2("Functional Requirements")
                for _f in _frs:
                    _body(
                        f"• {_f.get('fr_id','')}: "
                        f"{_f.get('statement','')}"
                    )
            _cn = vsr_ur_fr.get("compliance_notes", [])
            if _cn:
                pdf.ln(1)
                _h2("Compliance Notes")
                for _n in _cn:
                    _body(f"• {_n}")
        else:
            _body("No Validation Factory data available.")

        # — Traceability Coverage ——————————————————————————————————
        pdf.add_page()
        _h1("2. Traceability Coverage")
        if vsr_rtm:
            _kv("RTM ID", vsr_rtm.get("rtm_id", "—"))
            _kv(
                "Coverage",
                f"{vsr_rtm.get('coverage_percentage',0)}%",
            )
            _kv(
                "Total FRs",
                str(vsr_rtm.get("total_requirements", 0)),
            )
            _kv(
                "Covered",
                str(vsr_rtm.get(
                    "covered_requirements", 0
                )),
            )
            _kv(
                "Gaps",
                str(vsr_rtm.get("gap_requirements", 0)),
            )
        else:
            _body("Generate the RTM in the Traceability "
                  "tab to populate this section.")

        # — Adversarial Resilience & Edge Case Analysis ————————————
        pdf.add_page()
        _h1("3. Adversarial Resilience & Edge Case Analysis")
        if adversarial_result:
            _conf = adversarial_result.get(
                "assurance_confidence_score", 0
            )
            _rat = adversarial_result.get(
                "score_rationale", ""
            )
            _kv(
                "Assurance Confidence Score",
                f"{_conf} / 100",
            )
            _body(_sanitize(_rat))
            pdf.ln(3)
            _sts = adversarial_result.get(
                "stress_tests", []
            )
            if _sts:
                _cw_adv = [22, 38, 52, 62]
                pdf.set_fill_color(5, 102, 150)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 7)
                for _col, _cw_a in zip(
                    [
                        "Scenario",
                        "Type",
                        "Title",
                        "Failure Mode",
                    ],
                    _cw_adv,
                ):
                    pdf.cell(
                        _cw_a, 6, _col,
                        border=1, fill=True,
                    )
                pdf.ln()
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(30, 30, 30)
                pdf.set_font("Helvetica", "", 7)
                for _st_r in _sts:
                    _row_vals = [
                        _st_r.get("scenario_id", ""),
                        _st_r.get("type", ""),
                        _st_r.get("title", ""),
                        _st_r.get("failure_mode", ""),
                    ]
                    _row_y = pdf.get_y()
                    _row_x = pdf.l_margin
                    _heights = []
                    for _rv, _cw_a in zip(
                        _row_vals, _cw_adv
                    ):
                        _lines = (
                            pdf.get_string_width(
                                _sanitize(_rv)
                            ) / (_cw_a - 1)
                        )
                        _heights.append(
                            max(6, int(_lines + 1) * 5)
                        )
                    _max_h = max(_heights)
                    for _rv, _cw_a in zip(
                        _row_vals, _cw_adv
                    ):
                        pdf.set_xy(_row_x, _row_y)
                        pdf.multi_cell(
                            _cw_a, 5,
                            _sanitize(_rv),
                            border=1,
                        )
                        _row_x += _cw_a
                    pdf.set_y(_row_y + _max_h)
        else:
            _body(
                "Standard Validation Protocol — "
                "Adversarial Red-Teaming was not "
                "active during this session."
            )

        # — Performance Baseline ———————————————————————————————————
        pdf.add_page()
        _h1("4. Performance Baseline")
        if vsr_ts:
            _steps = vsr_ts.get("steps", [])
            _pos = sum(
                1 for s in _steps
                if s.get("test_case_type") == "Positive"
            )
            _neg = sum(
                1 for s in _steps
                if s.get("test_case_type") == "Negative"
            )
            _edge = sum(
                1 for s in _steps
                if s.get("test_case_type") == "Edge_Case"
            )
            _setup = sum(
                1 for s in _steps
                if s.get("step_type") == "Setup"
            )
            _exec_c = len(_steps) - _setup
            _adv_r = round(
                (_neg + _edge) / max(_exec_c, 1) * 100
            )
            _pb_rows = [
                ("Script ID",
                 _sanitize(vsr_ts.get("script_id", "-"))),
                ("Test Type",
                 _sanitize(vsr_ts.get("test_type", "-"))),
                ("Total Steps",         str(len(_steps))),
                ("Setup Steps",         str(_setup)),
                ("Positive Cases",      str(_pos)),
                ("Negative Cases",      str(_neg)),
                ("Edge Cases",          str(_edge)),
                ("Adversarial Coverage", f"{_adv_r}%"),
            ]
            _pb_cw = [90, 84]
            # — Header row (Infor Blue + white text) ──────────────
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(5, 102, 150)
            pdf.set_text_color(255, 255, 255)
            for _ph, _pw in zip(["Metric", "Value"], _pb_cw):
                pdf.cell(_pw, 7, _ph, border=1, fill=True)
            pdf.ln()
            # — Data rows (alternating light fill) ────────────────
            pdf.set_text_color(30, 30, 30)
            for _ri, (_mk, _mv) in enumerate(_pb_rows):
                if _ri % 2 == 0:
                    pdf.set_fill_color(240, 246, 251)
                else:
                    pdf.set_fill_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(_pb_cw[0], 6, _mk, border=1, fill=True)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(_pb_cw[1], 6, _mv, border=1, fill=True)
                pdf.ln()
            _qc = vsr_ts.get("quality_checklist", {})
            if _qc:
                pdf.ln(2)
                _h2("Quality Checklist")
                for _qk, _qv in _qc.items():
                    _m = "PASS" if _qv else "FAIL"
                    _body(
                        f"[{_m}] "
                        f"{_qk.replace('_', ' ').title()}"
                    )
        else:
            _body("No test script data available.")

        # — Drift Thresholds ———————————————————————————————————————
        pdf.add_page()
        _h1("5. Drift Thresholds")
        _body(
            "Acceptable drift limits per GAMP 5 risk "
            "classification. Active row reflects current "
            "document risk level."
        )
        pdf.ln(3)
        _thresh = [
            ("High",   "<= 5%",  "90 days",  "Rigorous Scripted"),
            ("Medium", "<= 10%", "180 days", "Hybrid"),
            ("Low",    "<= 20%", "365 days", "Unscripted"),
        ]
        _cw = [28, 28, 30, 54]
        _hdrs = [
            "Risk Level", "Drift Limit",
            "Re-validate", "Strategy",
        ]
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(5, 102, 150)     # Infor Blue
        pdf.set_text_color(255, 255, 255)   # white header text
        for _i, _hh in enumerate(_hdrs):
            pdf.cell(
                _cw[_i], 7, _hh,
                border=1, fill=True,
            )
        pdf.ln()
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        for _rl, _dl, _rv, _st_s in _thresh:
            _hl = _rl.lower() == _risk.lower()
            if _hl:
                pdf.set_fill_color(195, 228, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            for _i, _cv in enumerate(
                [_rl, _dl, _rv, _st_s]
            ):
                pdf.cell(
                    _cw[_i], 6, _cv,
                    border=1, fill=True,
                )
            pdf.ln()

        # — PCCP Roadmap ———————————————————————————————————————————
        pdf.add_page()
        _h1("6. PCCP Roadmap")
        _body(
            f"Post-Correction & Change of Practice roadmap "
            f"for {_risk} Risk classification."
        )
        pdf.ln(2)
        _milestones = [
            ("Q1 — Month 1",
             "Initial baseline validation, IQ/OQ, "
             "UAT sign-off"),
        ]
        if _risk.lower() == "high":
            _milestones.append((
                "Q1 — Week 4",
                "Adversarial re-test & Model Card v1.0",
            ))
        _milestones += [
            ("Q2", "Drift assessment, compliance gap review, "
             "CAPA if threshold breached"),
            ("Q3", "Mid-cycle performance audit, "
             "corrective action review"),
            ("Q4", "Annual re-validation, PCCP update, "
             "regulatory version check"),
        ]
        for _mq, _md in _milestones:
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(
                34, 5.5, _sanitize(_mq) + ":",
                new_x=XPos.RIGHT, new_y=YPos.TOP,
            )
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(
                0, 5.5, _sanitize(_md),
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )

        # — Model Card (High Risk only) ————————————————————————————
        if _risk.lower() == "high":
            pdf.add_page()
            _h1("7. Model Card")
            _body(
                "Auto-attached: High Risk classification "
                "requires Model Card per FDA AI/ML SAMD "
                "guidance."
            )
            pdf.ln(2)
            _kv("System", "EVOLV Validation Factory")
            _kv("Version", "0.1.0")
            _kv("Risk Class",
                f"{_risk} (GAMP 5 Cat. 5)")
            _kv(
                "Intended Use",
                "Automated CSA/CSV document generation "
                "for GxP systems",
            )
            _kv(
                "Reg. Framework",
                "GAMP 5 Rev 2 | 21 CFR Part 11 | ICH Q10",
            )
            pdf.ln(2)
            _h2("Limitations")
            for _lim in [
                "Output requires qualified human review "
                "before regulatory submission.",
                "Accuracy depends on completeness of "
                "ingested regulatory documents.",
                "Not a substitute for Qualified Person "
                "(QP) oversight.",
            ]:
                _body(f"• {_lim}")

            # — 90-Day Health Check ————————————————————————————————
            pdf.add_page()
            _h1("8. 90-Day Health Check Schedule")
            _body(
                "Auto-attached: High Risk mandates "
                "90-day monitoring per GAMP 5 §10.4."
            )
            pdf.ln(2)
            _hc = [
                ("Week 1",  "Establish performance baseline"),
                ("Week 2",  "Initial compliance gap review"),
                ("Week 4",  "First drift measurement"),
                ("Week 6",  "Mid-period adversarial re-test"),
                ("Week 8",  "Corrective action review "
                            "(CAPA if drift > 5%)"),
                ("Week 10", "Documentation update"),
                ("Week 12", "Full re-validation & "
                            "new VSR for QA sign-off"),
            ]
            for _wk, _wt in _hc:
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(
                    26, 5.5, _sanitize(_wk) + ":",
                    new_x=XPos.RIGHT, new_y=YPos.TOP,
                )
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(
                    0, 5.5, _sanitize(_wt),
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )

        # — E-Signature Placeholders ———————————————————————————————
        pdf.add_page()
        _h1("Electronic Signature — Manifestation")
        _body(
            "In accordance with 21 CFR Part 11, the "
            "following signatures constitute legally binding "
            "approval of this Validation Summary Report."
        )
        pdf.ln(5)
        _sigs = [
            ("Document Author",    "Validation Engineer"),
            ("Quality Reviewer",   "Quality Assurance Lead"),
            ("System Owner",       "IT / Operations Lead"),
            ("Regulatory Approver","Regulatory Affairs"),
        ]
        for _sn, _sr in _sigs:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(
                0, 6, _sn,
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(
                0, 5, f"Role: {_sr}",
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_text_color(30, 30, 30)
            pdf.ln(2)
            _sx = pdf.l_margin
            _sy = pdf.get_y() + 4
            pdf.set_draw_color(120, 120, 120)
            pdf.set_font("Helvetica", "", 8)
            # Signature label + underline
            pdf.set_xy(_sx, pdf.get_y())
            pdf.cell(
                22, 5, "Signature:",
                new_x=XPos.RIGHT, new_y=YPos.TOP,
            )
            pdf.line(_sx + 22, _sy, _sx + 90, _sy)
            # Date label + underline (offset right)
            pdf.set_xy(_sx + 95, pdf.get_y())
            pdf.cell(
                16, 5, "Date:",
                new_x=XPos.RIGHT, new_y=YPos.TOP,
            )
            pdf.line(
                _sx + 111, _sy, _sx + 150, _sy,
            )
            pdf.ln(10)

        return bytes(pdf.output())

    # ── Pull aggregated data from upstream modules ────────────────
    _vsr_ur_fr = st.session_state.get("vf_ur_fr")
    _vsr_ts    = st.session_state.get("vf_test_script")
    _vsr_rtm   = st.session_state.get("rtm_result")
    _vsr_demo  = st.session_state.get("demo_mode", False)
    if _vsr_demo:
        _vsr_ur_fr = _vsr_ur_fr or DEMO_DATA.get("ur_fr")
        _vsr_ts    = _vsr_ts    or DEMO_DATA.get("test_script")
        _vsr_rtm   = _vsr_rtm   or DEMO_DATA.get("rtm")
    _vsr_ok = _vsr_ur_fr is not None

    # ── Handle "Compile Record of Assurance" from sidebar ─────────
    _vsr_adv = st.session_state.get(
        "vf_adversarial_result"
    )
    if st.session_state.pop("_compile_vsr_requested", False):
        if _vsr_ok:
            st.session_state["_vsr_preview_bytes"] = (
                _generate_vsr_pdf(
                    _vsr_ur_fr, _vsr_ts, _vsr_rtm,
                    adversarial_result=_vsr_adv,
                )
            )

    # ── Breadcrumb ────────────────────────────────────────────────
    breadcrumb(["Home", "Traceability", "VSR"])

    # ── Top bar: title + GxP PDF export (top-right) ──────────────
    _vsr_hdr_col, _vsr_pdf_col = st.columns([5, 1])
    with _vsr_hdr_col:
        page_header(
            "Validation Summary Report",
            "Consolidated GxP assurance record "
            "· PCCP-ready · 21 CFR Part 11",
        )
    with _vsr_pdf_col:
        st.markdown(
            "<div style='height:1.5rem;'></div>",
            unsafe_allow_html=True,
        )
        if _vsr_ok:
            _vsr_pdf_bytes = (
                st.session_state.get("_vsr_preview_bytes")
                or _generate_vsr_pdf(
                    _vsr_ur_fr, _vsr_ts, _vsr_rtm,
                    adversarial_result=_vsr_adv,
                )
            )
            st.download_button(
                "⬇ GxP PDF",
                data=_vsr_pdf_bytes,
                file_name=(
                    "VSR_"
                    f"{datetime.utcnow():%Y%m%d_%H%M%S}"
                    ".pdf"
                ),
                mime="application/pdf",
                key="vsr_gxp_pdf_btn",
                type="primary",
            )

    # ── Live Preview (when compiled from sidebar button) ──────────
    if "_vsr_preview_bytes" in st.session_state:
        import base64 as _b64mod
        _pdf_b64 = _b64mod.b64encode(
            st.session_state["_vsr_preview_bytes"]
        ).decode()
        st.markdown(
            "#### Live Preview — Record of Assurance"
        )
        st.components.v1.html(
            f'<iframe src="data:application/pdf;base64,'
            f'{_pdf_b64}" width="100%" height="800" '
            f'style="border:none; border-radius:6px;">'
            f"</iframe>",
            height=820,
        )
        st.markdown("---")

    # ── Gate: require upstream data ───────────────────────────────
    if not _vsr_ok:
        empty_state(
            "No Validation Data",
            "Complete the Validation Factory and "
            "Traceability workflows, then click "
            "'Compile Record of Assurance' in the "
            "Traceability tab.",
            icon="file-shield",
            action_label="Go to Validation Factory",
        )
    else:
        # ── Derived values ────────────────────────────────────────
        _vsr_risk = (
            _vsr_ur_fr
            .get("user_requirement", {})
            .get("risk_level", "Medium")
        )
        _vsr_is_high = _vsr_risk.lower() == "high"
        _vsr_cov = (
            _vsr_rtm.get("coverage_percentage", 0)
            if _vsr_rtm else 0
        )
        _vsr_steps = (
            _vsr_ts.get("steps", []) if _vsr_ts else []
        )
        _vsr_pos = sum(
            1 for s in _vsr_steps
            if s.get("test_case_type") == "Positive"
        )
        _vsr_neg = sum(
            1 for s in _vsr_steps
            if s.get("test_case_type") == "Negative"
        )
        _vsr_edge = sum(
            1 for s in _vsr_steps
            if s.get("test_case_type") == "Edge_Case"
        )
        _vsr_setup = sum(
            1 for s in _vsr_steps
            if s.get("step_type") == "Setup"
        )
        _vsr_exec = len(_vsr_steps) - _vsr_setup
        _vsr_adv = round(
            (_vsr_neg + _vsr_edge)
            / max(_vsr_exec, 1) * 100
        )

        # ── Status badge helper ───────────────────────────────────
        def _vbadge(ok: bool) -> str:
            if ok:
                return (
                    '<span class="badge badge-low"'
                    ' style="font-size:0.62rem;">'
                    "&#10003;&nbsp;Verified</span>"
                )
            return (
                '<span class="badge badge-medium"'
                ' style="font-size:0.62rem;">'
                "&#9888;&nbsp;Review&nbsp;Required</span>"
            )

        # ── Section registry ──────────────────────────────────────
        _vsr_secs = [
            (
                "validation-summary",
                "Validation Summary",
                _vsr_ur_fr is not None,
            ),
            (
                "traceability",
                "Traceability Coverage",
                _vsr_rtm is not None and _vsr_cov >= 80,
            ),
            (
                "performance",
                "Performance Baseline",
                _vsr_ts is not None,
            ),
            ("drift", "Drift Thresholds", True),
            ("pccp",  "PCCP Roadmap",     True),
        ]
        if _vsr_is_high:
            _vsr_secs += [
                ("model-card",   "Model Card",         True),
                ("health-check", "90-Day Health Check", True),
            ]

        # ── Active section state ──────────────────────────────────
        if "vsr_active_section" not in st.session_state:
            st.session_state.vsr_active_section = (
                "validation-summary"
            )
        _vsr_active = st.session_state.vsr_active_section

        # ── Page-scoped CSS ───────────────────────────────────────
        st.markdown(
            """
            <style>
            .vsr-nav-badge {
                font-size: 0.6rem;
                display: block;
                margin: -0.25rem 0 0.35rem 0;
            }
            .vsr-section-card {
                border: 1px solid #1e2d3d;
                border-radius: 6px;
                padding: 1.1rem 1.3rem 0.9rem;
                margin-bottom: 0.9rem;
                background: rgba(20, 30, 44, 0.55);
            }
            .vsr-section-title {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.7rem;
                padding-bottom: 0.45rem;
                border-bottom: 1px solid #253647;
                font-size: 1rem;
                font-weight: 700;
                color: #e8f4fb;
            }
            .vsr-kv-row {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 0.35rem;
                font-size: 0.83rem;
            }
            .vsr-kv-key {
                font-weight: 600;
                color: #8fb4cc;
                min-width: 9rem;
            }
            .vsr-kv-val { color: #d8eaf5; }
            .vsr-thresh-tbl {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.8rem;
                margin-top: 0.5rem;
            }
            .vsr-thresh-tbl th {
                background: #0c1e30;
                color: #6aaed4;
                padding: 0.4rem 0.65rem;
                text-align: left;
                border-bottom: 2px solid #056696;
            }
            .vsr-thresh-tbl td {
                padding: 0.38rem 0.65rem;
                border-bottom: 1px solid #1e2d3d;
                color: #c0d8e8;
            }
            .vsr-thresh-tbl tr.vsr-active-row td {
                background: rgba(5,102,150,0.2);
                color: #e8f4fb;
                font-weight: 700;
            }
            .vsr-pccp-item {
                display: flex;
                gap: 0.9rem;
                margin-bottom: 0.65rem;
                align-items: flex-start;
            }
            .vsr-pccp-q {
                min-width: 5rem;
                font-weight: 700;
                font-size: 0.82rem;
                padding-top: 0.1rem;
            }
            .vsr-pccp-desc {
                font-size: 0.82rem;
                color: #c0d8e8;
            }
            .vsr-check-ok  { color: #4caf50; font-weight: 700; }
            .vsr-check-fail{ color: #f44336; font-weight: 700; }
            .vsr-checklist-item {
                display: flex;
                gap: 0.5rem;
                font-size: 0.82rem;
                margin-bottom: 0.28rem;
                color: #c0d8e8;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ── Master-Detail layout ──────────────────────────────────
        _nav_c, _cnt_c = st.columns([1, 3])

        # LEFT — Vertical scroll-spy nav ──────────────────────────
        with _nav_c:
            st.markdown(
                "<p style='font-size:0.68rem;font-weight:700;"
                "letter-spacing:0.07em;color:#6a8fa6;"
                "text-transform:uppercase;"
                "margin-bottom:0.4rem;'>"
                "Report Sections</p>",
                unsafe_allow_html=True,
            )
            for _sid, _slabel, _sok in _vsr_secs:
                _act = _sid == _vsr_active
                _bl = (
                    "3px solid #056696;"
                    if _act else
                    "3px solid #1e2d3d;"
                )
                _bg = (
                    "background:rgba(5,102,150,0.14);"
                    if _act else ""
                )
                _fc = "#056696" if _act else "#8aa8bc"
                _fw = "700" if _act else "400"
                st.markdown(
                    f'<div style="padding:0.45rem 0.55rem '
                    f'0.05rem;border-left:{_bl}{_bg}'
                    f'border-radius:0 4px 4px 0;'
                    f'margin-bottom:0.05rem;">'
                    f'<span style="font-size:0.78rem;'
                    f'font-weight:{_fw};color:{_fc};">'
                    f'{_slabel}</span><br/>'
                    f'<span class="vsr-nav-badge">'
                    f'{_vbadge(_sok)}</span></div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "→ View",
                    key=f"vsr_nav_{_sid}",
                    use_container_width=True,
                ):
                    st.session_state.vsr_active_section = (
                        _sid
                    )
                    st.rerun()

        # RIGHT — Content card ─────────────────────────────────────
        with _cnt_c:

            def _card_open(title: str, ok: bool) -> None:
                st.markdown(
                    f'<div class="vsr-section-card">'
                    f'<div class="vsr-section-title">'
                    f"{title}&ensp;{_vbadge(ok)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            def _card_close() -> None:
                st.markdown(
                    "</div>", unsafe_allow_html=True
                )

            def _kv_html(k: str, v: str) -> None:
                st.markdown(
                    f'<div class="vsr-kv-row">'
                    f'<span class="vsr-kv-key">{k}</span>'
                    f'<span class="vsr-kv-val">{v}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # ── Section: Validation Summary ───────────────────────
            if _vsr_active == "validation-summary":
                _card_open(
                    "Validation Summary",
                    _vsr_ur_fr is not None,
                )
                _ur_d = _vsr_ur_fr.get(
                    "user_requirement", {}
                )
                _kv_html(
                    "URS ID",
                    _vsr_ur_fr.get("urs_id", "—"),
                )
                _kv_html(
                    "UR ID", _ur_d.get("ur_id", "—"),
                )
                _kv_html(
                    "Risk Level",
                    _ur_d.get("risk_level", "—"),
                )
                _kv_html(
                    "Risk Assessment",
                    _ur_d.get("risk_assessment", "—"),
                )
                _kv_html(
                    "Implementation",
                    _ur_d.get(
                        "implementation_method", "—"
                    ),
                )
                _kv_html(
                    "Test Strategy",
                    _ur_d.get("test_strategy", "—"),
                )
                st.markdown(
                    "<p style='margin:0.8rem 0 0.25rem;"
                    "font-weight:700;font-size:0.82rem;"
                    "color:#6aaed4;'>Requirement</p>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<blockquote style='border-left:"
                    f"3px solid #056696;padding:"
                    f"0.38rem 0.75rem;font-size:0.85rem;"
                    f"color:#d8eaf5;margin:0;"
                    f"font-style:italic;'>"
                    f"{_ur_d.get('statement', '—')}"
                    f"</blockquote>",
                    unsafe_allow_html=True,
                )
                _frs_d = _vsr_ur_fr.get(
                    "functional_requirements", []
                )
                if _frs_d:
                    st.markdown(
                        "<p style='margin:0.8rem 0 0.25rem;"
                        "font-weight:700;font-size:0.82rem;"
                        "color:#6aaed4;'>"
                        "Functional Requirements</p>",
                        unsafe_allow_html=True,
                    )
                    for _fr_i in _frs_d:
                        _kv_html(
                            _fr_i.get("fr_id", ""),
                            _fr_i.get("statement", ""),
                        )
                _cn_d = _vsr_ur_fr.get(
                    "compliance_notes", []
                )
                if _cn_d:
                    st.markdown(
                        "<p style='margin:0.8rem 0 0.25rem;"
                        "font-weight:700;font-size:0.82rem;"
                        "color:#6aaed4;'>"
                        "Compliance Notes</p>",
                        unsafe_allow_html=True,
                    )
                    for _n_i in _cn_d:
                        st.markdown(
                            f"<p style='font-size:0.8rem;"
                            f"color:#9abccc;margin:0.18rem 0;"
                            f"'>• {_n_i}</p>",
                            unsafe_allow_html=True,
                        )
                _card_close()

            # ── Section: Traceability Coverage ────────────────────
            elif _vsr_active == "traceability":
                _tc_ok = (
                    _vsr_rtm is not None
                    and _vsr_cov >= 80
                )
                _card_open("Traceability Coverage", _tc_ok)
                if _vsr_rtm:
                    _tc1, _tc2, _tc3, _tc4 = st.columns(4)
                    _tc1.metric(
                        "Total FRs",
                        _vsr_rtm.get(
                            "total_requirements", 0
                        ),
                    )
                    _tc2.metric(
                        "Covered",
                        _vsr_rtm.get(
                            "covered_requirements", 0
                        ),
                    )
                    _tc3.metric(
                        "Gaps",
                        _vsr_rtm.get(
                            "gap_requirements", 0
                        ),
                    )
                    _tc4.metric(
                        "Coverage", f"{_vsr_cov}%"
                    )
                    _tp = int(_vsr_cov)
                    _tb = (
                        "green" if _tp >= 80
                        else "amber" if _tp >= 50
                        else "red"
                    )
                    st.markdown(
                        f'<div class="soho-progress"'
                        f' style="margin:0.75rem 0 0.2rem;">'
                        f'<div class="soho-progress-fill'
                        f' {_tb}" style="width:{_tp}%;">'
                        f'</div></div>'
                        f'<p style="font-size:0.75rem;'
                        f'color:#8aa8bc;margin:0;">'
                        f"{_tp}% requirement coverage</p>",
                        unsafe_allow_html=True,
                    )
                    _rrows = _vsr_rtm.get("rows", [])
                    if _rrows:
                        st.markdown(
                            "<p style='margin:0.8rem 0 "
                            "0.25rem;font-weight:700;"
                            "font-size:0.82rem;"
                            "color:#6aaed4;'>"
                            "FR Coverage Detail</p>",
                            unsafe_allow_html=True,
                        )
                        for _rr in _rrows[:12]:
                            _rst = _rr.get(
                                "coverage_status", "—"
                            )
                            _ric = (
                                "&#10003;" if _rst == "Covered"
                                else "&#10007;"
                            )
                            _rcl = (
                                "badge-low"
                                if _rst == "Covered"
                                else "badge-high"
                            )
                            _req_s = _rr.get(
                                "requirement_statement", ""
                            )[:58]
                            st.markdown(
                                f'<div class="vsr-kv-row">'
                                f'<span class="vsr-kv-key">'
                                f"{_rr.get('fr_id','')}"
                                f"</span>"
                                f'<span class="vsr-kv-val">'
                                f'<span class="badge {_rcl}"'
                                f' style="font-size:0.6rem;">'
                                f"{_ric} {_rst}</span>"
                                f"&ensp;{_req_s}"
                                f"</span></div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.info(
                        "Generate the RTM in the "
                        "Traceability tab first."
                    )
                _card_close()

            # ── Section: Performance Baseline ─────────────────────
            elif _vsr_active == "performance":
                _card_open(
                    "Performance Baseline",
                    _vsr_ts is not None,
                )
                if _vsr_ts:
                    _pb1, _pb2, _pb3, _pb4 = st.columns(4)
                    _pb1.metric(
                        "Total Steps", len(_vsr_steps)
                    )
                    _pb2.metric("Positive", _vsr_pos)
                    _pb3.metric("Negative", _vsr_neg)
                    _pb4.metric("Edge Cases", _vsr_edge)
                    _abw = min(_vsr_adv, 100)
                    _abc = (
                        "green" if _abw >= 40 else "amber"
                    )
                    st.markdown(
                        f'<div style="margin:0.75rem 0 0.2rem">'
                        f'<span style="font-size:0.82rem;'
                        f'font-weight:700;color:#6aaed4;">'
                        f"Adversarial Coverage:&ensp;</span>"
                        f'<span class="badge '
                        f'{"badge-low" if _abw >= 40 else "badge-medium"}'
                        f'" style="font-size:0.72rem;">'
                        f"{_vsr_adv}%</span></div>"
                        f'<div class="soho-progress">'
                        f'<div class="soho-progress-fill'
                        f' {_abc}" style="width:{_abw}%;">'
                        f'</div></div>'
                        f'<p style="font-size:0.73rem;'
                        f"color:#8aa8bc;margin:0.2rem 0 "
                        f"0.75rem;\">"
                        f"Negative + Edge vs execution "
                        f"steps</p>",
                        unsafe_allow_html=True,
                    )
                    _qc_d = _vsr_ts.get(
                        "quality_checklist", {}
                    )
                    if _qc_d:
                        st.markdown(
                            "<p style='margin:0.3rem 0 "
                            "0.25rem;font-weight:700;"
                            "font-size:0.82rem;"
                            "color:#6aaed4;'>"
                            "Quality Checklist</p>",
                            unsafe_allow_html=True,
                        )
                        for _qk, _qv in _qc_d.items():
                            _qic = (
                                '<span class="vsr-check-ok">'
                                "✓</span>"
                                if _qv else
                                '<span class="vsr-check-fail">'
                                "✗</span>"
                            )
                            st.markdown(
                                f'<div class="vsr-checklist'
                                f'-item">{_qic}&ensp;'
                                f"{_qk.replace('_',' ').title()}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.info(
                        "Generate test scripts in the "
                        "Validation Factory tab first."
                    )
                _card_close()

            # ── Section: Drift Thresholds ─────────────────────────
            elif _vsr_active == "drift":
                _card_open("Drift Thresholds", True)
                st.markdown(
                    "<p style='font-size:0.82rem;"
                    "color:#8aa8bc;margin-bottom:0.75rem;'>"
                    "Acceptable drift limits per GAMP 5 risk "
                    "classification. The highlighted row "
                    "reflects this document's risk level.</p>",
                    unsafe_allow_html=True,
                )
                _dt_rows = [
                    (
                        "High", "≤ 5%", "90 days",
                        "Rigorous Scripted",
                        "Mandatory re-validate after any "
                        "change event",
                    ),
                    (
                        "Medium", "≤ 10%", "180 days",
                        "Hybrid",
                        "Scripted + unscripted review cycle",
                    ),
                    (
                        "Low", "≤ 20%", "365 days",
                        "Unscripted",
                        "Annual exploratory charter",
                    ),
                ]
                _tbl = (
                    '<table class="vsr-thresh-tbl">'
                    "<thead><tr>"
                    "<th>Risk Level</th>"
                    "<th>Drift Limit</th>"
                    "<th>Re-validate</th>"
                    "<th>Strategy</th>"
                    "<th>Note</th>"
                    "</tr></thead><tbody>"
                )
                for _drl, _ddl, _drv, _dst, _dnt in _dt_rows:
                    _dact = (
                        "vsr-active-row"
                        if _drl.lower() == _vsr_risk.lower()
                        else ""
                    )
                    _tbl += (
                        f'<tr class="{_dact}">'
                        f"<td><strong>{_drl}</strong></td>"
                        f"<td>{_ddl}</td>"
                        f"<td>{_drv}</td>"
                        f"<td>{_dst}</td>"
                        f"<td>{_dnt}</td>"
                        f"</tr>"
                    )
                _tbl += "</tbody></table>"
                st.markdown(_tbl, unsafe_allow_html=True)
                _card_close()

            # ── Section: PCCP Roadmap ─────────────────────────────
            elif _vsr_active == "pccp":
                _card_open("PCCP Roadmap", True)
                st.markdown(
                    f"<p style='font-size:0.82rem;"
                    f"color:#8aa8bc;margin-bottom:0.75rem;'>"
                    f"Post-Correction &amp; Change of "
                    f"Practice roadmap for "
                    f"<strong style='color:#e8f4fb;'>"
                    f"{_vsr_risk} Risk</strong> "
                    f"classification. Aligns with GAMP 5 "
                    f"lifecycle and CSA proportionality "
                    f"principle.</p>",
                    unsafe_allow_html=True,
                )
                _pm_items = [
                    (
                        "Q1 — Month 1",
                        "Initial baseline validation, "
                        "IQ/OQ execution, UAT sign-off",
                        "#056696",
                    ),
                ]
                if _vsr_is_high:
                    _pm_items.append((
                        "Q1 — Week 4",
                        "Adversarial test re-run and "
                        "Model Card v1.0 publication",
                        "#d97c2a",
                    ))
                _pm_items += [
                    (
                        "Q2",
                        "First drift assessment, compliance "
                        "gap review, CAPA if drift exceeds "
                        "threshold",
                        "#3a7ea8",
                    ),
                    (
                        "Q3",
                        "Mid-cycle performance audit, "
                        "corrective action review, "
                        "stakeholder sign-off",
                        "#3a7ea8",
                    ),
                    (
                        "Q4",
                        "Annual re-validation, PCCP update, "
                        "regulatory version check, new VSR",
                        "#3a7ea8",
                    ),
                ]
                for _pq, _pd, _pc in _pm_items:
                    st.markdown(
                        f'<div class="vsr-pccp-item">'
                        f'<div class="vsr-pccp-q"'
                        f' style="color:{_pc};">'
                        f"{_pq}</div>"
                        f'<div class="vsr-pccp-desc">'
                        f"{_pd}</div></div>",
                        unsafe_allow_html=True,
                    )
                _card_close()

            # ── Section: Model Card (High Risk only) ──────────────
            elif (
                _vsr_active == "model-card"
                and _vsr_is_high
            ):
                _card_open("Model Card", True)
                st.markdown(
                    "<p style='font-size:0.78rem;"
                    "color:#d4922a;font-style:italic;"
                    "margin-bottom:0.75rem;'>"
                    "&#9888;&nbsp;Auto-attached: High Risk "
                    "classification requires a Model Card "
                    "per FDA AI/ML SAMD guidance.</p>",
                    unsafe_allow_html=True,
                )
                _mc = {
                    "System": "EVOLV Validation Factory",
                    "Version": "0.1.0",
                    "Risk Class": (
                        f"{_vsr_risk} (GAMP 5 Cat. 5)"
                    ),
                    "Intended Use": (
                        "Automated CSA/CSV document "
                        "generation for GxP systems"
                    ),
                    "Reg. Framework": (
                        "GAMP 5 Rev 2 | 21 CFR Part 11 "
                        "| ICH Q10"
                    ),
                    "Knowledge Base": (
                        "GAMP 5 & CSA guidance "
                        "(Pinecone vector store)"
                    ),
                    "Output Types": (
                        "URS · UR/FR · Test Scripts "
                        "· RTM · VSR"
                    ),
                }
                for _mk, _mv in _mc.items():
                    _kv_html(_mk, _mv)
                st.markdown(
                    "<p style='margin:0.8rem 0 0.25rem;"
                    "font-weight:700;font-size:0.82rem;"
                    "color:#6aaed4;'>Limitations</p>",
                    unsafe_allow_html=True,
                )
                for _lim in [
                    "Output requires qualified human "
                    "expert review before regulatory "
                    "submission.",
                    "Accuracy depends on completeness "
                    "of ingested regulatory documents.",
                    "Not a substitute for Qualified "
                    "Person (QP) oversight.",
                    "Embeddings are point-in-time — "
                    "re-ingest after regulatory updates.",
                ]:
                    st.markdown(
                        f"<p style='font-size:0.8rem;"
                        f"color:#9abccc;margin:0.18rem 0;"
                        f"'>• {_lim}</p>",
                        unsafe_allow_html=True,
                    )
                _card_close()

            # ── Section: 90-Day Health Check ──────────────────────
            elif (
                _vsr_active == "health-check"
                and _vsr_is_high
            ):
                _card_open("90-Day Health Check", True)
                st.markdown(
                    "<p style='font-size:0.78rem;"
                    "color:#d4922a;font-style:italic;"
                    "margin-bottom:0.75rem;'>"
                    "&#9888;&nbsp;Auto-attached: High Risk "
                    "mandates a 90-day monitoring schedule "
                    "per GAMP 5 §10.4 and CSA guidance.</p>",
                    unsafe_allow_html=True,
                )
                _hcs = [
                    (
                        "Week 1",
                        "Establish performance baseline: "
                        "record step counts, coverage %, "
                        "adversarial ratio",
                    ),
                    (
                        "Week 2",
                        "Initial compliance gap review: "
                        "verify all FRs have test coverage",
                    ),
                    (
                        "Week 4",
                        "First drift measurement: compare "
                        "against baseline thresholds (≤ 5%)",
                    ),
                    (
                        "Week 6",
                        "Mid-period adversarial re-test: "
                        "re-run all negative & edge cases",
                    ),
                    (
                        "Week 8",
                        "Corrective action review: "
                        "initiate CAPA if drift > threshold",
                    ),
                    (
                        "Week 10",
                        "Documentation update: refresh "
                        "URS/UR-FR if system scope changed",
                    ),
                    (
                        "Week 12",
                        "Full re-validation: generate new "
                        "VSR and obtain QA sign-off",
                    ),
                ]
                for _hw, _ht in _hcs:
                    st.markdown(
                        f'<div class="vsr-pccp-item">'
                        f'<div class="vsr-pccp-q"'
                        f' style="color:#056696;">'
                        f"{_hw}</div>"
                        f'<div class="vsr-pccp-desc">'
                        f"{_ht}</div></div>",
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    "<p style='margin:0.75rem 0 0.25rem;"
                    "font-weight:700;font-size:0.82rem;"
                    "color:#6aaed4;'>Sign-off Checklist</p>",
                    unsafe_allow_html=True,
                )
                for _ci in [
                    "Audit trail reviewed and verified",
                    "Test coverage ≥ 80% maintained",
                    "No unresolved CAPAs outstanding",
                    "Model Card updated if system changed",
                    "Regulatory version drift checked",
                    "Stakeholder sign-off obtained",
                ]:
                    st.markdown(
                        f'<div class="vsr-checklist-item">'
                        f'<span style="color:#5a8098;">'
                        f"&#9744;</span>&ensp;{_ci}</div>",
                        unsafe_allow_html=True,
                    )
                _card_close()


# ===================================================================
# Page 11 — EVOLV Sentinel
# ===================================================================
elif page.startswith("11"):

    breadcrumb(["Home", "EVOLV Sentinel"])
    page_header(
        "EVOLV Sentinel",
        "Change Impact Assessment — GxP Traceability & IAR Engine",
    )

    # ── Local card helpers ────────────────────────────────────────
    def _card_open(title: str, icon: str = "") -> None:
        _ico = (
            f'<i class="fa-solid {icon}"'
            f' style="margin-right:0.4rem;"></i>'
            if icon else ""
        )
        st.markdown(
            f'<div class="vsr-section-card">'
            f'<div class="vsr-section-title">'
            f"{_ico}{title}</div>",
            unsafe_allow_html=True,
        )

    def _card_close() -> None:
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Load traceability graph ───────────────────────────────────
    SENTINEL_GRAPH = (
        PROJECT_ROOT / "Agents" / "sentinel"
        / "traceability_sample.json"
    )
    _sentinel_graph_ok = SENTINEL_GRAPH.exists()
    if not _sentinel_graph_ok:
        st.error(
            f"Traceability graph not found: `{SENTINEL_GRAPH}`. "
            "Run `scripts/setup_sentinel.py` to initialise."
        )

    # ── Diff Input ───────────────────────────────────────────────
    _card_open("Paste Git Diff", icon="fa-code-compare")
    diff_text = st.text_area(
        "Paste git diff",
        height=200,
        placeholder="git diff HEAD~1",
        key="sentinel_diff_input",
        label_visibility="collapsed",
    )
    st.caption(
        "Tip: run `git diff HEAD~1` in your project root "
        "and paste the output here."
    )
    run_btn = st.button(
        "Run Impact Analysis",
        type="primary",
        key="sentinel_run",
        disabled=not _sentinel_graph_ok,
    )
    _card_close()

    # ── Analysis ─────────────────────────────────────────────────
    if run_btn and diff_text.strip():
        try:
            from Agents.sentinel import (
                ImpactEngine,
                JustificationEngine,
            )
            _ie = ImpactEngine.from_file(SENTINEL_GRAPH)
            _report = _ie.analyze(diff_text)
            st.session_state["sentinel_report"] = (
                _ie.to_dict(_report)
            )
            st.session_state["sentinel_report_obj"] = _report
            st.session_state["sentinel_diff_text"] = diff_text
        except Exception as _exc:
            st.error(f"Impact analysis failed: {_exc}")

    # ── Results ──────────────────────────────────────────────────
    if "sentinel_report" in st.session_state:
        _rpt = st.session_state["sentinel_report"]
        _summary = _rpt.get("summary", {})
        _at_risk = _rpt.get("at_risk_requirements", [])
        _scripts = _rpt.get("test_scripts_to_execute", [])

        # Metric row
        _mc1, _mc2, _mc3, _mc4 = st.columns(4)
        with _mc1:
            st.metric(
                "Files Changed",
                len(_rpt.get("modified_modules", [])),
            )
        with _mc2:
            st.metric("At-Risk Requirements", len(_at_risk))
        with _mc3:
            st.metric("Test Scripts Required", len(_scripts))
        with _mc4:
            _band_parts = ", ".join(
                f"{b}:{_summary.get(b, 0)}"
                for b in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
                if _summary.get(b, 0) > 0
            ) or "None"
            st.metric("Risk Bands", _band_parts)

        st.markdown("---")

        # At-Risk Requirements table
        if _at_risk:
            _card_open(
                "At-Risk Requirements",
                icon="fa-triangle-exclamation",
            )
            import pandas as _pd_s
            _req_rows = [
                {
                    "Req ID": r.get("req_id", ""),
                    "Title": r.get("title", ""),
                    "Risk Level": r.get("risk_level", ""),
                    "GxP Category": r.get("gxp_category", ""),
                    "Criticality": r.get(
                        "criticality_score", ""
                    ),
                    "Scope": round(
                        r.get("scope_of_change", 0.0), 3
                    ),
                    "Impact Score": round(
                        r.get("impact_score", 0.0), 3
                    ),
                    "Risk Band": r.get("risk_band", ""),
                }
                for r in _at_risk
            ]
            st.dataframe(
                _pd_s.DataFrame(_req_rows),
                use_container_width=True,
                hide_index=True,
            )
            _card_close()

        # Consolidated Test Execution Plan table
        if _scripts:
            _card_open(
                "Consolidated Test Execution Plan",
                icon="fa-clipboard-check",
            )
            _script_rows = [
                {
                    "Script ID": s.get("script_id", ""),
                    "Phase": s.get("phase", ""),
                    "Title": s.get("title", ""),
                    "Priority": s.get(
                        "execution_priority", ""
                    ),
                    "Automation": s.get(
                        "automation_status", ""
                    ),
                }
                for s in _scripts
            ]
            st.dataframe(
                _pd_s.DataFrame(_script_rows),
                use_container_width=True,
                hide_index=True,
            )
            _card_close()

        # IAR Generation
        st.markdown("---")
        _card_open(
            "Generate Impact Assessment Report (IAR)",
            icon="fa-file-waveform",
        )
        _ic1, _ic2 = st.columns(2)
        with _ic1:
            iar_author = st.text_input(
                "Prepared By",
                value="EVOLV Sentinel",
                key="sentinel_author",
            )
        with _ic2:
            iar_project = st.text_input(
                "Project Name",
                value="EVOLV Validation Factory",
                key="sentinel_project",
            )

        import os as _os_s
        _use_llm = bool(
            _os_s.environ.get("ANTHROPIC_API_KEY")
        )
        _mode_label = (
            "LLM (Claude)" if _use_llm
            else "Dry-run (template)"
        )
        st.caption(f"Generation mode: {_mode_label}")

        gen_iar_btn = st.button(
            "Generate IAR",
            key="sentinel_gen_iar",
            type="primary",
        )
        if gen_iar_btn:
            try:
                from Agents.sentinel import JustificationEngine
                _je = JustificationEngine.from_file(
                    SENTINEL_GRAPH
                )
                _iar = _je.generate_iar(
                    impact_report=st.session_state[
                        "sentinel_report_obj"
                    ],
                    diff_text=st.session_state.get(
                        "sentinel_diff_text", diff_text
                    ),
                    author=iar_author,
                    project_name=iar_project,
                    dry_run=not _use_llm,
                )
                _md = JustificationEngine.render_to_markdown(
                    _iar
                )
                st.session_state["sentinel_iar_md"] = _md
                st.session_state["sentinel_iar_id"] = (
                    _iar.iar_id
                )
                st.success("IAR generated successfully.")
            except Exception as _exc:
                st.error(f"IAR generation failed: {_exc}")

        _card_close()

        # IAR display + download
        if "sentinel_iar_md" in st.session_state:
            _card_open(
                "Impact Assessment Report",
                icon="fa-file-alt",
            )
            st.markdown(
                st.session_state["sentinel_iar_md"]
            )
            st.download_button(
                label="Download IAR (.md)",
                data=st.session_state["sentinel_iar_md"],
                file_name=(
                    f"{st.session_state['sentinel_iar_id']}"
                    ".md"
                ),
                mime="text/markdown",
                key="sentinel_iar_dl",
            )
            _card_close()

    else:
        empty_state(
            "No Diff Loaded",
            "Paste a git diff above and click "
            "Run Impact Analysis.",
            icon="satellite-dish",
        )

    # ══════════════════════════════════════════════════════════════
    # Section A — Sentinel Watcher: Requirement Drift Detection
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    _card_open(
        "Sentinel Watcher \u2014 Requirement Drift Detection",
        icon="fa-rotate",
    )

    import os as _os_w
    _BASELINE_PATH = (
        PROJECT_ROOT / "output" / "sentinel" / "baseline.json"
    )

    # Baseline status
    if _BASELINE_PATH.exists():
        try:
            with open(_BASELINE_PATH, "r", encoding="utf-8") as _bf:
                _bl_meta = json.load(_bf)
            _bl_ts = _bl_meta.get("generated_at", "unknown")[:19]
            _bl_n = _bl_meta.get("requirement_count", "?")
            st.caption(
                f"Baseline set \u2014 {_bl_n} requirements "
                f"\u2014 {_bl_ts} UTC"
            )
        except Exception:
            st.caption("Baseline file exists but could not be read.")
    else:
        st.caption("No baseline set")

    _wc1, _wc2 = st.columns(2)
    with _wc1:
        _set_bl_btn = st.button(
            "Set Baseline",
            key="sentinel_set_baseline",
            disabled=not _sentinel_graph_ok,
        )
    with _wc2:
        _sync_btn = st.button(
            "Sync & Detect Drift",
            key="sentinel_sync_drift",
            disabled=(
                not _sentinel_graph_ok
                or not _BASELINE_PATH.exists()
            ),
        )

    if _set_bl_btn and _sentinel_graph_ok:
        try:
            from Agents.sentinel import WatcherEngine as _WE
            _we = _WE.from_file(SENTINEL_GRAPH)
            _bl = _we.create_baseline(_BASELINE_PATH)
            st.session_state["sentinel_baseline"] = _bl
            st.toast(
                f"Baseline saved \u2014 "
                f"{_bl['requirement_count']} requirements hashed."
            )
            st.rerun()
        except Exception as _exc:
            st.error(f"Baseline creation failed: {_exc}")

    if _sync_btn and _sentinel_graph_ok:
        try:
            from Agents.sentinel import WatcherEngine as _WE
            _we = _WE.from_file(SENTINEL_GRAPH)
            _deltas = _we.detect_deltas(_BASELINE_PATH)
            st.session_state["sentinel_deltas"] = _deltas
            st.session_state.pop("sentinel_watcher_report", None)
        except Exception as _exc:
            st.error(f"Drift detection failed: {_exc}")

    # Show deltas / drift results
    if "sentinel_deltas" in st.session_state:
        _deltas = st.session_state["sentinel_deltas"]
        if _deltas:
            st.warning(
                f"\u26a0\ufe0f  {len(_deltas)} requirement(s) "
                "drifted from baseline."
            )
            import pandas as _pd_w
            _delta_rows = [
                {
                    "Req ID": d.req_id,
                    "Title": d.title,
                    "Old Hash": d.old_hash,
                    "New Hash": d.new_hash,
                }
                for d in _deltas
            ]
            st.dataframe(
                _pd_w.DataFrame(_delta_rows),
                use_container_width=True,
                hide_index=True,
            )
            _analyze_btn = st.button(
                "Analyze TC Impact",
                key="sentinel_analyze_tc",
                type="primary",
            )
            if _analyze_btn:
                try:
                    from Agents.sentinel import WatcherEngine as _WE
                    _we = _WE.from_file(SENTINEL_GRAPH)
                    _use_llm_w = bool(
                        _os_w.environ.get("ANTHROPIC_API_KEY")
                    )
                    _wr = _we.analyze_tc_impact(
                        _deltas,
                        dry_run=not _use_llm_w,
                    )
                    st.session_state[
                        "sentinel_watcher_report"
                    ] = _wr
                except Exception as _exc:
                    st.error(f"TC impact analysis failed: {_exc}")
        else:
            st.success(
                "All requirements match baseline. "
                "No drift detected."
            )

    # Show WatcherReport
    if "sentinel_watcher_report" in st.session_state:
        _wr = st.session_state["sentinel_watcher_report"]
        _wm1, _wm2 = st.columns(2)
        with _wm1:
            st.metric(
                "Impacted TCs",
                len(_wr.impacted_tc_ids),
            )
        with _wm2:
            _rd_label = (
                "\ud83d\udd34 Yes" if _wr.risk_drift
                else "\ud83d\udfe2 No"
            )
            st.metric("Risk Drift", _rd_label)

        if _wr.tc_impact_details:
            import pandas as _pd_wi
            _status_colours = {
                "Invalidated": "\ud83d\udd34 Invalidated",
                "Partially Impacted": "\ud83d\udfe0 Partially Impacted",
                "Unaffected": "\ud83d\udfe2 Unaffected",
            }
            _detail_rows = [
                {
                    "TC ID": d.tc_id,
                    "Status": _status_colours.get(
                        d.impact_status, d.impact_status
                    ),
                    "Rationale": d.rationale,
                }
                for d in _wr.tc_impact_details
            ]
            st.dataframe(
                _pd_wi.DataFrame(_detail_rows),
                use_container_width=True,
                hide_index=True,
            )

        st.info(_wr.regression_rationale)

    _card_close()

    # ══════════════════════════════════════════════════════════════
    # Section B — Demo: Simulate Vendor v2.0 Ingest
    # ══════════════════════════════════════════════════════════════
    _card_open(
        "Demo: Simulate Vendor v2.0 Ingest",
        icon="fa-vial-circle-check",
    )
    st.caption(
        "Simulates ingesting a vendor software update that changes "
        "3 requirements."
    )
    _demo_btn = st.button(
        "Ingest v2.0",
        key="sentinel_demo_ingest",
        type="primary",
    )
    if _demo_btn:
        st.session_state["sentinel_demo_triggered"] = True

    if st.session_state.get("sentinel_demo_triggered"):
        from Agents.sentinel import DEMO_V2_REPORT as _DEMO

        with st.expander(
            "\ud83d\udd14 Sentinel Alert",
            expanded=True,
        ):
            st.warning(
                "\u26a0\ufe0f  Alert: 3 Requirements have drifted."
            )
            st.success(
                "\u2705  Regression Suite Optimized: "
                "Rerun TC-05, TC-09."
            )
            st.info(
                "\ud83d\udccb  88% of documentation remains valid."
            )

        import pandas as _pd_d
        # Drifted requirements table
        st.markdown("**Drifted Requirements**")
        _demo_delta_rows = [
            {
                "Req ID": d.req_id,
                "Title": d.title,
                "Old Hash": d.old_hash,
                "New Hash": d.new_hash,
            }
            for d in _DEMO.deltas
        ]
        st.dataframe(
            _pd_d.DataFrame(_demo_delta_rows),
            use_container_width=True,
            hide_index=True,
        )

        # TC Impact Details table
        st.markdown("**TC Impact Details**")
        _demo_status_colours = {
            "Invalidated": "\ud83d\udd34 Invalidated",
            "Partially Impacted": "\ud83d\udfe0 Partially Impacted",
            "Unaffected": "\ud83d\udfe2 Unaffected",
        }
        _demo_detail_rows = [
            {
                "TC ID": d.tc_id,
                "Status": _demo_status_colours.get(
                    d.impact_status, d.impact_status
                ),
                "Rationale": d.rationale,
            }
            for d in _DEMO.tc_impact_details
        ]
        st.dataframe(
            _pd_d.DataFrame(_demo_detail_rows),
            use_container_width=True,
            hide_index=True,
        )

        # Risk Drift badge
        st.markdown(
            "\ud83d\udfe2 **Risk Drift:** None Detected"
        )

    _card_close()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 12 — Requirements Engine (Validation Factory)
# Single-column progressive disclosure with 14 GxP types, inline help
# drawers, Claude LLM transformation, and FDA/EMA 2026 AI auto-tagging.
# ═══════════════════════════════════════════════════════════════════════════
elif page.startswith("12"):
    from Agents.smart_requirements_engine import (
        REQUIREMENT_TYPES as _REQ_TYPES,
        SMARTRequirementsEngine as _SREEngine,
        SMARTEngineError as _SREError,
        SmartPackage as _SmartPackage,
    )
    import re as _sre12_re

    breadcrumb(["Home", "Requirements", "Requirements Engine"])
    page_header(
        "Requirements Engine",
        "14 GxP categories \u00b7 SMART rewrite via EVOLV"
        " Intelligence Engine"
        " \u00b7 FDA/EMA 2026 AI Guidance auto-tagging",
    )

    # ── Custom CSS for help drawer panel ─────────────────────────
    st.markdown(
        """
<style>
.req-help-panel {
    background: linear-gradient(135deg,#0d1b2a,#162032);
    border:1px solid #1e3a5f;
    border-left:3px solid #3b82f6;
    border-radius:8px;
    padding:0.9rem 1.1rem;
    margin:0.3rem 0 0.8rem 0;
    font-size:0.82rem;
    line-height:1.55;
}
.req-help-brand  { color:#3b82f6; font-size:0.65rem; font-weight:700;
                   letter-spacing:.1em; text-transform:uppercase;
                   margin-bottom:0.55rem; }
.req-help-title  { color:#60a5fa; font-weight:700; margin-bottom:0.4rem; }
.req-help-def    { color:#94a3b8; margin-bottom:0.6rem; }
.req-help-ref    { color:#64748b; font-style:italic; font-size:0.76rem; }
.req-help-ex     { color:#fbbf24; font-weight:600; font-size:0.76rem;
                   margin-top:0.6rem; margin-bottom:0.2rem; }
.req-help-pit    { color:#f87171; font-weight:600; font-size:0.76rem;
                   margin-top:0.5rem; margin-bottom:0.2rem; }
.req-help-li     { color:#94a3b8; margin-left:1rem; font-size:0.78rem; }
.ai-tag-badge {
    display:inline-block;
    background:#7c3aed;color:#ede9fe;
    font-size:0.7rem;font-weight:700;letter-spacing:.04em;
    padding:2px 9px;border-radius:20px;margin-left:0.4rem;
    vertical-align:middle;
}
.risk-badge-high   { background:#ef4444; }
.risk-badge-medium { background:#f0a500; }
.risk-badge-low    { background:#22c55e; }
.risk-badge {
    display:inline-block;color:#fff;font-size:0.72rem;
    font-weight:700;padding:2px 10px;border-radius:20px;
    margin-right:0.3rem;
}
.fda-badge {
    display:inline-block;
    background:#1e40af;color:#bfdbfe;font-size:0.70rem;
    padding:2px 9px;border-radius:20px;margin-right:0.3rem;
}

/* ── Compliance Shield ─────────────────────────────────── */
.shield-badge {
    display:inline-flex;align-items:center;gap:0.25rem;
    font-size:0.72rem;font-weight:700;padding:2px 10px;
    border-radius:20px;margin-right:0.3rem;cursor:help;
    vertical-align:middle;
}
.shield-green { background:#14532d;color:#bbf7d0;
                border:1px solid #22c55e; }
.shield-amber { background:#78350f;color:#fef3c7;
                border:1px solid #f59e0b; }
.shield-red   { background:#7f1d1d;color:#fecaca;
                border:1px solid #ef4444; }

/* ── Auto-Links Panel ──────────────────────────────────── */
.auto-link-panel {
    background:linear-gradient(135deg,#0f172a,#1e293b);
    border:1px solid #334155;border-left:3px solid #6366f1;
    border-radius:8px;padding:0.7rem 1rem;font-size:0.8rem;
    line-height:1.6;
}
.auto-link-section {
    color:#a5b4fc;font-weight:700;font-size:0.72rem;
    letter-spacing:.07em;text-transform:uppercase;
    margin-bottom:0.3rem;margin-top:0.5rem;
}
.auto-link-section:first-child { margin-top:0; }
.auto-link-item { color:#94a3b8;margin-left:0.8rem;
                  margin-bottom:0.15rem; }

/* ── Template hint text ────────────────────────────────── */
.tmpl-hint { color:#64748b;font-size:0.7rem;margin:0.3rem 0 0;
             font-style:italic;text-align:center; }
</style>
""",
        unsafe_allow_html=True,
    )

    # ── FDA/EMA 2026 notice bar ───────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient('
        '90deg,#1a1a2e,#16213e);border-left:4px solid #f0a500;'
        'border-radius:6px;padding:0.6rem 1rem;margin-bottom:0.6rem;">'
        '<span style="color:#f0a500;font-weight:700;font-size:0.85rem;">'
        'FDA/EMA 2026 AI Guidance</span>'
        '<span style="color:#c0c8d8;font-size:0.78rem;'
        'margin-left:0.8rem;">'
        'Requirements involving AI inference, automated decisions, '
        'patient safety, bias monitoring, or PCCP are auto-tagged '
        'and receive a mandatory Negative Test Scenario.'
        '</span></div>',
        unsafe_allow_html=True,
    )

    # ── Section 1: System Context ─────────────────────────────────
    st.markdown(
        '<p style="font-size:0.72rem;color:#64748b;'
        'letter-spacing:.08em;text-transform:uppercase;'
        'margin-bottom:0.3rem;margin-top:0.6rem;">'
        'SYSTEM CONTEXT</p>',
        unsafe_allow_html=True,
    )
    _sre12_name = st.text_input(
        "System Name",
        placeholder="e.g. Clinical LIMS v3.2",
        key="sre12_system_name",
    )
    _sre12_risk = st.selectbox(
        "Overall Risk Level",
        ["High", "Medium", "Low"],
        index=0,
        key="sre12_risk_level",
        help=(
            "High = patient safety / regulatory impact. "
            "Medium = quality / audit functions. "
            "Low = administrative / non-GxP."
        ),
    )
    _sre12_has_ai = st.checkbox(
        "\u26a1 System uses AI/ML or automated decision-making "
        "(applies FDA/EMA 2026 AI Guidance to all sections)",
        key="sre12_has_ai",
        value=False,
    )
    _sre12_process_map = st.text_area(
        "Process Map",
        placeholder=(
            "Describe the business process flow this system supports.\n"
            "e.g. Sample received \u2192 Lab analysis \u2192 "
            "QC review \u2192 Release decision"
        ),
        height=90,
        key="sre12_process_map",
    )
    _sre12_data_flow = st.text_area(
        "Data Flow",
        placeholder=(
            "Describe how data moves through the system.\n"
            "e.g. Instrument CSV \u2192 LIMS import \u2192 "
            "QC check \u2192 ERP release record"
        ),
        height=90,
        key="sre12_data_flow",
    )

    st.markdown(
        '<hr style="border-color:#1e3a5f;margin:1rem 0 0.6rem 0;">',
        unsafe_allow_html=True,
    )

    # ── Section 2: 14 Requirement Type Sections ───────────────────
    st.markdown(
        '<p style="font-size:0.72rem;color:#64748b;'
        'letter-spacing:.08em;text-transform:uppercase;'
        'margin-bottom:0.6rem;">'
        'REQUIREMENTS \u2014 enter your notes; '
        'leave blank to skip a category</p>',
        unsafe_allow_html=True,
    )

    def _sre12_help_html(type_key: str) -> str:
        """Render help-drawer HTML for one requirement type."""
        td = _REQ_TYPES.get(type_key, {})
        defn = td.get("definition", "")
        gref = td.get("gamp5_ref", "")
        examples = td.get("examples", [])
        pitfalls = td.get("pitfalls", [])
        ex_html = "".join(
            f'<div class="req-help-li">\u2022 {ex}</div>'
            for ex in examples
        )
        pit_html = "".join(
            f'<div class="req-help-li">\u2022 {pit}</div>'
            for pit in pitfalls
        )
        return (
            '<div class="req-help-panel">'
            '<div class="req-help-brand">'
            "EVOLV \u00b7 Compliance Intelligence"
            "</div>"
            f'<div class="req-help-title">{type_key}</div>'
            f'<div class="req-help-def">{defn}</div>'
            f'<div class="req-help-ref">{gref}</div>'
            f'<div class="req-help-ex">Example Requirements</div>'
            f'{ex_html}'
            f'<div class="req-help-pit">Common Pitfalls</div>'
            f'{pit_html}'
            "</div>"
        )

    def _smart_compliance_check(req_d: dict) -> dict:
        """Evaluate SMART + 2026 AI compliance for one requirement.

        :requirement: URS-21.13
        """
        txt = req_d.get("smart_text", "")
        flags = req_d.get("fda_ema_flags", [])
        neg = req_d.get("negative_test_scenario") or ""
        ac = req_d.get("acceptance_criteria", {})
        checks = {
            "Specific": txt.lower().startswith(
                "the system shall"
            ),
            "Measurable": bool(
                _sre12_re.search(
                    r"\d+\s*(?:ms|s|%|days?|hours?"
                    r"|records?|users?)"
                    r"|\bwithin\b|\bSLA\b|\buptime\b"
                    r"|\bthreshold\b|\b<=\b|\b>=\b",
                    txt,
                    _sre12_re.IGNORECASE,
                )
            ),
            "Achievable": len(ac.get("positive", [])) > 0,
            "Relevant": bool(
                req_d.get("category", "")
                or req_d.get("risk_level", "")
            ),
            "Traceable": (
                len(ac.get("negative", [])) > 0
                or len(ac.get("edge", [])) > 0
            ),
            "2026 AI Std": (bool(neg) if flags else True),
        }
        score = sum(1 for v in checks.values() if v)
        mx = len(checks)
        level = (
            "green" if score == mx
            else "amber" if score >= mx - 1
            else "red"
        )
        return {
            "score": score,
            "max": mx,
            "level": level,
            "checks": checks,
        }

    def _shield_html(c: dict) -> str:
        """Return shield badge HTML for a compliance result.

        :requirement: URS-21.13
        """
        lvl = c.get("level", "red")
        score = c.get("score", 0)
        mx = c.get("max", 6)
        checks = c.get("checks", {})
        tip = " | ".join(
            f"{'OK' if v else 'FAIL'}: {k}"
            for k, v in checks.items()
        )
        label = {
            "green": "\U0001f6e1 SMART + AI Compliant",
            "amber": "\U0001f6e1 Partial",
            "red": "\U0001f6e1 Needs Review",
        }.get(lvl, "\U0001f6e1")
        return (
            f'<span class="shield-badge shield-{lvl}"'
            f' title="{tip}">'
            f"{label} {score}/{mx}</span>"
        )

    def _auto_links(req_d: dict, type_name: str) -> dict:
        """Deterministic risk + TC suggestions for a requirement.

        :requirement: URS-21.13
        """
        risk = req_d.get("risk_level", "Low")
        flags = req_d.get("fda_ema_flags", [])
        ai_tag = req_d.get("ai_guidance_tagged", False)
        risks, tcs = [], []

        if risk == "High":
            risks += [
                "RISK-GXP-01: GxP Compliance Breach"
                " \u2014 Rigorous validation required"
                " (GAMP 5 §5)",
                "RISK-AUD-01: Audit Trail Integrity"
                " \u2014 21 CFR Part 11 obligation",
            ]
        if "Patient Safety" in flags:
            risks.append(
                "RISK-SAF-01: Patient Safety Impact"
                " \u2014 Severity = HIGH override"
            )
        if "AI Inference" in flags:
            risks.append(
                "RISK-AI-01: Model Drift / Bias"
                " \u2014 Continuous monitoring required"
            )
        if "Automated Decision" in flags:
            risks.append(
                "RISK-AI-02: Autonomous Decision Error"
                " \u2014 Human-in-the-loop control"
            )
        if "PCCP" in flags:
            risks.append(
                "RISK-AI-03: PCCP Change Control"
                " \u2014 Predetermined Change Control Plan"
            )
        if risk == "Medium" and not risks:
            risks.append(
                "RISK-QUA-01: Quality System Deviation"
                " \u2014 CAPA pathway"
            )
        if not risks:
            risks.append(
                "RISK-OPS-01: Operational Continuity"
                " \u2014 Standard monitoring"
            )

        if risk == "High":
            tcs += [
                "TC-OQ-001: Formal OQ"
                " \u2014 Positive execution path",
                "TC-OQ-002: Formal OQ"
                " \u2014 Negative / boundary test",
                "TC-UAT-001: UAT"
                " \u2014 Business-process walkthrough",
            ]
        elif risk == "Medium":
            tcs += [
                "TC-INF-001: Informal Charter"
                " \u2014 Exploratory testing",
                "TC-HYB-001: Hybrid OQ/UAT"
                " \u2014 Key flow verification",
            ]
        else:
            tcs.append(
                "TC-SUP-001: Supplier-Provided Evidence"
                " \u2014 CoV review"
            )
        if ai_tag or flags:
            tcs += [
                "TC-AI-001: AI Boundary Test"
                " \u2014 Out-of-distribution inputs",
                "TC-AI-002: Adversarial Scenario"
                " \u2014 Bias / edge-case probing",
            ]
        return {"risks": risks, "test_cases": tcs}

    def _auto_links_html(links: dict) -> str:
        """Return styled HTML panel for auto-link display.

        :requirement: URS-21.13
        """
        risks_html = "".join(
            f'<div class="auto-link-item">\u2022 {r}</div>'
            for r in links.get("risks", [])
        )
        tcs_html = "".join(
            f'<div class="auto-link-item">\u2022 {t}</div>'
            for t in links.get("test_cases", [])
        )
        return (
            '<div class="auto-link-panel">'
            '<div class="auto-link-section">'
            "Linked Risks</div>"
            f"{risks_html}"
            '<div class="auto-link-section">'
            "Suggested Test Cases</div>"
            f"{tcs_html}"
            "</div>"
        )

    for _t_key, _t_meta in _REQ_TYPES.items():
        _t_num = _t_meta["number"]
        _t_icon = _t_meta["icon"]
        _t_tag = _t_meta["tagline"]
        _sre12_help_key = f"sre12_help_{_t_key.lower().replace(' ', '_')}"
        _sre12_notes_key = (
            f"sre12_notes_{_t_key.lower().replace(' ', '_')}"
        )

        # Check if this section already has notes (for progress hint)
        _existing_notes = st.session_state.get(
            _sre12_notes_key, ""
        ).strip()
        _has_notes_indicator = (
            " \u2705" if _existing_notes else ""
        )

        with st.expander(
            f"{_t_icon} {_t_num}. {_t_key}"
            f" \u2014 {_t_tag}{_has_notes_indicator}",
            expanded=False,
        ):
            # Help toggle button (inline, single-column)
            _help_open = st.session_state.get(
                _sre12_help_key, False
            )
            _help_label = (
                "\u25bc Hide Help" if _help_open
                else "\u003f Show Help"
            )
            if st.button(
                _help_label,
                key=f"btn_help_{_t_key}",
                type="secondary",
            ):
                st.session_state[_sre12_help_key] = not _help_open
                st.rerun()

            # Help drawer (inline panel)
            if st.session_state.get(_sre12_help_key, False):
                st.markdown(
                    _sre12_help_html(_t_key),
                    unsafe_allow_html=True,
                )
                # Template button — pre-fill textarea
                _tmpl_examples = _REQ_TYPES.get(
                    _t_key, {}
                ).get("examples", [])
                if _tmpl_examples:
                    if st.button(
                        "\U0001f4cb Use as Template",
                        key=f"btn_tmpl_{_t_key}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        st.session_state[
                            _sre12_notes_key
                        ] = "\n".join(_tmpl_examples)
                        st.rerun()
                    st.markdown(
                        '<p class="tmpl-hint">Pre-fills the'
                        " notes field with SMART-standard"
                        " examples from the EVOLV"
                        " Intelligence Engine.</p>",
                        unsafe_allow_html=True,
                    )

            # User notes textarea
            st.text_area(
                "Your Notes",
                placeholder=(
                    "Input your raw requirements below \u2014 the"
                    " EVOLV Intelligence Engine will refactor them"
                    " into SMART, audit-ready standards.\n"
                    "e.g. System should back up data regularly\n"
                    "     Users need to log in securely"
                ),
                height=130,
                key=_sre12_notes_key,
                label_visibility="collapsed",
            )

    # ── Progress indicator ────────────────────────────────────────
    _sre12_filled = sum(
        1
        for _tk in _REQ_TYPES
        if st.session_state.get(
            f"sre12_notes_{_tk.lower().replace(' ', '_')}", ""
        ).strip()
    )
    st.markdown(
        f'<p style="font-size:0.75rem;color:#64748b;'
        f'margin:0.4rem 0 0.8rem 0;">'
        f'{_sre12_filled} of {len(_REQ_TYPES)} '
        f'categories populated</p>',
        unsafe_allow_html=True,
    )

    # ── Transform button ──────────────────────────────────────────
    st.markdown(
        '<hr style="border-color:#1e3a5f;margin:0.6rem 0;">',
        unsafe_allow_html=True,
    )
    _sre12_transform = st.button(
        "\u2728 Transform to SMART Requirements",
        type="primary",
        key="sre12_transform_btn",
        use_container_width=True,
    )

    if _sre12_transform:
        _sre12_notes_collected: dict = {}
        for _tk in _REQ_TYPES:
            _n_key = (
                f"sre12_notes_{_tk.lower().replace(' ', '_')}"
            )
            _raw = st.session_state.get(_n_key, "").strip()
            if _raw:
                _sre12_notes_collected[_tk] = _raw

        if not _sre12_notes_collected:
            st.warning(
                "Open at least one section and enter your "
                "requirements before transforming."
            )
        else:
            _sre12_ctx = {
                "system_name": st.session_state.get(
                    "sre12_system_name", ""
                ),
                "process_map": st.session_state.get(
                    "sre12_process_map", ""
                ),
                "data_flow": st.session_state.get(
                    "sre12_data_flow", ""
                ),
                "overall_risk": st.session_state.get(
                    "sre12_risk_level", "Medium"
                ),
            }
            with st.spinner(
                "Transforming to SMART format "
                "(Claude \u2192 GxP-compliant output)..."
            ):
                try:
                    _sre12_eng = _SREEngine()
                    _sre12_pkg = _sre12_eng.transform_to_smart(
                        context=_sre12_ctx,
                        notes_by_type=_sre12_notes_collected,
                        risk_level=_sre12_ctx["overall_risk"],
                        has_ai=st.session_state.get(
                            "sre12_has_ai", False
                        ),
                    )
                    st.session_state["sre12_package"] = (
                        _sre12_pkg.to_dict()
                    )
                except _SREError as _sre12_e:
                    st.error(
                        f"Requirements Engine error "
                        f"(CSV-021): {_sre12_e}"
                    )
                except Exception as _sre12_ex:
                    st.error(
                        f"Unexpected error: {_sre12_ex}"
                    )

    # ── Results ───────────────────────────────────────────────────
    _sre12_pkg_data = st.session_state.get("sre12_package")
    if _sre12_pkg_data:
        _pkg_stats = _sre12_pkg_data.get("stats", {})
        _pkg_sections = _sre12_pkg_data.get("sections", [])
        _pkg_ctx = _sre12_pkg_data.get("context", {})

        st.markdown(
            '<hr style="border-color:#1e3a5f;margin:0.8rem 0;">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-size:0.72rem;color:#64748b;'
            'letter-spacing:.08em;text-transform:uppercase;'
            'margin-bottom:0.6rem;">'
            'RESULTS</p>',
            unsafe_allow_html=True,
        )

        # KPI row
        _r1, _r2, _r3, _r4 = st.columns(4)
        _r1.metric("Requirements", _pkg_stats.get("total", 0))
        _r2.metric("High Risk", _pkg_stats.get("high_risk", 0))
        _r3.metric(
            "AI/2026 Flagged",
            _pkg_stats.get("fda_ema_flagged", 0),
        )
        _r4.metric(
            "Sections",
            _pkg_stats.get("sections_populated", 0),
        )

        st.markdown(
            '<hr style="border-color:#1e3a5f;margin:0.6rem 0;">',
            unsafe_allow_html=True,
        )

        # Per-section results
        for _sec_data in _pkg_sections:
            _sname = _sec_data.get("type_name", "")
            _sreqs = _sec_data.get("requirements", [])
            _sai = _sec_data.get("ai_guidance_tagged", False)

            if not _sreqs:
                continue

            _smeta = _REQ_TYPES.get(_sname, {})
            _sicon = _smeta.get("icon", "")
            _stag = _smeta.get("tagline", "")
            _snum = _smeta.get("number", "")

            _section_label = (
                f"{_sicon} {_snum}. {_sname} \u2014 "
                f"{len(_sreqs)} requirement"
                f"{'s' if len(_sreqs) != 1 else ''}"
            )
            if _sai:
                _section_label += " \u26a1 AI Guidance"

            with st.expander(_section_label, expanded=False):
                for _req_d in _sreqs:
                    _smart = _req_d.get("smart_text", "")
                    _risk = _req_d.get("risk_level", "Low")
                    _ai_tag = _req_d.get(
                        "ai_guidance_tagged", False
                    )
                    _flags = _req_d.get("fda_ema_flags", [])
                    _ac = _req_d.get("acceptance_criteria", {})
                    _neg_test = _req_d.get(
                        "negative_test_scenario"
                    )

                    # Compliance shield + auto-links
                    _compliance = _smart_compliance_check(
                        _req_d
                    )
                    _links = _auto_links(
                        _req_d,
                        _sec_data.get("type_name", ""),
                    )

                    # SMART requirement text
                    st.success(_smart)

                    # Badges row
                    _risk_cls = {
                        "High": "risk-badge-high",
                        "Medium": "risk-badge-medium",
                        "Low": "risk-badge-low",
                    }.get(_risk, "risk-badge-low")
                    _badges = (
                        '<div style="margin:0.25rem 0 '
                        '0.5rem 0;display:flex;gap:0.4rem;'
                        'flex-wrap:wrap;align-items:center;">'
                        + _shield_html(_compliance)
                        + f'<span class="risk-badge '
                        f'{_risk_cls}">{_risk} Risk</span>'
                    )
                    for _fl in _flags:
                        _badges += (
                            f'<span class="fda-badge">'
                            f'2026 AI: {_fl}</span>'
                        )
                    if _ai_tag and not _flags:
                        _badges += (
                            '<span class="ai-tag-badge">'
                            "2026 AI Guidance</span>"
                        )
                    _badges += "</div>"
                    st.markdown(_badges, unsafe_allow_html=True)

                    # Acceptance criteria — 3 tabs
                    _ac_pos = _ac.get("positive", [])
                    _ac_neg = _ac.get("negative", [])
                    _ac_edg = _ac.get("edge", [])
                    if _ac_pos or _ac_neg or _ac_edg:
                        _tab_p, _tab_n, _tab_e, _tab_l = (
                            st.tabs(
                                [
                                    "\u2705 Positive",
                                    "\u274c Negative",
                                    "\u26a0 Edge Case",
                                    "\U0001f517 Auto-Links",
                                ]
                            )
                        )
                        with _tab_p:
                            for _p in _ac_pos:
                                st.success(_p)
                        with _tab_n:
                            for _n in _ac_neg:
                                st.error(_n)
                        with _tab_e:
                            for _e in _ac_edg:
                                st.warning(_e)
                        with _tab_l:
                            st.markdown(
                                _auto_links_html(_links),
                                unsafe_allow_html=True,
                            )

                    # Mandatory Negative Test Scenario
                    if _neg_test:
                        st.markdown(
                            '<div style="background:#1a0a0a;'
                            'border-left:3px solid #ef4444;'
                            'border-radius:6px;'
                            'padding:0.6rem 0.9rem;'
                            'margin:0.4rem 0;">'
                            '<span style="color:#ef4444;'
                            'font-weight:700;font-size:0.78rem;">'
                            'FDA/EMA 2026 — Mandatory '
                            'Negative Test Scenario</span>'
                            f'<div style="color:#fca5a5;'
                            f'font-size:0.8rem;margin-top:'
                            f'0.35rem;">{_neg_test}</div>'
                            "</div>",
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        '<hr style="border-color:#1e2d40;'
                        'margin:0.5rem 0;">',
                        unsafe_allow_html=True,
                    )

        # ── Export actions ────────────────────────────────────────
        st.markdown(
            '<hr style="border-color:#1e3a5f;margin:0.8rem 0;">',
            unsafe_allow_html=True,
        )
        _exp_a, _exp_b = st.columns(2)
        with _exp_a:
            if st.button(
                "\u27a1 Send to Validation Factory",
                key="sre12_export_vf",
                type="primary",
                use_container_width=True,
            ):
                # Flatten all SMART texts for Validation Factory
                _all_smart = []
                for _s in _pkg_sections:
                    for _r in _s.get("requirements", []):
                        _t = _r.get("smart_text", "")
                        if _t:
                            _all_smart.append(_t)
                st.session_state["p2_requirement"] = (
                    "\n".join(_all_smart)
                )
                st.session_state["page"] = "6"
                st.rerun()
        with _exp_b:
            if st.button(
                "\u2192 Send to Generate Reqs",
                key="sre12_export_p2",
                type="secondary",
                use_container_width=True,
            ):
                _all_smart2 = []
                for _s in _pkg_sections:
                    for _r in _s.get("requirements", []):
                        _t = _r.get("smart_text", "")
                        if _t:
                            _all_smart2.append(_t)
                st.session_state["p2_requirement"] = (
                    "\n".join(_all_smart2)
                )
                st.session_state["page"] = "2"
                st.rerun()

        # Raw JSON
        with st.expander("Raw JSON", expanded=False):
            import json as _sre12_json
            st.code(
                _sre12_json.dumps(_sre12_pkg_data, indent=2),
                language="json",
            )

# ===================================================================
# Page 13 — Enterprise Configuration
#   • Nomenclature Mapper  (Task 1 / ServiceNow strategy)
#   • Compliance Mode      (Task 3 / GMP vs GCP)
#   • SOP Plugin           (Task 4 / Co-Innovation)
# ===================================================================
elif page.startswith("13"):
    page_header(
        "Enterprise Configuration",
        "Adapt EVOLV to your team's language, regulations, "
        "and internal quality guidelines.",
    )

    _cfg_tab1, _cfg_tab2, _cfg_tab3 = st.tabs([
        "Nomenclature Mapper",
        "Compliance Mode",
        "SOP Plugin",
    ])

    # ── Tab 1: Nomenclature Mapper ─────────────────────────────
    with _cfg_tab1:
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.85rem;'
            'margin-bottom:1rem;">'
            "Map EVOLV's internal labels to your team's "
            "exact vocabulary.  Changes take effect in the "
            "UI and all AI-generated exports immediately."
            "</p>",
            unsafe_allow_html=True,
        )

        # Preset selector
        _nm_presets_dir = (
            PROJECT_ROOT / "configs" / "nomenclature_maps"
        )
        _nm_preset_files = sorted(
            _nm_presets_dir.glob("*.json")
        ) if _nm_presets_dir.exists() else []
        _nm_preset_names = (
            ["— Select preset —"]
            + [p.stem for p in _nm_preset_files]
        )

        _nm_col_a, _nm_col_b = st.columns([2, 1])
        with _nm_col_a:
            _nm_chosen = st.selectbox(
                "Load Preset",
                _nm_preset_names,
                key="nm_preset_select",
            )
        with _nm_col_b:
            st.write("")
            st.write("")
            if st.button(
                "Apply Preset",
                key="nm_apply_preset",
                disabled=_nm_chosen == "— Select preset —",
            ):
                try:
                    from Agents.metadata_mapper import (
                        MetadataMapper,
                    )
                    _nm_mapper = MetadataMapper.load_preset(
                        _nm_chosen
                    )
                    st.session_state["nm_labels"] = (
                        _nm_mapper.get_all_labels()
                    )
                    if _nm_mapper.config:
                        st.session_state["nm_tenant_name"] = (
                            _nm_mapper.config.tenant_name
                        )
                    st.success(
                        f"Preset '{_nm_chosen}' loaded."
                    )
                except Exception as _nm_err:
                    st.error(str(_nm_err))

        # JSON upload
        _nm_upload = st.file_uploader(
            "Or upload a nomenclature JSON file",
            type=["json"],
            key="nm_json_upload",
        )
        if _nm_upload:
            try:
                import json as _nm_json
                from Agents.metadata_mapper import (
                    MetadataMapper,
                    TenantConfig,
                )
                _nm_data = _nm_json.load(_nm_upload)
                _nm_mapper_u = MetadataMapper(
                    config=TenantConfig.from_dict(_nm_data)
                )
                st.session_state["nm_labels"] = (
                    _nm_mapper_u.get_all_labels()
                )
                st.success("Nomenclature map loaded.")
            except Exception as _nm_uerr:
                st.error(str(_nm_uerr))

        st.markdown("---")

        # Editable label table
        st.markdown(
            "**Edit Labels** — change any display name below:"
        )
        _nm_default_labels: Dict[str, Any] = {
            "requirement":         "Requirement",
            "test_case":           "Test Case",
            "audit":               "Audit",
            "review":              "Review",
            "urs":                 "URS",
            "ur":                  "User Requirement",
            "fr":                  "Functional Requirement",
            "validation_report":   "Validation Report",
            "test_script":         "Test Script",
            "gap_analysis":        "Gap Analysis",
            "traceability_matrix": "Traceability Matrix",
            "change_request":      "Change Request",
            "impact_assessment":   "Impact Assessment",
            "deviation":           "Deviation",
            "capa":                "CAPA",
        }
        _nm_current = st.session_state.get(
            "nm_labels", _nm_default_labels
        )
        _nm_rows = [
            {
                "Internal Key": k,
                "Display Label": _nm_current.get(k, v),
            }
            for k, v in _nm_default_labels.items()
        ]
        _nm_df = pd.DataFrame(_nm_rows)
        _nm_edited = st.data_editor(
            _nm_df,
            key="nm_label_editor",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Internal Key": st.column_config.TextColumn(
                    disabled=True
                ),
                "Display Label": st.column_config.TextColumn(
                    "Client Label"
                ),
            },
        )

        _nm_save_col, _nm_reset_col = st.columns(2)
        with _nm_save_col:
            if st.button(
                "Save Labels",
                key="nm_save_btn",
                type="primary",
                use_container_width=True,
            ):
                _nm_new = {
                    row["Internal Key"]: row["Display Label"]
                    for _, row in _nm_edited.iterrows()
                }
                st.session_state["nm_labels"] = _nm_new
                try:
                    from Agents.metadata_mapper import (
                        ConfigService,
                        TenantConfig,
                    )
                    ConfigService.get_instance().load_from_dict(
                        {
                            "tenant_id": "session",
                            "tenant_name": st.session_state.get(
                                "nm_tenant_name", "Session"
                            ),
                            "industry": "pharma",
                            "compliance_mode": (
                                st.session_state.get(
                                    "compliance_mode", "GMP"
                                )
                            ),
                            "labels": _nm_new,
                        }
                    )
                    st.success(
                        "Labels saved — active for this session."
                    )
                except Exception as _nm_serr:
                    st.error(str(_nm_serr))

        with _nm_reset_col:
            if st.button(
                "Reset to EVOLV Defaults",
                key="nm_reset_btn",
                use_container_width=True,
            ):
                st.session_state.pop("nm_labels", None)
                try:
                    from Agents.metadata_mapper import ConfigService
                    ConfigService.get_instance().reset()
                except Exception:
                    pass
                st.rerun()

        # Live preview
        st.markdown("---")
        st.markdown("**Live Preview**")
        _nm_preview_key = st.selectbox(
            "Preview key",
            list(_nm_default_labels.keys()),
            key="nm_preview_key",
        )
        _nm_preview_labels = st.session_state.get(
            "nm_labels", _nm_default_labels
        )
        _nm_display = _nm_preview_labels.get(
            _nm_preview_key, _nm_preview_key
        )
        st.info(
            f"**{_nm_preview_key}** → **{_nm_display}**"
        )

    # ── Tab 2: Compliance Mode ─────────────────────────────────
    with _cfg_tab2:
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.85rem;'
            'margin-bottom:1rem;">'
            "Select the active regulatory framework for this "
            "site.  The AI will prioritise the corresponding "
            "regulations in all generated documents and "
            "Pinecone queries."
            "</p>",
            unsafe_allow_html=True,
        )

        try:
            from Agents.compliance_context import (
                ComplianceMode,
                ComplianceContext,
            )

            _cm_options = {
                "GMP":      (
                    "GMP — Good Manufacturing Practice",
                    "21 CFR Part 211, GAMP 5, EU GMP Annex 11",
                    "Equipment calibration, batch records, "
                    "process validation.",
                ),
                "GCP":      (
                    "GCP — Good Clinical Practice",
                    "ICH E6 (R2), 21 CFR Part 11, GDPR/HIPAA",
                    "Patient privacy, informed consent, "
                    "investigator oversight.",
                ),
                "GLP":      (
                    "GLP — Good Laboratory Practice",
                    "21 CFR Part 58, OECD GLP Principles",
                    "Study data integrity, QA unit oversight, "
                    "ALCOA+ archival.",
                ),
                "ISO13485": (
                    "ISO 13485 — Medical Device QMS",
                    "ISO 13485:2016, 21 CFR Part 820, "
                    "EU MDR 2017/745",
                    "Design controls, risk management (ISO 14971)"
                    ", complaint handling.",
                ),
            }

            _current_cm = st.session_state.get(
                "compliance_mode", "GMP"
            )

            for _cm_key, (_cm_title, _cm_regs, _cm_focus) in (
                _cm_options.items()
            ):
                _cm_active = _cm_key == _current_cm
                _cm_border = (
                    "#3b82f6" if _cm_active else "#1e3a5f"
                )
                _cm_bg = (
                    "#0f2137" if _cm_active else "#0d1b2a"
                )
                st.markdown(
                    f'<div style="border:1px solid {_cm_border};'
                    f"border-radius:8px;padding:0.9rem 1rem;"
                    f"background:{_cm_bg};"
                    f'margin-bottom:0.6rem;">'
                    f'<div style="display:flex;align-items:'
                    f'center;justify-content:space-between;">'
                    f'<span style="color:#e2e8f0;font-weight:'
                    f'600;font-size:0.95rem;">{_cm_title}'
                    f'{"  ✓" if _cm_active else ""}</span>'
                    f'</div><div style="color:#94a3b8;'
                    f'font-size:0.78rem;margin-top:0.3rem;">'
                    f"<strong>Regulations:</strong> {_cm_regs}"
                    f"<br/><strong>Focus:</strong> {_cm_focus}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                if not _cm_active:
                    if st.button(
                        f"Activate {_cm_key}",
                        key=f"cm_activate_{_cm_key}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            "compliance_mode"
                        ] = _cm_key
                        st.success(
                            f"Compliance mode set to {_cm_key}."
                        )
                        st.rerun()

            # Show active prompt injection preview
            st.markdown("---")
            st.markdown("**Active System Prompt Injection**")
            _cm_ctx = ComplianceContext(
                mode=ComplianceMode(_current_cm),
                site_name=st.session_state.get(
                    "nm_tenant_name", "Your Site"
                ),
                sop_guidelines=st.session_state.get(
                    "sop_guidelines", ""
                ),
            )
            with st.expander(
                "View prompt prefix (sent to AI)", expanded=False
            ):
                st.code(
                    _cm_ctx.get_system_prompt_injection(),
                    language="text",
                )

        except Exception as _cm_err:
            st.error(f"Compliance context error: {_cm_err}")

    # ── Tab 3: SOP Plugin (Co-Innovation) ─────────────────────
    with _cfg_tab3:
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.85rem;'
            'margin-bottom:1rem;">'
            "Upload your internal Quality Guidelines or SOP "
            "text.  EVOLV will use these as additional "
            "constraints when checking for gaps, rewriting "
            "requirements, and generating test scripts."
            "</p>",
            unsafe_allow_html=True,
        )

        _sop_file = st.file_uploader(
            "Upload Quality Guidelines / SOP (.txt or .md)",
            type=["txt", "md"],
            key="sop_file_upload",
        )
        if _sop_file:
            _sop_text = _sop_file.read().decode(
                "utf-8", errors="replace"
            )
            st.session_state["sop_guidelines"] = _sop_text
            st.success(
                f"SOP loaded: {len(_sop_text):,} characters "
                f"from '{_sop_file.name}'."
            )

        st.markdown(
            "Or paste your guidelines directly:"
        )
        _sop_area = st.text_area(
            "Quality Guidelines",
            value=st.session_state.get("sop_guidelines", ""),
            height=200,
            key="sop_text_area",
            placeholder=(
                "e.g. All requirements must cite a risk level. "
                "Test cases must follow the IQ/OQ/PQ format..."
            ),
            label_visibility="collapsed",
        )

        _sop_a, _sop_b = st.columns(2)
        with _sop_a:
            if st.button(
                "Save Guidelines",
                key="sop_save_btn",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["sop_guidelines"] = _sop_area
                st.success(
                    "Guidelines saved — active for this session."
                )
        with _sop_b:
            if st.button(
                "Clear Guidelines",
                key="sop_clear_btn",
                use_container_width=True,
            ):
                st.session_state["sop_guidelines"] = ""
                st.rerun()

        if st.session_state.get("sop_guidelines", ""):
            st.markdown("---")
            st.markdown(
                "**Active Guidelines Preview** "
                f"({len(st.session_state['sop_guidelines']):,}"
                " chars)"
            )
            st.text_area(
                "Preview",
                value=(
                    st.session_state["sop_guidelines"][:800]
                    + ("…" if len(
                        st.session_state["sop_guidelines"]
                    ) > 800 else "")
                ),
                height=150,
                disabled=True,
                key="sop_preview",
                label_visibility="collapsed",
            )

# ===================================================================
# Page 14 — Blast Radius Dashboard
# ===================================================================
elif page.startswith("14"):
    page_header(
        "Blast Radius",
        "Visualise the regression impact of a requirement "
        "change — optimise your test suite instantly.",
    )

    # ── Input panel ───────────────────────────────────────────
    _br_col_left, _br_col_right = st.columns([1, 1])

    with _br_col_left:
        st.markdown("#### Requirement Change")
        _br_req_id = st.text_input(
            "Requirement ID",
            value=st.session_state.get(
                "br_req_id", "URS-7.1"
            ),
            key="br_req_id_input",
            placeholder="e.g. URS-7.1",
        )
        _br_old = st.text_area(
            "Original Requirement",
            value=st.session_state.get(
                "br_old_req",
                "The system shall track warehouse temperature.",
            ),
            height=120,
            key="br_old_input",
        )
        _br_new = st.text_area(
            "Updated Requirement",
            value=st.session_state.get(
                "br_new_req",
                "The system shall monitor and alert on "
                "warehouse temperature using 21 CFR Part 211 "
                "thresholds and log all excursions.",
            ),
            height=120,
            key="br_new_input",
        )
        _br_source = st.selectbox(
            "Source System",
            ["manual", "servicenow", "sap", "jira", "other"],
            key="br_source",
        )

        if st.button(
            "Run Blast Radius Analysis",
            key="br_run_btn",
            type="primary",
            use_container_width=True,
        ):
            if not _br_req_id.strip():
                st.error("Please enter a Requirement ID.")
            elif (
                not _br_old.strip() or not _br_new.strip()
            ):
                st.error(
                    "Please enter both original and updated "
                    "requirement text."
                )
            else:
                st.session_state["br_req_id"] = _br_req_id
                st.session_state["br_old_req"] = _br_old
                st.session_state["br_new_req"] = _br_new
                try:
                    from Agents.sentinel_impact_agent import (
                        SentinelImpactAgent,
                    )
                    _br_report = (
                        SentinelImpactAgent()
                        .analyze_blast_radius(
                            old_requirement=_br_old,
                            new_requirement=_br_new,
                            requirement_id=_br_req_id,
                        )
                    )
                    st.session_state["br_report"] = (
                        _br_report.to_dict()
                    )
                    st.rerun()
                except Exception as _br_err:
                    st.error(
                        f"Blast radius analysis failed: "
                        f"{_br_err}"
                    )

        # ── Context-Injection Preview (Task 3) ────────────────
        st.markdown("---")
        st.markdown("#### Active Compliance Context")
        try:
            from Agents.compliance_context import (
                ComplianceContext,
                ComplianceMode,
            )
            _br_cm = st.session_state.get(
                "compliance_mode", "GMP"
            )
            _br_ctx = ComplianceContext(
                mode=ComplianceMode(_br_cm),
                sop_guidelines=st.session_state.get(
                    "sop_guidelines", ""
                ),
            )
            st.markdown(
                f'<div style="background:#0d1b2a;border:1px '
                f'solid #1e3a5f;border-radius:6px;'
                f'padding:0.6rem 0.9rem;'
                f'font-size:0.8rem;color:#94a3b8;">'
                f'<strong style="color:#60a5fa;">'
                f'Mode:</strong> {_br_cm} — '
                f'{_br_ctx.get_description()}'
                f'</div>',
                unsafe_allow_html=True,
            )
            with st.expander(
                "View rendered prompt template", expanded=False
            ):
                st.code(
                    _br_ctx.render_prompt(),
                    language="text",
                )
        except Exception:
            pass

    # ── Results panel ─────────────────────────────────────────
    with _br_col_right:
        _br_data = st.session_state.get("br_report")
        if not _br_data:
            st.markdown(
                '<div style="background:#0d1b2a;border:1px '
                'solid #1e3a5f;border-radius:8px;padding:3rem;'
                'text-align:center;color:#64748b;">'
                '<div style="font-size:2.5rem;">⬡</div>'
                "<br/>Run an analysis to see the blast "
                "radius dashboard.</div>",
                unsafe_allow_html=True,
            )
        else:
            _br_cat = _br_data.get(
                "change_category", "Unknown"
            )
            _br_delta = _br_data.get("semantic_delta", "")
            _br_score = _br_data.get("impact_score", 0)
            _br_cat_colours = {
                "Structural":    "#ef4444",
                "Regulatory":    "#f97316",
                "Behavioural":   "#eab308",
                "Clarification": "#22c55e",
            }
            _br_cat_col = _br_cat_colours.get(
                _br_cat, "#94a3b8"
            )

            # ── Sentinel Alert banner ──────────────────────────
            st.markdown(
                f'<div style="background:#0d1b2a;border-left:'
                f"4px solid {_br_cat_col};border-radius:8px;"
                f"padding:0.8rem 1.1rem;"
                f'margin-bottom:0.6rem;">'
                f'<span style="color:{_br_cat_col};'
                f'font-weight:700;font-size:0.82rem;">'
                f'SENTINEL ALERT — {_br_cat.upper()} CHANGE'
                f"</span>"
                f'<div style="color:#cbd5e1;font-size:0.83rem;'
                f'margin-top:0.3rem;">{_br_delta}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── KPI tiles + Impact Score ───────────────────────
            (
                _kpi_r, _kpi_y, _kpi_g,
                _kpi_t, _kpi_s,
            ) = st.columns(5)
            _kpi_specs = [
                (_kpi_r, "#ef4444", "#1a0a0a",
                 _br_data["red_count"], "RERUN"),
                (_kpi_y, "#eab308", "#1a1400",
                 _br_data["yellow_count"], "REVIEW"),
                (_kpi_g, "#22c55e", "#0a1a0a",
                 _br_data["green_count"], "VALID"),
                (_kpi_t, "#3b82f6", "#0f1a2e",
                 f'{_br_data.get("time_saved_hours",0):.1f}h',
                 "SAVED"),
                (_kpi_s, _br_cat_col, "#0d1b2a",
                 _br_score, "IMPACT"),
            ]
            for _col, _fc, _bg, _val, _lbl in _kpi_specs:
                with _col:
                    st.markdown(
                        f'<div style="background:{_bg};'
                        f"border:1px solid {_fc};"
                        f"border-radius:8px;padding:0.6rem;"
                        f'text-align:center;">'
                        f'<div style="color:{_fc};'
                        f'font-size:1.4rem;font-weight:700;">'
                        f"{_val}</div>"
                        f'<div style="color:{_fc};'
                        f'opacity:0.7;font-size:0.65rem;">'
                        f"{_lbl}</div></div>",
                        unsafe_allow_html=True,
                    )

            # ── Visual Network Graph (D3 force graph) ─────────
            _br_ng = _br_data.get("network_graph", {})
            if _br_ng.get("nodes"):
                st.markdown("#### Network Graph")
                import json as _br_js
                _ng_json = _br_js.dumps(_br_ng)
                _graph_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  body {{ margin:0; background:#0a1220; overflow:hidden; }}
  .node circle {{ stroke:#1e3a5f; stroke-width:1.5px;
    cursor:pointer; }}
  .node text {{ fill:#e2e8f0; font-size:10px;
    font-family:monospace; pointer-events:none; }}
  .link {{ stroke-opacity:0.6; }}
  .tooltip {{ position:absolute; background:#1e293b;
    color:#e2e8f0; padding:6px 10px; border-radius:6px;
    font-size:11px; font-family:monospace;
    pointer-events:none; opacity:0; transition:opacity .2s;
    border:1px solid #334155; max-width:220px; }}
</style>
</head>
<body>
<div class="tooltip" id="tip"></div>
<script>
const graph = {_ng_json};
const W = window.innerWidth, H = window.innerHeight;
const svg = d3.select("body").append("svg")
  .attr("width", W).attr("height", H);
const tip = d3.select("#tip");

const sim = d3.forceSimulation(graph.nodes)
  .force("link", d3.forceLink(graph.edges)
    .id(d => d.id).distance(90))
  .force("charge", d3.forceManyBody().strength(-220))
  .force("center", d3.forceCenter(W/2, H/2))
  .force("collide", d3.forceCollide(28));

const link = svg.append("g").selectAll("line")
  .data(graph.edges).join("line")
  .attr("class","link")
  .attr("stroke", d => d.color)
  .attr("stroke-width", 2);

const node = svg.append("g").selectAll("g")
  .data(graph.nodes).join("g")
  .attr("class","node")
  .call(d3.drag()
    .on("start", (e,d) => {{
      if(!e.active) sim.alphaTarget(0.3).restart();
      d.fx=d.x; d.fy=d.y; }})
    .on("drag", (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
    .on("end", (e,d) => {{
      if(!e.active) sim.alphaTarget(0);
      d.fx=null; d.fy=null; }}));

node.append("circle")
  .attr("r", d => d.size || 14)
  .attr("fill", d => d.color)
  .attr("fill-opacity", 0.85)
  .on("mouseover", (e, d) => {{
    tip.style("opacity",1)
      .style("left",(e.pageX+12)+"px")
      .style("top",(e.pageY-8)+"px")
      .html("<b>"+d.id+"</b><br>"+d.label
        +(d.severity?"<br>Severity: "+d.severity:"")
        +(d.type?"<br>Type: "+d.type:""));
  }})
  .on("mouseout", () => tip.style("opacity",0));

node.append("text")
  .attr("dy","0.35em")
  .attr("text-anchor","middle")
  .style("font-size", d => (d.size||14)*0.6+"px")
  .text(d => d.id);

sim.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});
</script>
</body></html>"""
                _st_components.html(
                    _graph_html, height=340
                )

            # ── Impacted Items table ───────────────────────────
            st.markdown("#### Impacted Items")
            _br_items = _br_data.get("impacted_items", [])
            if _br_items:
                _br_rows = []
                for _bi in _br_items:
                    _sev_icon = {
                        "Red": "🔴", "Yellow": "🟡",
                        "Green": "🟢",
                    }.get(_bi["severity"], "⚪")
                    _tier_lbl = {
                        1: "Tier 1", 2: "Tier 2", 3: "Tier 3",
                    }.get(_bi["tier"], "?")
                    _br_rows.append({
                        "Sev": (
                            f'{_sev_icon} {_bi["severity"]}'
                        ),
                        "ID":   _bi["item_id"],
                        "Type": _bi["item_type"].replace(
                            "_", " "
                        ).title(),
                        "Title": _bi["title"],
                        "Tier": _tier_lbl,
                    })
                st.dataframe(
                    pd.DataFrame(_br_rows),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Sev": st.column_config.TextColumn(
                            width="small"
                        ),
                        "ID": st.column_config.TextColumn(
                            width="small"
                        ),
                    },
                )

    # ── Rationalization Log + JSON (full width) ────────────────
    _br_data2 = st.session_state.get("br_report")
    if _br_data2:
        st.markdown("---")
        _rl_tab, _bj_tab, _ctx_tab = st.tabs([
            "Rationalization Log",
            "Blast Radius JSON",
            "Context-Aware Prompt",
        ])

        with _rl_tab:
            _rl = _br_data2.get("rationalization_log", "")
            if _rl:
                st.markdown(
                    '<div style="background:#0a1220;border:1px'
                    ' solid #1e3a5f;border-radius:8px;'
                    'padding:1.2rem;font-family:monospace;'
                    'font-size:0.83rem;white-space:pre-wrap;'
                    'color:#cbd5e1;line-height:1.6;">'
                    + _rl.replace("\n", "<br/>")
                    + "</div>",
                    unsafe_allow_html=True,
                )

        with _bj_tab:
            st.json(
                _br_data2.get("blast_radius_json", {}),
                expanded=True,
            )

        with _ctx_tab:
            try:
                from Agents.compliance_context import (
                    ComplianceContext, ComplianceMode,
                )
                _ct_cm = st.session_state.get(
                    "compliance_mode", "GMP"
                )
                _ct_ctx = ComplianceContext(
                    mode=ComplianceMode(_ct_cm),
                    sop_guidelines=st.session_state.get(
                        "sop_guidelines", ""
                    ),
                )
                st.code(
                    _ct_ctx.render_prompt(),
                    language="text",
                )
            except Exception as _ct_err:
                st.error(str(_ct_err))

        # ── Download ──────────────────────────────────────────
        import json as _br_json_mod
        st.download_button(
            "Download Full Report (JSON)",
            data=_br_json_mod.dumps(_br_data2, indent=2),
            file_name=(
                "blast_radius_"
                + _br_data2.get("requirement_id", "req")
                + "_"
                + _br_data2.get("change_id", "chg")
                + ".json"
            ),
            mime="application/json",
        )
