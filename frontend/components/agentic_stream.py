"""Agentic Stream: Agentforce-style action blocks with Evolv Reasoning.

Each "Action" in the workspace is rendered as a Stream Block:
  · Header      — agent icon, action type, timestamp
  · Body        — the primary content (yielded by caller)
  · Thought Log — transparent AI reasoning steps
  · Next Steps  — proactive suggested follow-up actions

Usage::

    from components.agentic_stream import (
        action_block, thought_log, next_steps
    )

    with action_block(
        title="URS-7.1 Generated",
        agent="RequirementArchitect",
        status="complete",
        thoughts=[
            "Querying Pinecone for GAMP 5 context...",
            "Applying CSA criticality scoring...",
            "Scanning for PII / patient-safety triggers...",
            "Building regulatory rationale from p.42...",
        ],
    ):
        st.markdown("**The system shall track warehouse temperature.**")
        next_steps([
            ("Generate Test Script",  "vf",  "📋"),
            ("Assess Risk",           "3",   "⚠️"),
            ("View in Traceability",  "7",   "🔗"),
        ])

:requirement: URS-20.1 - Intelligence engine structured output.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import streamlit as st


# ── Agent metadata ────────────────────────────────────────────────

_AGENT_META: dict[str, tuple[str, str]] = {
    "RequirementArchitect": ("📐", "#056696"),
    "VerificationAgent":    ("✅", "#488421"),
    "RiskStrategist":       ("⚠️",  "#D17D00"),
    "DeltaAgent":           ("🧪", "#7C3AED"),
    "IntelligenceEngine":   ("✦",  "#32CD32"),
    "SMARTEngine":          ("🎯", "#0EA5E9"),
    "EvolV":                ("◈",  "#056696"),
}

_STATUS_META: dict[str, tuple[str, str]] = {
    "complete":    ("●", "#488421"),
    "in_progress": ("◌", "#D17D00"),
    "failed":      ("✕", "#B94E4E"),
    "pending":     ("○", "#94A3B8"),
}


# ── Thought Log ───────────────────────────────────────────────────

def thought_log(
    steps: list[str],
    agent: str = "EvolV",
    is_streaming: bool = False,
) -> None:
    """Render an Evolv Reasoning thought-log strip.

    Shows the AI's reasoning chain as an animated sequence of
    timestamped steps — making the AI a transparent partner.

    :param steps: List of reasoning step strings in order.
    :param agent: Agent name for icon lookup.
    :param is_streaming: If True, shows a pulsing spinner on the
        last entry to indicate the AI is still thinking.
    :requirement: URS-20.1 - Intelligence engine structured output.
    """
    if not steps:
        return

    icon, color = _AGENT_META.get(agent, ("◈", "#056696"))

    steps_html = ""
    for i, step in enumerate(steps):
        is_last = i == len(steps) - 1
        spinner = (
            '<span class="thought-spinner"></span>'
            if is_streaming and is_last else ""
        )
        delay = i * 120  # stagger animation in ms
        steps_html += (
            f'<div class="thought-step" '
            f'style="animation-delay:{delay}ms">'
            f'<span class="thought-dot" '
            f'style="background:{color};"></span>'
            f'<span class="thought-text">{step}</span>'
            f'{spinner}'
            f'</div>'
        )

    st.markdown(
        f'<div class="thought-log">'
        f'<div class="thought-log-header">'
        f'<span class="thought-icon">{icon}</span>'
        f'<span class="thought-label">Evolv Reasoning</span>'
        f'</div>'
        f'<div class="thought-steps">{steps_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Next Steps ────────────────────────────────────────────────────

def next_steps(
    suggestions: list[tuple[str, str, str]],
    prefix: str = "Suggested:",
) -> None:
    """Render proactive next-step action pills at the block footer.

    :param suggestions: List of ``(label, page_id, icon)`` tuples.
        Clicking navigates to ``page_id`` and triggers a rerun.
    :param prefix: Short label before the pill row.
    :requirement: URS-20.1 - Intelligence engine structured output.
    """
    if not suggestions:
        return

    pills_html = "".join(
        f'<span class="next-step-pill" '
        f'data-page="{page_id}" '
        f'style="cursor:pointer">'
        f'{icon}&nbsp;{label}'
        f'</span>'
        for label, page_id, icon in suggestions
    )

    # Render the visual strip
    st.markdown(
        f'<div class="next-steps-bar">'
        f'<span class="next-steps-label">{prefix}</span>'
        f'{pills_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Wire up navigation buttons (invisible; pills are visual only)
    cols = st.columns(len(suggestions))
    for col, (label, page_id, icon) in zip(cols, suggestions):
        with col:
            if st.button(
                f"{icon} {label}",
                key=f"_ns_{page_id}_{label[:8]}",
                use_container_width=True,
            ):
                st.session_state["page"] = page_id
                st.rerun()


# ── Action Block ──────────────────────────────────────────────────

@contextmanager
def action_block(
    title: str,
    agent: str = "EvolV",
    status: str = "complete",
    timestamp: str | None = None,
    thoughts: list[str] | None = None,
    key: str = "",
):
    """Context manager that wraps content in an Agentic Stream Block.

    Renders header → body (yielded) → optional thought log.
    The next_steps() helper should be called inside the block body
    to place suggested follow-ups at the block footer.

    :param title:     Block title (action description).
    :param agent:     Agent name — controls icon and accent color.
    :param status:    'complete' | 'in_progress' | 'failed' | 'pending'
    :param timestamp: Display timestamp; defaults to current UTC.
    :param thoughts:  Reasoning steps for the thought log.
    :param key:       Optional unique key.
    :requirement: URS-20.1 - Intelligence engine structured output.
    """
    if not timestamp:
        timestamp = (
            datetime.now(timezone.utc).strftime("%H:%M UTC")
        )

    agent_icon, agent_color = _AGENT_META.get(
        agent, ("◈", "#056696")
    )
    status_icon, status_color = _STATUS_META.get(
        status, ("●", "#488421")
    )
    slug = key or title[:24].replace(" ", "_")

    # ── Block header ──────────────────────────────────────────────
    st.markdown(
        f'<div class="action-block-header" id="ab_{slug}">'
        # Left: agent badge
        f'<span class="agent-badge" '
        f'style="background:{agent_color}18;'
        f'color:{agent_color};'
        f'border:1px solid {agent_color}30;">'
        f'{agent_icon}&nbsp;{agent}'
        f'</span>'
        # Center: title
        f'<span class="action-block-title">{title}</span>'
        # Right: status + time
        f'<span class="action-meta">'
        f'<span class="status-dot" '
        f'style="color:{status_color};">{status_icon}</span>'
        f'<span class="action-ts">{timestamp}</span>'
        f'</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Block body (caller fills in) ──────────────────────────────
    with st.container():
        st.markdown(
            '<div class="action-block-body">',
            unsafe_allow_html=True,
        )
        yield
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Thought log (below body) ──────────────────────────────────
    if thoughts:
        is_live = status == "in_progress"
        thought_log(thoughts, agent=agent, is_streaming=is_live)
