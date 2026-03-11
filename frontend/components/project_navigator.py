"""
ProjectNavigator component.

Renders a hierarchical tree view of all EVOLV projects,
releases, and GAMP 5 folders using Streamlit native widgets
with custom CSS styling.  Selection state is stored in
``st.session_state`` under the ``pn_`` prefix.

:requirement: URS-30.1 - Hierarchical project/release
              tree view.
:requirement: URS-30.2 - Auto-populate GAMP 5 folders on
              New Release.
:requirement: URS-30.3 - Move items between releases.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


# ─────────────────────────────────────────────────────────────
# Icon map
# ─────────────────────────────────────────────────────────────

_FOLDER_ICONS: Dict[str, str] = {
    "URS":                    "📋",
    "Risk Assessment":        "⚠️",
    "Functional Specifications": "📐",
    "Test Scripts":           "🧪",
    "Traceability Matrix":    "🔗",
    "VSR":                    "📄",
    "Supplier Assessment":    "🏭",
}

_TYPE_ICONS: Dict[str, str] = {
    "urs":          "📋",
    "test_script":  "🧪",
    "risk":         "⚠️",
    "traceability": "🔗",
    "report":       "📄",
    "note":         "📝",
    "supplier_doc": "🏭",
}

_STATUS_COLORS: Dict[str, str] = {
    "Draft":     "#94a3b8",
    "In Review": "#f0a500",
    "Approved":  "#22c55e",
    "Rejected":  "#f87171",
    "Retired":   "#475569",
    "Planned":   "#64748b",
    "In Progress": "#3b82f6",
    "Released":  "#22c55e",
    "Archived":  "#475569",
}

_RELEASE_STATUS_ICONS: Dict[str, str] = {
    "Planned":     "🔵",
    "In Progress": "🟡",
    "Released":    "🟢",
    "Archived":    "⚫",
}


def _status_badge(status: str) -> str:
    """Return an HTML color badge for *status*."""
    color = _STATUS_COLORS.get(status, "#94a3b8")
    return (
        f'<span style="background:{color}20;color:{color};'
        f"border:1px solid {color}55;border-radius:4px;"
        f'padding:1px 6px;font-size:0.68rem;'
        f'font-weight:600;">{status}</span>'
    )


def _node_css() -> str:
    """Return the CSS block for tree node styling."""
    return """
<style>
.pn-project-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.4rem;
    border-radius: 6px;
    margin-bottom: 0.2rem;
    background: #0f2137;
    border-left: 3px solid #3b82f6;
}
.pn-release-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.4rem 0.35rem 1.2rem;
    border-radius: 4px;
    margin-bottom: 0.15rem;
    background: #0d1b2a;
    border-left: 2px solid #1e3a5f;
    font-size: 0.88rem;
    color: #cbd5e1;
}
.pn-folder-label {
    font-size: 0.8rem;
    color: #94a3b8;
    padding: 0.2rem 0.4rem 0.2rem 2rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}
