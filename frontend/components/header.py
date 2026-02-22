"""Page header and breadcrumb components (SOHO style).

:requirement: URS-1.1 - Consistent navigation chrome.
"""

import streamlit as st


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
