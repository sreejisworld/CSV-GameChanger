"""Theme loader and colour constants for the SOHO design system.

:requirement: URS-15.1 - Branded PDF / UI theming.
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# ── Colour constants ─────────────────────────────────────────────
EV_BLUE = "#056696"
EV_SLATE = "#54585A"

# Backward-compatible aliases
INFOR_BLUE = EV_BLUE
INFOR_SLATE = EV_SLATE


def load_theme(project_root: Path) -> None:
    """Load base + Notion-extension CSS and inject keyboard shortcuts.

    Loads two CSS layers in order:
    1. ``soho_theme.css`` — design tokens, sidebar, components
    2. ``notion_theme.css`` — centered workspace, block cards,
       ghost-text and selection-toolbar styles

    Reads ``dark_mode`` from session state and sets ``data-theme``
    on the host document so CSS custom-property overrides activate.

    :param project_root: Absolute path to the repository root.
    :requirement: URS-15.1 - Branded PDF / UI theming.
    """
    frontend = project_root / "frontend"
    css_files = [
        frontend / "soho_theme.css",
        frontend / "notion_theme.css",
    ]
    combined = "\n".join(
        p.read_text(encoding="utf-8")
        for p in css_files
        if p.exists()
    )
    if combined:
        st.markdown(
            f"<style>{combined}</style>",
            unsafe_allow_html=True,
        )

    # Apply dark/light theme attribute to the host document
    is_dark = st.session_state.get("dark_mode", False)
    theme_val = "dark" if is_dark else "light"
    components.html(
        f"""<script>
        (function() {{
            var root = parent.document.documentElement;
            root.setAttribute('data-theme', '{theme_val}');
            // Also apply to the main app container
            var app = parent.document.querySelector(
                '[data-testid="stAppViewContainer"]'
            );
            if (app) app.setAttribute('data-theme', '{theme_val}');
        }})();
        </script>""",
        height=0,
        width=0,
    )

    # Keyboard shortcuts: Ctrl+S → download, Esc → close expanders
    components.html(
        """<script>
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                var btn = parent.document.querySelector(
                    '[data-testid="stDownloadButton"] button'
                );
                if (btn) btn.click();
            }
            if (e.key === 'Escape') {
                parent.document.querySelectorAll('details[open]')
                    .forEach(function(el) {
                        el.removeAttribute('open');
                    });
            }
        });
        </script>""",
        height=0,
        width=0,
    )
