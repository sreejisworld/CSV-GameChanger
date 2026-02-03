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
            "4. Gap Analysis",
            "5. Audit Logs",
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


# ===================================================================
# Page 1 — Ingest Vendor Docs
# ===================================================================
if page.startswith("1"):
    _page_header(
        "Ingest Vendor Documents",
        "Upload vendor documentation for GAMP 5 gap analysis",
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
# Page 4 — Gap Analysis Dashboard
# ===================================================================
elif page.startswith("4"):
    _page_header(
        "Gap Analysis Dashboard",
        "Vendor document compliance review against GAMP 5",
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
