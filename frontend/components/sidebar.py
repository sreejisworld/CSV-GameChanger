"""Sidebar component: dark nav with grouped sections and FA icons.

Renders a fully HTML-driven sidebar with FontAwesome 6 icons,
grouped navigation (DATA / ANALYSIS / WORKFLOW), and live audit
feed.  Navigation uses native Streamlit buttons for reliability
— no JavaScript, no iframes, no browser reloads.

:requirement: URS-1.1 - System navigation.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# ── Navigation structure ─────────────────────────────────────────
NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("DATA", [
        ("1",  "fa-file-lines",             "Ingest Docs"),
        ("2",  "fa-pen-to-square",          "Generate Reqs"),
        ("12", "fa-wand-magic-sparkles",    "SMART Req. Engine"),
    ]),
    ("ANALYSIS", [
        ("3", "fa-scale-balanced",      "Risk Assessment"),
        ("4", "fa-magnifying-glass",    "Gap Analysis"),
        ("5", "fa-clipboard-list",      "Audit Logs"),
    ]),
    ("WORKFLOW", [
        ("6", "fa-industry",    "Validation Factory"),
        ("7", "fa-link",        "Traceability"),
        ("8", "fa-chart-bar",   "Demo Comparison"),
        ("9", "fa-shield-halved", "Command Center"),
        ("10", "fa-file-shield", "VSR"),
        ("11", "fa-satellite-dish", "EVOLV Sentinel"),
    ]),
    ("ENTERPRISE", [
        ("13", "fa-sliders",        "Enterprise Config"),
        ("14", "fa-circle-nodes",   "Blast Radius"),
        ("15", "fa-code",           "Developer Console"),
    ]),
]


def render_sidebar(
    audit_csv: Path,
) -> str:
    """Render the complete sidebar and return the active page id.

    Uses native st.button() for navigation — no JS, no hidden
    widgets, no iframes.  Active item is rendered as styled HTML;
    inactive items are plain Streamlit buttons styled to match via
    CSS.  Falls back to query-param for bookmarks.

    :param audit_csv: Path to the audit trail CSV file.
    :return: Active page id string ("1"–"9").
    """
    # ── Fallback: query-param navigation (bookmarks / deep links) ─
    if "nav" in st.query_params:
        st.session_state["page"] = st.query_params["nav"]
        del st.query_params["nav"]

    # Default page
    if "page" not in st.session_state:
        st.session_state["page"] = "1"
    active_page: str = st.session_state["page"]

    with st.sidebar:
        # ---- Logo ----
        st.markdown(
            """
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">
                    <span>E</span>
                </div>
                <h3>EVOLV</h3>
                <p>THE VALIDATION FACTORY</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ---- Navigation ----
        for group_label, items in NAV_GROUPS:
            st.markdown(
                f'<p class="nav-group-label">{group_label}</p>',
                unsafe_allow_html=True,
            )
            for page_id, fa_icon, label in items:
                if page_id == active_page:
                    # Active item: styled HTML (non-interactive)
                    st.markdown(
                        f'<div class="nav-item active">'
                        f'<i class="fa-solid {fa_icon}"></i>'
                        f'<span class="nav-item-text">{label}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # Inactive item: native Streamlit button
                    if st.button(
                        label,
                        key=f"_nav_btn_{page_id}",
                        use_container_width=True,
                    ):
                        st.session_state["page"] = page_id
                        st.rerun()

        st.markdown("---")

        # ---- System status ----
        st.caption("System Status")
        api_ok = True
        try:
            from API.agent_controller import AgentController  # noqa: F401
        except Exception:
            api_ok = False

        st.markdown(
            f"API Controller: &ensp;"
            f"{'**Online**' if api_ok else '**Offline**'}"
        )
        st.markdown(
            f"Audit Trail: &ensp;"
            f"{'**Active**' if audit_csv.exists() else '**Missing**'}"
        )
        st.caption("v0.1.0")

        # ---- Demo Mode toggle ----
        st.markdown("---")
        demo_on = st.toggle("Demo Mode", key="demo_mode")
        if demo_on:
            st.caption("Showing sample LIMS data")

        # ---- Expert Mode toggle ----
        expert_on = st.toggle(
            "Expert Mode", key="expert_mode",
        )
        if expert_on:
            st.caption(
                "Skip doc lookup \u2014 use custom logic"
            )

        # ---- Adversarial Red-Teaming status (toggle lives
        #      in the Validation Factory page header) ----
        _adv_active = st.session_state.get(
            "adversarial_mode", False
        )
        if _adv_active:
            st.markdown(
                '<span style="color:#f0a500;'
                ' font-size:0.72rem;">'
                '⚡ Adversarial Mode: Active</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Adversarial Mode: Off")

        # ---- Compliance Mode Toggle ----
        st.markdown("---")
        st.caption("Compliance Mode")
        _compliance_opts = ["GMP", "GCP", "GLP", "ISO13485"]
        _compliance_labels = {
            "GMP":      "GMP — 21 CFR Part 211",
            "GCP":      "GCP — ICH E6",
            "GLP":      "GLP — 21 CFR Part 58",
            "ISO13485": "ISO 13485 — MedTech",
        }
        _current_mode = st.session_state.get(
            "compliance_mode", "GMP"
        )
        _selected = st.selectbox(
            "Active Regulation",
            options=_compliance_opts,
            index=_compliance_opts.index(_current_mode),
            format_func=lambda x: _compliance_labels[x],
            key="compliance_mode_selector",
            label_visibility="collapsed",
        )
        if _selected != _current_mode:
            st.session_state["compliance_mode"] = _selected
            st.rerun()

        # ---- Load Demo Project ----
        st.markdown("---")
        if st.button(
            "Load Demo Project",
            key="load_demo_project",
            use_container_width=True,
        ):
            st.session_state["_load_demo_requested"] = True
            st.rerun()
        st.caption(
            "Pre-load LIMS demo for walkthrough"
        )

        # ---- Assurance Record ----
        st.markdown("---")
        st.markdown(
            '<p class="nav-group-label">ASSURANCE</p>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Compile Record of Assurance",
            key="_nav_btn_compile_vsr",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["page"] = "10"
            st.session_state["_compile_vsr_requested"] = True
            st.rerun()

        # ---- Compliance Monitor: Live Audit Feed ----
        st.markdown("---")
        st.caption("Compliance Monitor")
        st.markdown(
            '<p style="font-size:0.7rem; opacity:0.55; '
            'margin:0 0 0.4rem 0;">'
            "21 CFR Part 11 &bull; Live Audit Feed</p>",
            unsafe_allow_html=True,
        )

        if audit_csv.exists():
            try:
                _audit_df = pd.read_csv(audit_csv)
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
                        f'<div class="audit-feed-item">'
                        f"<strong>{_action}</strong><br/>"
                        f'<span class="feed-meta">'
                        f"{_agent} &bull; {_ts}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            except Exception:
                st.markdown(
                    '<span style="font-size:0.75rem; '
                    'opacity:0.6;">Unable to read audit '
                    "trail</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<span style="font-size:0.75rem; '
                'opacity:0.6;">No entries yet</span>',
                unsafe_allow_html=True,
            )

    return active_page