.pn-item-row {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.15rem 0.4rem 0.15rem 2.8rem;
    font-size: 0.78rem;
    color: #94a3b8;
    border-left: 1px solid #1e293b;
    margin-left: 2rem;
}
.pn-item-active {
    background: #0f2137;
    color: #e2e8f0;
    border-radius: 4px;
}
.pn-stat-pill {
    font-size: 0.65rem;
    background: #1e3a5f;
    color: #64748b;
    border-radius: 10px;
    padding: 1px 6px;
    margin-left: auto;
}
</style>
"""


# ─────────────────────────────────────────────────────────────
# Selection state helpers
# ─────────────────────────────────────────────────────────────

def get_selection() -> Dict[str, Any]:
    """
    Return the current tree selection from session_state.

    Shape::

        {
            "type": "project"|"release"|"folder"|"item",
            "project_id": str,
            "release_id": str | None,
            "folder_name": str | None,
            "item_id": str | None,
        }
    """
    return st.session_state.get(
        "pn_selection",
        {
            "type":        None,
            "project_id":  None,
            "release_id":  None,
            "folder_name": None,
            "item_id":     None,
        },
    )


def _set_selection(
    sel_type: str,
    project_id: Optional[str] = None,
    release_id: Optional[str] = None,
    folder_name: Optional[str] = None,
    item_id: Optional[str] = None,
) -> None:
    """Write selection to session_state and rerun."""
    st.session_state["pn_selection"] = {
        "type":        sel_type,
        "project_id":  project_id,
        "release_id":  release_id,
        "folder_name": folder_name,
        "item_id":     item_id,
    }


# ─────────────────────────────────────────────────────────────
# Main render function
# ─────────────────────────────────────────────────────────────

def render_navigator(store: Any) -> None:
    """
    Render the full ProjectNavigator tree in the current
    Streamlit column/container.

    Injects CSS once, then renders each project as a
    collapsible block containing releases and GAMP 5 folders.

    :param store: ProjectStore instance.
    :requirement: URS-30.1
    """
    st.markdown(_node_css(), unsafe_allow_html=True)

    projects = store.list_projects()

    if not projects:
        st.markdown(
            '<div style="color:#475569;font-size:0.82rem;'
            'padding:1rem;text-align:center;">'
            "No projects yet.<br/>Click "
            "<strong>+ New Project</strong> to start."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    sel = get_selection()

    for proj in projects:
        _render_project_node(proj, store, sel)


def _render_project_node(
    proj: Any,
    store: Any,
    sel: Dict[str, Any],
) -> None:
    """Render one project block with its releases."""
    is_active_proj = (
        sel.get("project_id") == proj.project_id
    )
    release_count = len(proj.releases)

    # Project header — click to select
    header_html = (
        '<div class="pn-project-header">'
        '<span style="font-size:1rem;">📁</span>'
        f'<span style="color:#e2e8f0;font-weight:600;'
        f'font-size:0.9rem;flex:1;">{proj.name}</span>'
        f'<span class="pn-stat-pill">'
        f"{release_count} rel.</span>"
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    if st.button(
        "Select project",
        key=f"pn_sel_proj_{proj.project_id}",
        use_container_width=True,
    ):
        _set_selection("project", proj.project_id)
        st.rerun()

    if not proj.releases:
        st.markdown(
            '<div style="color:#475569;font-size:0.75rem;'
            'padding:0.2rem 0 0.2rem 1.5rem;">'
            "No releases — click + New Release"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # Render releases
    for rel_id, rel_d in proj.releases.items():
        from API.project_store import Release
        rel = Release.from_dict(rel_d)
        _render_release_node(
            proj, rel, store, sel
        )


def _render_release_node(
    proj: Any,
    rel: Any,
    store: Any,
    sel: Dict[str, Any],
) -> None:
    """Render one release block with its folders."""
    is_active_rel = (
        sel.get("release_id") == rel.release_id
    )
    status_icon = _RELEASE_STATUS_ICONS.get(
        rel.status, "⚪"
    )
    item_total = rel.item_count()

    with st.expander(
        f"{status_icon} {rel.name}  "
        f"({item_total} items)",
        expanded=is_active_rel,
    ):
        if st.button(
            f"Open {rel.version}",
            key=f"pn_sel_rel_{rel.release_id}",
            use_container_width=True,
        ):
            _set_selection(
                "release",
                proj.project_id,
                rel.release_id,
            )
            st.rerun()

        # Folders
        for folder_name, items in rel.folders.items():
            folder_icon = _FOLDER_ICONS.get(
                folder_name, "📂"
            )
            count = len(items)
            is_active_folder = (
                sel.get("folder_name") == folder_name
                and sel.get("release_id")
                == rel.release_id
            )

            folder_html = (
                '<div class="pn-folder-label">'
                f"{folder_icon} "
                f'<span style="color:'
                f'{"#e2e8f0" if is_active_folder else "#94a3b8"}'
                f';font-size:0.8rem;">{folder_name}</span>'
                f'<span class="pn-stat-pill">'
                f"{count}</span>"
                "</div>"
            )
            st.markdown(
                folder_html, unsafe_allow_html=True
            )

            if st.button(
                folder_name,
                key=(
                    f"pn_sel_folder_"
                    f"{rel.release_id}_{folder_name}"
                ),
                use_container_width=True,
            ):
                _set_selection(
                    "folder",
                    proj.project_id,
                    rel.release_id,
                    folder_name,
                )
                st.rerun()

            # Items in folder
            for item_d in items:
                _render_item_row(
                    proj, rel, folder_name,
                    item_d, sel,
                )


def _render_item_row(
    proj: Any,
    rel: Any,
    folder_name: str,
    item_d: Dict[str, Any],
    sel: Dict[str, Any],
) -> None:
    """Render a single item row inside a folder."""
    from API.project_store import FolderItem
    item = FolderItem.from_dict(item_d)

    is_active = sel.get("item_id") == item.item_id
    icon = _TYPE_ICONS.get(item.item_type, "📄")
    status_color = _STATUS_COLORS.get(
        item.status, "#94a3b8"
    )

    item_html = (
        f'<div class="pn-item-row'
        f'{"  pn-item-active" if is_active else ""}">'
        f"{icon} "
        f'<span style="flex:1;overflow:hidden;'
        f'text-overflow:ellipsis;white-space:nowrap;">'
        f"{item.name}</span>"
        f'<span style="color:{status_color};'
        f'font-size:0.65rem;flex-shrink:0;">'
        f"●</span>"
        "</div>"
    )
    st.markdown(item_html, unsafe_allow_html=True)

    if st.button(
        item.name[:28],
        key=f"pn_sel_item_{item.item_id}",
        use_container_width=True,
    ):
        _set_selection(
            "item",
            proj.project_id,
            rel.release_id,
            folder_name,
            item.item_id,
        )
        st.rerun()
