"""Notion-style Block Editor components for EVOLV.

Each requirement is a Card Block: closed by default (title only),
with a toggle to reveal its AI-generated SMART fields.

Usage::

    from components.block_editor import (
        workspace_header,
        card_block,
        smart_fields,
        block_divider,
    )

    workspace_header("Generate Requirements", "GAMP 5 · GMP Mode")

    with card_block("The system shall track warehouse temperature",
                    risk="high", key="req_001"):
        smart_fields({
            "Specific":     "Temperature logging in cold store A",
            "Measurable":   "±0.5 °C precision, logged every 5 min",
            "Achievable":   "Via IoT sensor API integration",
            "Relevant":     "GxP Direct — patient safety impact",
            "Time-bound":   "Real-time; 24h retention minimum",
        })

:requirement: URS-21.6 - SMART requirement structured output.
"""

from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


# ── Workspace header ──────────────────────────────────────────────

def workspace_header(
    title: str,
    subtitle: str = "",
    meta: list[str] | None = None,
) -> None:
    """Render a Notion-style full-width page title.

    :param title: Page title (large, bold).
    :param subtitle: Optional muted subtitle.
    :param meta: Optional list of meta-pill strings
        (e.g. ["GMP Mode", "v0.1.0"]).
    :requirement: URS-1.1 - Consistent navigation chrome.
    """
    meta_html = ""
    if meta:
        pills = "".join(
            f'<span style="display:inline-flex;align-items:center;'
            f'gap:4px;padding:2px 10px;background:var(--ev-bg-alt);'
            f'border-radius:999px;font-size:0.75rem;'
            f'color:var(--ev-slate-light);">{m}</span>'
            for m in meta
        )
        meta_html = (
            f'<div class="nph-meta" '
            f'style="margin-top:8px;display:flex;'
            f'flex-wrap:wrap;gap:6px;">'
            f'{pills}</div>'
        )
    st.markdown(
        f'<div class="notion-page-header">'
        f'<p class="nph-title">{title}</p>'
        + (
            f'<p class="nph-subtitle">{subtitle}</p>'
            if subtitle else ""
        )
        + meta_html
        + "</div>",
        unsafe_allow_html=True,
    )


# ── Block divider ─────────────────────────────────────────────────

def block_divider() -> None:
    """Render a subtle Notion-style section divider.

    :requirement: URS-1.1 - Consistent navigation chrome.
    """
    st.markdown(
        '<div class="notion-divider"></div>',
        unsafe_allow_html=True,
    )


# ── Card Block ────────────────────────────────────────────────────

@contextmanager
def card_block(
    title: str,
    risk: str = "info",
    badge_text: str = "",
    key: str = "",
    default_open: bool = False,
):
    """Context manager that renders a collapsible requirement block.

    By default the block shows only the title (closed). Clicking
    the expander reveals SMART fields or any content yielded inside
    the context manager.

    The implementation wraps Streamlit's native ``st.expander`` so
    standard Streamlit widgets work inside it.

    :param title: The requirement title shown in the header row.
    :param risk: One of 'high', 'medium', 'low', 'info'. Controls
        the colored indicator dot.
    :param badge_text: Optional badge label (e.g. "GxP Direct").
    :param key: Unique key; defaults to a slug of title.
    :param default_open: Whether to render the block open
        by default.
    :requirement: URS-21.6 - SMART requirement structured output.
    """
    # Build a tidy expander summary with indicator + optional badge
    _slug = key or title[:40].replace(" ", "_")
    _risk_colors = {
        "high":   "#B94E4E",
        "medium": "#D17D00",
        "low":    "#488421",
        "info":   "#056696",
    }
    _dot_color = _risk_colors.get(risk.lower(), "#056696")

    _badge_html = ""
    if badge_text:
        _bg_map = {
            "high":   "var(--ev-red-bg)",
            "medium": "var(--ev-amber-bg)",
            "low":    "var(--ev-green-bg)",
            "info":   "var(--ev-blue-bg)",
        }
        _fg_map = {
            "high":   "var(--ev-red)",
            "medium": "var(--ev-amber)",
            "low":    "var(--ev-green)",
            "info":   "var(--ev-blue)",
        }
        _badge_html = (
            f' <span style="display:inline-block;'
            f'padding:1px 8px;'
            f'background:{_bg_map.get(risk,"var(--ev-blue-bg)")};'
            f'color:{_fg_map.get(risk,"var(--ev-blue)")};'
            f'border-radius:999px;font-size:0.78rem;'
            f'font-weight:600;">{badge_text}</span>'
        )

    _indicator = (
        f'<span style="display:inline-block;width:8px;height:8px;'
        f'border-radius:50%;background:{_dot_color};'
        f'flex-shrink:0;margin-right:2px;"></span>'
    )
    _summary = (
        f"{_indicator} {title}{_badge_html}"
    )

    with st.expander(_summary, expanded=default_open):
        yield


