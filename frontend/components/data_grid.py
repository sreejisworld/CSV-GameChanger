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

# Clean Slate: minimalist SVG illustration for a fresh project
_CLEAN_SLATE_SVG = (
    '<svg width="80" height="80" viewBox="0 0 80 80"'
    ' fill="none" xmlns="http://www.w3.org/2000/svg">'
    # Outer circle glow ring
    '<circle cx="40" cy="40" r="36" stroke="currentColor"'
    ' stroke-width="1" opacity="0.12"/>'
    # Document outline
    '<rect x="24" y="16" width="32" height="40" rx="3"'
    ' stroke="currentColor" stroke-width="1.5"'
    ' stroke-linejoin="round"/>'
    # Folded corner
    '<path d="M44 16 L56 28" stroke="currentColor"'
    ' stroke-width="1.5" stroke-linecap="round"/>'
    '<path d="M44 16 L44 28 L56 28"'
    ' stroke="currentColor" stroke-width="1.5"'
    ' fill="none" stroke-linejoin="round"/>'
    # Lines suggesting content
    '<line x1="30" y1="36" x2="50" y2="36"'
    ' stroke="currentColor" stroke-width="1.5"'
    ' stroke-linecap="round"/>'
    '<line x1="30" y1="42" x2="50" y2="42"'
    ' stroke="currentColor" stroke-width="1.5"'
    ' stroke-linecap="round"/>'
    '<line x1="30" y1="48" x2="42" y2="48"'
    ' stroke="currentColor" stroke-width="1.5"'
    ' stroke-linecap="round"/>'
    # Sparkle accent (top-right)
    '<circle cx="58" cy="20" r="3.5"'
    ' fill="#32CD32" opacity="0.60"/>'
    '<circle cx="58" cy="20" r="1.5"'
    ' fill="#32CD32" opacity="0.90"/>'
    '</svg>'
)

_EMPTY_ICONS = {
    "clean_slate": _CLEAN_SLATE_SVG,
    "document": (
        '<svg width="64" height="64" viewBox="0 0 64 64"'
        ' fill="none" stroke="currentColor" stroke-width="1.5"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 8h22l12 12v36a2 2 0 01-2 2H16a2'
        ' 2 0 01-2-2V10a2 2 0 012-2z"/>'
        '<polyline points="38 8 38 20 50 20"/>'
        '<line x1="22" y1="30" x2="42" y2="30"/>'
        '<line x1="22" y1="38" x2="42" y2="38"/>'
        '<line x1="22" y1="46" x2="32" y2="46"/>'
        '</svg>'
    ),
    "table": (
        '<svg width="64" height="64" viewBox="0 0 64 64"'
        ' fill="none" stroke="currentColor" stroke-width="1.5"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="8" y="12" width="48" height="40" rx="3"/>'
        '<line x1="8" y1="24" x2="56" y2="24"/>'
        '<line x1="8" y1="36" x2="56" y2="36"/>'
        '<line x1="8" y1="48" x2="56" y2="48"/>'
        '<line x1="28" y1="12" x2="28" y2="52"/>'
        '</svg>'
    ),
    "search": (
        '<svg width="64" height="64" viewBox="0 0 64 64"'
        ' fill="none" stroke="currentColor" stroke-width="1.5"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="28" cy="28" r="16"/>'
        '<line x1="40" y1="40" x2="54" y2="54"/>'
        '</svg>'
    ),
}


def empty_state(
    title: str,
    description: str,
    icon: str = "clean_slate",
    action_label: str = "",
) -> None:
    """Render a premium Clean Slate empty-state placeholder.

    Uses a minimalist SVG illustration and a single CTA button
    — the hallmark of polished enterprise software.

    :param title: Bold heading text.
    :param description: Supporting message.
    :param icon: One of 'clean_slate', 'document', 'table',
        'search'. Defaults to 'clean_slate'.
    :param action_label: Optional primary action button label.
    :requirement: URS-17.5 - Tabular data presentation.
    """
    svg = _EMPTY_ICONS.get(icon, _EMPTY_ICONS["clean_slate"])
    # Colour the SVG with CSS currentColor via inline style
    svg_wrap = (
        f'<div style="color: var(--ev-slate-light);">'
        f'{svg}</div>'
    )
    action = (
        f'<a class="soho-btn-primary">{action_label}</a>'
        if action_label else ""
    )
    st.markdown(
        f'<div class="soho-empty-state">'
        f'{svg_wrap}'
        f'<p class="empty-title">{title}</p>'
        f'<p class="empty-desc">{description}</p>'
        f'{action}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Shimmer skeleton ─────────────────────────────────────────────

def skeleton_table(rows: int = 5) -> None:
    """Show animated shimmer skeleton loading placeholder.

    Uses the CSS shimmer animation — no spinner, no heavy loader.

    :param rows: Number of placeholder rows.
    :requirement: URS-17.5 - Tabular data presentation.
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
