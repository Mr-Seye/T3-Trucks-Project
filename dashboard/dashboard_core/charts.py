"""Python script containing functions to create altair charts for the dashboard."""

import altair as alt
import pandas as pd


def revenue_trend_chart(trend: pd.DataFrame, time_grain: str) -> alt.Chart:
    """Creates a chart of the revenue trend by day or hour."""
    if time_grain == "Daily":
        x_field = "day_dt:T"
        x_title = "Day"
        x_tooltip = alt.Tooltip("day_dt:T", title="Day")
    else:
        x_field = "hour_ts:T"
        x_title = "Hour"
        x_tooltip = alt.Tooltip("hour_ts:T", title="Hour")

    return (
        alt.Chart(trend)
        .mark_line()
        .encode(
            x=alt.X(x_field, title=x_title),
            y=alt.Y("revenue:Q", title="Revenue"),
            tooltip=[
                x_tooltip,
                alt.Tooltip("revenue:Q", title="Revenue", format=",.2f"),
                alt.Tooltip("transactions:Q",
                            title="Transactions", format=",.0f"),
                alt.Tooltip("avg_sale:Q", title="Avg ticket", format=",.2f"),
            ],
        )
        .properties(height=260)
    )


def payment_mix_pie(pm: pd.DataFrame) -> alt.Chart:
    """Creates a pie chart of the revenue by payment method."""
    return (
        alt.Chart(pm)
        .mark_arc()
        .encode(
            theta=alt.Theta("count:Q", stack=True),
            color=alt.Color("payment_method:N", title="Method"),
            tooltip=[
                alt.Tooltip("payment_method:N", title="Method"),
                alt.Tooltip("count:Q", title="Transactions"),
            ],
        )
        .properties(height=260)
    )


def truck_bar_chart(truck_perf: pd.DataFrame, field: str, title: str) -> alt.Chart:
    """Creates a bar chart of each truck's sales performance."""
    return (
        alt.Chart(truck_perf)
        .mark_bar()
        .encode(
            x=alt.X("truck_name:N", sort="-y", title="Truck"),
            y=alt.Y(f"{field}:Q", title=title),
            tooltip=[
                alt.Tooltip("truck_name:N", title="Truck"),
                alt.Tooltip("revenue:Q", title="Revenue", format=",.2f"),
                alt.Tooltip("transactions:Q",
                            title="Transactions", format=",.0f"),
                alt.Tooltip("avg_sale:Q", title="Avg ticket", format=",.2f"),
                alt.Tooltip("cash_share:Q", title="Cash share", format=".1%"),
            ],
        )
        .properties(height=300)
    )