# ── SMART Fields Grid ─────────────────────────────────────────────

def smart_fields(
    fields: dict[str, str],
    columns: int = 2,
) -> None:
    """Render a responsive grid of SMART field cards.

    :param fields: Dict of {label: value} pairs, e.g.::

        {
            "Specific":   "Monitor temperature in cold store A",
            "Measurable": "±0.5 °C precision, every 5 min",
        }

    :param columns: Number of columns in the grid (default 2).
    :requirement: URS-21.6 - SMART requirement structured output.
    """
    items_html = "".join(
        f'<div class="smart-field">'
        f'<div class="smart-field-label">{label}</div>'
        f'<div class="smart-field-value">{value}</div>'
        f'</div>'
        for label, value in fields.items()
        if value
    )
    st.markdown(
        f'<div class="smart-fields">{items_html}</div>',
        unsafe_allow_html=True,
    )


# ── Requirement list renderer ─────────────────────────────────────

def requirement_blocks(
    requirements: list[dict],
    id_key: str = "URS_ID",
    title_key: str = "Requirement_Statement",
    criticality_key: str = "Criticality",
    rationale_key: str = "Regulatory_Rationale",
    show_smart: bool = True,
) -> None:
    """Render a list of URS dicts as collapsible card blocks.

    A convenience wrapper around ``card_block`` for the common case
    of displaying a list of generated requirements.

    :param requirements: List of URS dicts from RequirementArchitect.
    :param id_key: Key for the URS ID field.
    :param title_key: Key for the requirement statement.
    :param criticality_key: Key for High/Medium/Low criticality.
    :param rationale_key: Key for regulatory rationale text.
    :param show_smart: Whether to show the SMART fields section.
    :requirement: URS-21.6 - SMART requirement structured output.
    """
    if not requirements:
        from components.data_grid import empty_state
        empty_state(
            "Clean Slate",
            "No requirements yet. Start typing above to generate "
            "your first GAMP 5-aligned requirement.",
            icon="clean_slate",
            action_label="Start your first Validation",
        )
        return

    _crit_to_risk = {
        "high":   "high",
        "medium": "medium",
        "low":    "low",
    }

    for req in requirements:
        urs_id    = req.get(id_key, "URS-?")
        title     = req.get(title_key, "Untitled requirement")
        crit_raw  = req.get(criticality_key, "medium")
        crit      = str(crit_raw).lower()
        risk      = _crit_to_risk.get(crit, "info")
        rationale = req.get(rationale_key, "")

        with card_block(
            title=f"{urs_id} — {title}",
            risk=risk,
            badge_text=str(crit_raw).title(),
            key=urs_id,
        ):
            if rationale:
                st.markdown(
                    f'<div class="soho-info-box">'
                    f'<strong>Regulatory Rationale</strong><br/>'
                    f'{rationale}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if show_smart:
                smart_fields({
                    "Criticality":   str(crit_raw).title(),
                    "URS ID":        urs_id,
                    "Risk level":    risk.title(),
                })
