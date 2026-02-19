"""Theme loader and colour constants for the Infor SOHO design system.

:requirement: URS-15.1 - Branded PDF / UI theming.
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# ── Colour constants ─────────────────────────────────────────────
INFOR_BLUE = "#056696"
INFOR_SLATE = "#54585A"


def load_theme(project_root: Path) -> None:
    """Load the external CSS theme and inject keyboard shortcuts.

    :param project_root: Absolute path to the repository root.
    """
    css_path = project_root / "frontend" / "infor_soho_theme.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}"
            f"</style>",
            unsafe_allow_html=True,
        )

    # Keyboard shortcuts: Ctrl+S → download, Esc → close expanders
    components.html(
        """
        <script>
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
        </script>
        """,
        height=0,
    )
