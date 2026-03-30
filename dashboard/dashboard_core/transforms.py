"""Python script responsible for manipulating/transforming data."""
import pandas as pd
import streamlit as st


@st.cache_data(ttl=900, show_spinner=False)
def clean_base_df(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a cleaned and correctly cast dataframe"""
    df = df.copy()
    # Transaction totals likely stored in pence, so we divide by 100 for pounds
    df["total"] = pd.to_numeric(df["total"], errors="coerce") / 100
    df["truck_name"] = df["truck_name"].astype("string").str.strip()
    df["payment_method"] = df["payment_method"].astype(
        "string").str.strip().str.lower()
    df["day_dt"] = pd.to_datetime(df["day_dt"], errors="coerce")
    df["hour_ts"] = pd.to_datetime(df["hour_ts"], errors="coerce")

    df = df.dropna(subset=["total", "truck_name", "day_dt", "hour_ts"])
    df = df[df["total"] > 0]
    return df


@st.cache_data(ttl=300, show_spinner=False)
def apply_filters(
    df: pd.DataFrame,
    payment_filter: tuple[str],
    selected_trucks: tuple[str]
) -> pd.DataFrame:
    """Returns output depending on selected filters"""
    out = df
    if payment_filter:
        out = out[out["payment_method"].isin(payment_filter)]
    if selected_trucks:
        out = out[out["truck_name"].isin(selected_trucks)]
    return out
