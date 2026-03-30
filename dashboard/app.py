"""Main Streamlit app for the dashboard"""
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from dashboard_core.style import apply_page_style
from dashboard_core.config import load_config
from dashboard_core.queries import load_transactions_joined
from dashboard_core.transforms import clean_base_df, apply_filters
from dashboard_core.metrics import (
    currency, safe_pct, compute_trend, compute_truck_perf, compute_payment_mix
)
from dashboard_core.charts import revenue_trend_chart, payment_mix_pie, truck_bar_chart

load_dotenv()
apply_page_style()

cfg = load_config()

st.title("T3 CFO Dashboard — Truck Performance")
st.caption(
    "Stakeholder: Hiram (CFO)."
)

with st.sidebar:
    st.header("Filters")

    today = date.today()
    default_start = today - timedelta(days=30)

    date_range = st.date_input(
        "Date range",
        value=(default_start, today),
        min_value=date(2000, 1, 1),
        max_value=today,
    )
    if isinstance(date_range, tuple):
        start_dt, end_dt = date_range
    else:
        start_dt, end_dt = date_range, date_range

    st.divider()

    sort_metric = st.selectbox(
        "Sort trucks by",
        options=["Revenue (sum)", "Transactions (count)",
                 "Average ticket (mean)"],
        index=0,
    )

    payment_filter_ui = st.multiselect(
        "Payment method (optional)",
        options=["cash", "card"],
        default=[],
        help="Leave empty to include both.",
    )

    time_grain = st.radio(
        "Trend grain",
        options=["Daily", "Hourly"],
        index=0,
        help="Hourly uses partition-derived hour timestamps.",
    )

    st.divider()

# Load data (cached in queries.py)
try:
    with st.spinner("Querying Athena..."):
        raw = load_transactions_joined(cfg, start_dt, end_dt)
        base_df = clean_base_df(raw)
except Exception as e:
    st.error("Could not load data from Athena.")
    st.exception(e)
    st.stop()

# Truck selector
tmp_for_trucks = base_df
if payment_filter_ui:
    tmp_for_trucks = tmp_for_trucks[tmp_for_trucks["payment_method"].isin(
        payment_filter_ui)]
all_trucks = sorted(tmp_for_trucks["truck_name"].dropna().unique().tolist())

selected_trucks_ui = st.multiselect(
    "Trucks to include (optional)",
    options=all_trucks,
    default=all_trucks,
)

df = apply_filters(
    base_df,
    payment_filter=tuple(payment_filter_ui),
    selected_trucks=tuple(selected_trucks_ui),
)

if df.empty:
    st.warning("No data available for the chosen filters.")
    st.stop()

# KPIs
total_revenue = float(df["total"].sum())
n_transactions = int(df["transaction_id"].nunique())
avg_sale = float(df["total"].mean())
cash_share = float(df["payment_method"].eq("cash").mean())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Revenue (selected period)", currency(total_revenue))
k2.metric("Transactions", f"{n_transactions:,}")
k3.metric("Average ticket", currency(avg_sale))
k4.metric("Cash share (by count)", safe_pct(cash_share))

# Aggregations (cached in metrics.py)
trend = compute_trend(df, time_grain=time_grain)
truck_perf = compute_truck_perf(df)
pm = compute_payment_mix(df)

# Sorting
if sort_metric == "Revenue (sum)":
    truck_perf = truck_perf.sort_values("revenue", ascending=False)
elif sort_metric == "Transactions (count)":
    truck_perf = truck_perf.sort_values("transactions", ascending=False)
else:
    truck_perf = truck_perf.sort_values("avg_sale", ascending=False)

top_truck_by_tx = truck_perf.sort_values(
    "transactions", ascending=False).iloc[0]["truck_name"]
top_truck_by_rev = truck_perf.sort_values(
    "revenue", ascending=False).iloc[0]["truck_name"]
bottom_truck_by_rev = truck_perf.sort_values(
    "revenue", ascending=True).iloc[0]["truck_name"]

st.caption(
    f"Highlights: Top by revenue: **{top_truck_by_rev}** · Top by volume: **{top_truck_by_tx}** · "
    f"Lowest revenue: **{bottom_truck_by_rev}**"
)

# Charts
c1, c2 = st.columns((2, 1))
with c1:
    st.subheader("Revenue trend")
    st.altair_chart(revenue_trend_chart(
        trend, time_grain), use_container_width=True)

with c2:
    st.subheader("Payment mix")
    st.altair_chart(payment_mix_pie(pm), use_container_width=True)

st.subheader("Truck performance comparison")

bar_metric = st.radio(
    "Compare trucks by",
    options=["Revenue", "Transactions", "Average ticket", "Cash share"],
    horizontal=True,
)

metric_map = {
    "Revenue": ("revenue", "Revenue"),
    "Transactions": ("transactions", "Transactions"),
    "Average ticket": ("avg_sale", "Average ticket"),
    "Cash share": ("cash_share", "Cash share"),
}
field, title = metric_map[bar_metric]
st.altair_chart(truck_bar_chart(truck_perf, field, title),
                use_container_width=True)

# Table
st.subheader("Truck performance table")
display = truck_perf.copy()
display["revenue"] = display["revenue"].round(2)
display["avg_sale"] = display["avg_sale"].round(2)
display["cash_share_%"] = (display["cash_share"] * 100).round(1)
display = display.drop(columns=["cash_share"])
st.dataframe(display, use_container_width=True, hide_index=True)

# Action cues
st.subheader("Action cues (cost control & profit focus)")
low_rev_threshold = truck_perf["revenue"].quantile(0.25)
high_cash_threshold = truck_perf["cash_share"].quantile(0.75)

low_rev = truck_perf[truck_perf["revenue"] <= low_rev_threshold][
    ["truck_name", "revenue", "transactions", "avg_sale"]
]
high_cash = truck_perf[truck_perf["cash_share"] >= high_cash_threshold][
    ["truck_name", "cash_share", "transactions"]
]

a1, a2 = st.columns(2)

with a1:
    st.markdown("**Underperforming trucks (bottom quartile revenue)**")
    if low_rev.empty:
        st.write("None identified.")
    else:
        st.dataframe(low_rev, use_container_width=True, hide_index=True)

with a2:
    st.markdown("**High cash reliance (top quartile cash share)**")
    if high_cash.empty:
        st.write("None identified.")
    else:
        tmp = high_cash.copy()
        tmp["cash_share_%"] = (tmp["cash_share"] * 100).round(1)
        tmp = tmp.drop(columns=["cash_share"])
        st.dataframe(tmp, use_container_width=True, hide_index=True)
