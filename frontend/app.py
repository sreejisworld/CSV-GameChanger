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
            "4. Audit Logs",
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
    st.caption(f"v0.1.0")


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


# ===================================================================
# Page 1 — Ingest Vendor Docs
# ===================================================================
if page.startswith("1"):
    _page_header(
        "Ingest Vendor Documents",
        "Upload vendor documentation for GAMP 5 gap analysis",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            "Upload a vendor document (.pdf or .docx)",
            type=["pdf", "docx"],
            help="The file will be parsed and checked against "
                 "GAMP 5 requirements.",
        )

        if uploaded is not None:
            dest = VENDOR_DIR / uploaded.name
            VENDOR_DIR.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(uploaded.getvalue())
            st.success(f"Saved to `{dest.relative_to(PROJECT_ROOT)}`")

            if st.button("Run Gap Analysis", type="primary"):
                with st.spinner("Analyzing..."):
                    try:
                        ctrl = AgentController()
                        result = ctrl.analyze_vendor_gaps(
                            str(dest)
                        )
                        st.json(result)
                    except Exception as exc:
                        st.error(f"Analysis failed: {exc}")

    with col2:
        st.markdown("##### Accepted Formats")
        st.markdown(
            "- **PDF** &mdash; vendor SOPs, manuals\n"
            "- **DOCX** &mdash; specifications, protocols"
        )
        existing = list(VENDOR_DIR.glob("*")) if VENDOR_DIR.exists() else []
        if existing:
            st.markdown("##### Previously Uploaded")
            for f in existing[:10]:
                st.text(f.name)


# ===================================================================
# Page 2 — Generate Requirements
# ===================================================================
elif page.startswith("2"):
    _page_header(
        "Generate Requirements (URS)",
        "Describe a requirement in plain English "
        "and the engine produces a GAMP 5 compliant URS",
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

    if st.button("Generate URS", type="primary"):
        if not requirement.strip():
            st.warning("Please enter a requirement description.")
        else:
            with st.spinner("Generating URS..."):
                try:
                    ctrl = AgentController()
                    urs = ctrl.generate_urs(
                        requirement=requirement.strip(),
                        min_score=min_score,
                    )
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
                except Exception as exc:
                    st.error(f"URS generation failed: {exc}")


# ===================================================================
# Page 3 — Risk Assessment (Delta)
# ===================================================================
elif page.startswith("3"):
    _page_header(
        "Risk Assessment (Delta Agent)",
        "GAMP 5 risk evaluation with CSA testing strategy",
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
            except Exception as exc:
                st.error(f"Risk assessment failed: {exc}")


# ===================================================================
# Page 4 — Audit Logs
# ===================================================================
elif page.startswith("4"):
    _page_header(
        "Audit Trail",
        "21 CFR Part 11 compliant, append-only audit log",
    )

    if not AUDIT_CSV.exists():
        st.info(
            "No audit trail found yet. Run an agent action "
            "to create the first entry."
        )
    else:
        df = pd.read_csv(AUDIT_CSV)

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
