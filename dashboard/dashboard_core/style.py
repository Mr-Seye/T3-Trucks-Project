"""Python script responsible for HTML element styling"""

import streamlit as st


def apply_page_style() -> None:
    """Applies HTML styling to the dashboard."""
    st.set_page_config(
        page_title="T3 CFO Dashboard — Truck Performance", layout="wide")
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
          [data-testid="stMetricValue"] { font-size: 1.6rem; }
          [data-testid="stMetricLabel"] { font-size: 0.95rem; }
          .small-note { color: rgba(49, 51, 63, 0.7); font-size: 0.9rem; }
          .stDataFrame { border-radius: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
