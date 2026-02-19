"""Sidebar component: dark nav with grouped sections and FA icons.

Renders a fully HTML-driven sidebar with FontAwesome 6 icons,
grouped navigation (DATA / ANALYSIS / WORKFLOW), and live audit
feed.  Navigation clicks use Streamlit query-params to communicate
the selected page back to the app.

:requirement: URS-1.1 - System navigation.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path

# ── Navigation structure ─────────────────────────────────────────
NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("DATA", [
        ("1", "fa-file-lines",      "Ingest Docs"),
        ("2", "fa-pen-to-square",   "Generate Reqs"),
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
    ]),
]


def _build_nav_html(active_page: str) -> str:
    """Build the full HTML block for grouped navigation.

    :param active_page: The page id string ("1"–"9").
    :return: HTML string.
    """
    html_parts: list[str] = []
    for group_label, items in NAV_GROUPS:
        html_parts.append(
            f'<p class="nav-group-label">{group_label}</p>'
        )
        for page_id, fa_icon, label in items:
            active_cls = (
                " active" if page_id == active_page else ""
            )
            html_parts.append(
                f'<a class="nav-item{active_cls}" '
                f'href="?nav={page_id}" target="_self">'
                f'<i class="fa-solid {fa_icon}"></i>'
                f'{label}'
                f'</a>'
            )
    return "\n".join(html_parts)


def render_sidebar(
    audit_csv: Path,
) -> str:
    """Render the complete sidebar and return the active page id.

    :param audit_csv: Path to the audit trail CSV file.
    :return: Active page id string ("1"–"9").
    """
    # ---- Handle nav click via query param ----
    if "nav" in st.query_params:
        st.session_state["page"] = st.query_params["nav"]
        del st.query_params["nav"]
        st.rerun()

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

        # ---- Grouped HTML navigation ----
        nav_html = _build_nav_html(active_page)
        st.markdown(
            f'<nav class="sidebar-nav">{nav_html}</nav>',
            unsafe_allow_html=True,
        )

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
