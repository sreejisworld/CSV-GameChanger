"""Page header and breadcrumb components (SOHO style).

:requirement: URS-1.1 - Consistent navigation chrome.
"""

import streamlit as st


def adversarial_page_header(title: str, subtitle: str) -> None:
    """Render page header with inline Adversarial Red-Teaming toggle.

    Puts the title/subtitle in the left column and the toggle widget
    in the right column.  Uses key ``adversarial_mode`` so the value
    persists in session_state as the user navigates between modules.

    :param title: Page title.
    :param subtitle: Short description.
    :requirement: URS-1.1 - Consistent navigation chrome.
    """
    _h_col, _t_col = st.columns([5, 2])
    with _h_col:
        st.markdown(
            f"""
            <div class="soho-header">
                <h2>{title}</h2>
                <p>{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with _t_col:
        # Vertical nudge so the toggle aligns with the title
        st.markdown("<br/>", unsafe_allow_html=True)
        adv = st.toggle(
            "Adversarial Red-Teaming",
            key="adversarial_mode",
        )
        if adv:
            st.markdown(
                '<span style="color:#f0a500;'
                " font-size:0.72rem;\">"
                "⚡ High Intensity — active</span>",
                unsafe_allow_html=True,
            )


def breadcrumb(stages: list) -> None:
    """Render a SOHO breadcrumb trail.

    :param stages: Ordered list of breadcrumb labels.
    """
    crumbs = (
        ' <span class="breadcrumb-sep">\u203a</span> '
        .join(
            f'<span class="breadcrumb-item">{s}</span>'
            for s in stages
        )
    )
    st.markdown(
        f'<div class="breadcrumb">{crumbs}</div>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    """Render a SOHO page header with title and subtitle.

    :param title: Page title.
    :param subtitle: Short description.
    """
    st.markdown(
        f"""
        <div class="soho-header">
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
