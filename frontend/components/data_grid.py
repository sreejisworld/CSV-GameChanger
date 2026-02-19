"""Data-grid helpers: toolbar, empty state, skeleton loader.

:requirement: URS-17.5 - Tabular data presentation.
"""

import streamlit as st


# ── Toolbar ──────────────────────────────────────────────────────

def toolbar(
    title: str = "",
    buttons: list | None = None,
) -> None:
    """Render a SOHO toolbar above a data grid.

    :param title: Optional section label.
    :param buttons: List of dicts with 'label' key.
    """
    btns = buttons or []
    btn_html = ""
    _icons = {
        "Export": (
            '<svg viewBox="0 0 24 24">'
            '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0'
            ' 01-2-2v-4"/>'
            '<polyline points="7 10 12 15 17 10"/>'
            '<line x1="12" y1="15" x2="12" y2="3"/>'
            '</svg>'
        ),
        "Filter": (
            '<svg viewBox="0 0 24 24">'
            '<polygon points="22 3 2 3 10 12.46'
            ' 10 19 14 21 14 12.46 22 3"/>'
            '</svg>'
        ),
    }
    for b in btns:
        lbl = b.get("label", "")
        icon = _icons.get(lbl, "")
        btn_html += (
            f'<span class="toolbar-btn">'
            f'{icon}{lbl}</span>'
        )
    title_html = (
        f'<span class="toolbar-title">{title}</span>'
        if title else ""
    )
    st.markdown(
        f'<div class="soho-toolbar">'
        f'<div class="toolbar-left">{title_html}'
        f'{btn_html}</div></div>',
        unsafe_allow_html=True,
    )


# ── Empty state ──────────────────────────────────────────────────

_EMPTY_ICONS = {
    "document": (
        '<svg width="56" height="56" viewBox="0 0 56 56"'
        ' fill="none" stroke="#CCCCCC" stroke-width="1.5"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 7h20l10 10v32a2 2 0 01-2 2H14a2'
        ' 2 0 01-2-2V9a2 2 0 012-2z"/>'
        '<polyline points="34 7 34 17 44 17"/>'
        '<line x1="20" y1="27" x2="36" y2="27"/>'
        '<line x1="20" y1="33" x2="36" y2="33"/>'
        '<line x1="20" y1="39" x2="28" y2="39"/>'
        '</svg>'
    ),
    "table": (
        '<svg width="56" height="56" viewBox="0 0 56 56"'
        ' fill="none" stroke="#CCCCCC" stroke-width="1.5"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="8" y="10" width="40" height="36"'
        ' rx="2"/>'
        '<line x1="8" y1="20" x2="48" y2="20"/>'
        '<line x1="8" y1="30" x2="48" y2="30"/>'
        '<line x1="8" y1="40" x2="48" y2="40"/>'
        '<line x1="24" y1="10" x2="24" y2="46"/>'
        '</svg>'
    ),
    "search": (
        '<svg width="56" height="56" viewBox="0 0 56 56"'
        ' fill="none" stroke="#CCCCCC" stroke-width="1.5"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="24" cy="24" r="14"/>'
        '<line x1="34" y1="34" x2="46" y2="46"/>'
        '</svg>'
    ),
}


def empty_state(
    title: str,
    description: str,
    icon: str = "document",
    action_label: str = "",
) -> None:
    """Render a centered empty-state placeholder.

    :param title: Bold heading text.
    :param description: Supporting message.
    :param icon: One of 'document', 'table', 'search'.
    :param action_label: Optional CTA button label.
    """
    svg = _EMPTY_ICONS.get(icon, _EMPTY_ICONS["document"])
    action = (
        f'<span class="soho-btn-primary">'
        f'{action_label}</span>'
        if action_label else ""
    )
    st.markdown(
        f'<div class="soho-empty-state">'
        f'{svg}'
        f'<p class="empty-title">{title}</p>'
        f'<p class="empty-desc">{description}</p>'
        f'{action}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Skeleton loading ─────────────────────────────────────────────

def skeleton_table(rows: int = 5) -> None:
    """Show animated skeleton loading placeholder.

    :param rows: Number of placeholder rows.
    """
    row_html = "".join(
        '<div class="skeleton-row"></div>'
        for _ in range(rows)
    )
    st.markdown(
        f'<div class="skeleton-table">'
        f'<div class="skeleton-header"></div>'
        f'{row_html}</div>',
        unsafe_allow_html=True,
    )
