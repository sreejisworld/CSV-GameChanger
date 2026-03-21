"""Humanization helpers: Evolv Pulse indicator, Last Verified stamp.

These micro-components reinforce EVOLV's dual identity: AI-powered
precision with human accountability at every step.

Usage::

    from components.humanize import evolv_pulse, last_verified_stamp

    # Next to an AI-assisted input field label
    evolv_pulse()

    # Below a generated requirement
    last_verified_stamp("Jane Smith", "2026-03-14 10:42 UTC")

:requirement: URS-13.1 - Human oversight and audit accountability.
"""

from datetime import datetime, timezone

import streamlit as st


# ── Evolv Pulse ──────────────────────────────────────────────────

def evolv_pulse(label: str = "AI-assisted") -> None:
    """Render a subtle glowing Evolv Pulse indicator.

    Replaces bulky 'Ask AI' buttons with a single pulsing dot
    that signals AI readiness without visual noise.

    :param label: Micro-label next to the dot. Pass an empty
        string to show the dot only.
    :requirement: URS-13.1 - Human oversight indicator.
    """
    label_html = (
        f'<span class="evolv-pulse-label">{label}</span>'
        if label else ""
    )
    st.markdown(
        f'<div class="evolv-pulse-wrap">'
        f'<span class="evolv-pulse"></span>'
        f'{label_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Last Verified stamp ──────────────────────────────────────────

def last_verified_stamp(
    user_name: str,
    timestamp: str | None = None,
) -> None:
    """Render a 'Last Verified by [User]' pill stamp.

    Signals that a human has reviewed this requirement —
    the human is the hero; EVOLV is the tool.

    :param user_name: Full name or username of the reviewer.
    :param timestamp: ISO-8601 or display-ready timestamp string.
        Defaults to current UTC time if not supplied.
    :requirement: URS-13.1 - Human oversight and accountability.
    """
    if not timestamp:
        timestamp = (
            datetime.now(timezone.utc)
            .strftime("%Y-%m-%d %H:%M UTC")
        )
    st.markdown(
        f'<div class="last-verified-stamp">'
        f'<span class="lv-dot"></span>'
        f'<span>Last verified by&nbsp;'
        f'<span class="lv-user">{user_name}</span></span>'
        f'<span class="lv-time">· {timestamp}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Inline AI field wrapper ──────────────────────────────────────

def ai_field_header(label: str) -> None:
    """Render a field label with an Evolv Pulse dot inline.

    Provides a drop-in header for any textarea or text_input
    that is AI-assisted, replacing the old 'Ask AI' button
    pattern with a non-intrusive pulse indicator.

    :param label: The field label to display.
    :requirement: URS-13.1 - Human oversight indicator.
    """
    st.markdown(
        f'<div class="evolv-pulse-wrap" '
        f'style="margin-bottom: 0.25rem;">'
        f'<span style="font-size:14px; font-weight:600; '
        f'color:var(--ev-slate); letter-spacing:0.01em;">'
        f'{label}</span>'
        f'<span class="evolv-pulse" '
        f'style="margin-left:4px;"></span>'
        f'</div>',
        unsafe_allow_html=True,
    )
