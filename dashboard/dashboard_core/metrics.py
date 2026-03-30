"""Python script that calcuates metrics for the streamlit app"""

import pandas as pd
import streamlit as st


def safe_pct(x: float) -> str:
    """Returns a percentage to 1.d.p."""
    return f"{x * 100:.1f}%"


def currency(v: float) -> str:
    """Returns a number in currency format (2.d.p)."""
    return f"{v:,.2f}"


@st.cache_data(ttl=300, show_spinner=False)
def compute_trend(df: pd.DataFrame, time_grain: str) -> pd.DataFrame:
    """Returns a dataframe of daily or hourly transaction trends."""
    if time_grain == "Daily":
        return (
            df.groupby("day_dt", as_index=False)
              .agg(
                  revenue=("total", "sum"),
                  transactions=("transaction_id", "nunique"),
                  avg_sale=("total", "mean"),
            )
            .sort_values("day_dt")
        )
    return (
        df.groupby("hour_ts", as_index=False)
          .agg(
              revenue=("total", "sum"),
              transactions=("transaction_id", "nunique"),
              avg_sale=("total", "mean"),
        )
        .sort_values("hour_ts")
    )


@st.cache_data(ttl=300, show_spinner=False)
def compute_truck_perf(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe of individual truck sales performance"""
    return (
        df.groupby("truck_name", as_index=False)
          .agg(
              revenue=("total", "sum"),
              transactions=("transaction_id", "nunique"),
              avg_sale=("total", "mean"),
              cash_share=("payment_method", lambda s: float(
                  s.eq("cash").mean())),
        )
    )


@st.cache_data(ttl=300, show_spinner=False)
def compute_payment_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe of the split between payment methods."""
    pm = (
        df["payment_method"]
        .value_counts(dropna=False)
        .rename_axis("payment_method")
        .reset_index(name="count")
    )
    pm["payment_method"] = pm["payment_method"].fillna("unknown")
    return pm
