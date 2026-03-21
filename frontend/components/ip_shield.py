"""IP Shield — Non-copyable, watermarked Read-Only view.

Applies layered IP protection to sensitive report pages (e.g. the
Demo Comparison / "Pains vs. EVOLV" Page 8):

  1. CSS ``user-select: none`` — no text selection / copy
  2. ``contextmenu`` prevention via JS (no right-click menu)
  3. Semi-transparent diagonal watermark overlay
  4. Print-blocking ``@media print`` rule
  5. "PROPRIETARY READ-ONLY" banner at the top of the section

Usage::

    from components.ip_shield import (
        ip_shield_activate,
        ip_shield_section,
        ip_shield_deactivate,
    )

    # Activate once at the top of Page 8:
    ip_shield_activate("EVOLV Confidential · Demo Report")

    # Wrap individual content blocks:
    with ip_shield_section():
        st.markdown("... your protected content ...")

    # Optional: remove protection (e.g. for authenticated users):
    # ip_shield_deactivate()

:requirement: URS-19.6 - Demo Comparison export and IP protection.
"""

from __future__ import annotations
from contextlib import contextmanager

import streamlit as st
import streamlit.components.v1 as components


# ── Activate global IP shield ─────────────────────────────────────

def ip_shield_activate(
    watermark_text: str = "EVOLV CONFIDENTIAL",
    show_banner: bool = True,
) -> None:
    """Inject full-page IP protection for the current page.

    Injects:
    - A global ``<style>`` block that disables text selection,
      hides scrollbars for copy-paste detection, and blocks printing.
    - A diagonal watermark ``::before`` overlay on ``.ip-zone``.
    - A JavaScript snippet blocking right-click inside ``.ip-zone``.
    - An optional READ-ONLY banner at the top of the content.

    Safe to call multiple times per page load (guarded by a flag).

    :param watermark_text: Text rendered as the diagonal watermark.
    :param show_banner: Whether to show the read-only banner pill.
    :requirement: URS-19.6 - Demo Comparison IP protection.
    """
    # Inject CSS: disable selection + watermark + print block
    st.markdown(
        f"""
        <style>
        /* ── IP Shield: disable text selection ──────────────── */
        .ip-zone, .ip-zone * {{
            user-select: none !important;
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
        }}
        /* ── Diagonal watermark overlay ─────────────────────── */
        .ip-zone {{
            position: relative;
        }}
        .ip-zone::after {{
            content: "{watermark_text}";
            position: absolute;
            top: 48%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-32deg);
            font-size: clamp(18px, 3vw, 36px);
            font-weight: 900;
            font-family: 'Inter', 'Geist', system-ui, sans-serif;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(5, 102, 150, 0.05);
            pointer-events: none;
            z-index: 100;
            white-space: nowrap;
            mix-blend-mode: multiply;
        }}
        /* Repeat watermark for tall sections */
        .ip-zone.tall::after {{
            font-size: clamp(22px, 4vw, 48px);
            top: 30%;
        }}
        .ip-zone::before {{
            content: "{watermark_text}";
            position: absolute;
            top: 70%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-32deg);
            font-size: clamp(18px, 3vw, 36px);
            font-weight: 900;
            font-family: 'Inter', 'Geist', system-ui, sans-serif;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(5, 102, 150, 0.04);
            pointer-events: none;
            z-index: 100;
            white-space: nowrap;
            mix-blend-mode: multiply;
        }}
        /* ── Print block ─────────────────────────────────────── */
        @media print {{
            .ip-zone, .ip-shield-banner {{
                display: none !important;
            }}
            body::before {{
                content: "This document is protected. "
                         "Printing is not permitted.";
                display: block;
                font-size: 24px;
                font-weight: bold;
                color: #B94E4E;
                padding: 40px;
                text-align: center;
            }}
        }}
        /* ── Read-only banner ────────────────────────────────── */
        .ip-shield-banner {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(5, 102, 150, 0.07);
            border: 1px solid rgba(5, 102, 150, 0.20);
            border-radius: 999px;
            padding: 4px 14px;
            font-size: 11px;
            font-weight: 700;
            color: #056696;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 16px;
            user-select: none;
        }}
        .ip-shield-banner .shield-icon {{
            font-size: 13px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inject JS: block right-click inside .ip-zone elements
    components.html(
        """
        <script>
        (function() {
          if (parent.__evolvIPShield) return;
          parent.__evolvIPShield = true;

          parent.document.addEventListener('contextmenu', function(e) {
            var zone = e.target.closest
              ? e.target.closest('.ip-zone')
              : null;
            if (zone) {
              e.preventDefault();
              e.stopPropagation();
              return false;
            }
          }, true);

          // Block keyboard copy inside protected zones
          parent.document.addEventListener('keydown', function(e) {
            var zone = e.target.closest
              ? e.target.closest('.ip-zone')
              : null;
            if (zone && (e.ctrlKey || e.metaKey)) {
              var key = e.key.toLowerCase();
              if (key === 'c' || key === 'a' || key === 'x') {
                e.preventDefault();
                return false;
              }
            }
          }, true);

          // Block drag-to-copy inside zones
          parent.document.addEventListener('dragstart', function(e) {
            var zone = e.target.closest
              ? e.target.closest('.ip-zone')
              : null;
            if (zone) {
              e.preventDefault();
              return false;
            }
          }, true);
        })();
        </script>
        """,
        height=0,
        width=0,
    )

    # Show read-only banner
    if show_banner:
        st.markdown(
            '<div class="ip-shield-banner">'
            '<span class="shield-icon">🛡</span>'
            '<span>Proprietary · Read-Only · '
            'EVOLV Confidential</span>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── Protected section wrapper ─────────────────────────────────────

@contextmanager
def ip_shield_section(tall: bool = False):
    """Context manager wrapping content in a protected ``.ip-zone``.

    Must be called after ``ip_shield_activate()``.

    :param tall: If True, adds a second watermark instance for
        sections taller than the viewport.
    :requirement: URS-19.6 - Demo Comparison IP protection.
    """
    extra = " tall" if tall else ""
    st.markdown(
        f'<div class="ip-zone{extra}">',
        unsafe_allow_html=True,
    )
    yield
    st.markdown("</div>", unsafe_allow_html=True)


# ── Deactivate (for authenticated / paid users) ───────────────────

def ip_shield_deactivate() -> None:
    """Inject CSS that removes all ip-zone protections.

    Use this to bypass the shield for authenticated/paid sessions
    where copying is permitted.

    :requirement: URS-19.6 - Demo Comparison IP protection.
    """
    st.markdown(
        """
        <style>
        .ip-zone, .ip-zone * {
            user-select: auto !important;
            -webkit-user-select: auto !important;
        }
        .ip-zone::after,
        .ip-zone::before {
            display: none !important;
        }
        .ip-shield-banner { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
