"""Generates a dictionary containing the HTML daily report."""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import boto3
import awswrangler as wr
import pandas as pd


@dataclass(frozen=True)
class Config:
    region: str
    database: str
    t_transactions: str
    t_truck: str
    t_payment_method: str
    s3_output: str


def load_config() -> Config:
    """Creates a configuration object to be used later."""
    region = os.environ.get("AWS_REGION", "eu-west-2")
    database = os.environ.get("ATHENA_DATABASE", "")
    t_transactions = os.environ.get("ATHENA_TX_TABLE", "transaction")
    t_truck = os.environ.get("ATHENA_TRUCK_TABLE", "truck")
    t_payment_method = os.environ.get("ATHENA_PM_TABLE", "payment_method")
    s3_output = os.environ.get("ATHENA_S3_OUTPUT", "")

    if not database:
        raise RuntimeError("Missing ATHENA_DATABASE")
    if not s3_output:
        raise RuntimeError(
            "Missing ATHENA_S3_OUTPUT (e.g. s3://<bucket>/athena-results/)")

    return Config(
        region=region,
        database=database,
        t_transactions=t_transactions,
        t_truck=t_truck,
        t_payment_method=t_payment_method,
        s3_output=s3_output,
    )


def previous_day_utc() -> date:
    """Gets the previous day in UTC."""
    now_utc = datetime.now(timezone.utc).date()
    return now_utc - timedelta(days=1)


def parse_report_date(event: dict) -> date:
    """
    If event contains "report_date" in YYYY-MM-DD format, use it.
    Otherwise default to previous day (UTC).
    """
    raw = (event or {}).get("report_date")
    if raw:
        return date.fromisoformat(str(raw))
    return previous_day_utc()


def athena_read(sql: str, cfg: Config, session: boto3.Session) -> pd.DataFrame:
    """Gets specified query result from Athena data lake."""
    return wr.athena.read_sql_query(
        sql=sql,
        database=cfg.database,
        s3_output=cfg.s3_output,
        boto3_session=session,
        ctas_approach=False,
    )


def gbp_from_pence(pence: float) -> float:
    """Converts pence to pounds."""
    return round((pence or 0.0) / 100.0, 2)


def fmt_gbp(value: float) -> str:
    """Formats number into currency standard."""
    return f"£{value:,.2f}"


def fmt_int(value: int) -> str:
    """Adds comma separators to numbers."""
    return f"{value:,}"


def build_metrics(cfg: Config, report_day: date) -> dict:
    """Collects several different metrics to be used in the report."""
    session = boto3.Session(region_name=cfg.region)

    y = report_day.strftime("%Y")
    m = report_day.strftime("%m")
    d = report_day.strftime("%d")

    where_day = f"""
      CAST(t.year AS VARCHAR) = '{y}'
      AND LPAD(CAST(t.month AS VARCHAR), 2, '0') = '{m}'
      AND LPAD(CAST(t.day AS VARCHAR), 2, '0') = '{d}'
    """

    overall_sql = f"""
    SELECT
      COUNT(DISTINCT t.transaction_id) AS n_transactions,
      SUM(CAST(t.total AS DOUBLE))     AS total_pence,
      AVG(CAST(t.total AS DOUBLE))     AS avg_customer_spend_pence
    FROM "{cfg.database}"."{cfg.t_transactions}" t
    WHERE {where_day}
      AND CAST(t.total AS DOUBLE) IS NOT NULL
      AND CAST(t.total AS DOUBLE) > 0
    """

    overall_df = athena_read(overall_sql, cfg, session)
    n_tx = int((overall_df.loc[0, "n_transactions"]
               if not overall_df.empty else 0) or 0)
    total_pence = float(
        (overall_df.loc[0, "total_pence"] if not overall_df.empty else 0.0) or 0.0)
    avg_customer_spend_pence = float(
        (overall_df.loc[0, "avg_customer_spend_pence"]
         if not overall_df.empty else 0.0) or 0.0
    )

    by_truck_sql = f"""
    SELECT
      COALESCE(tr.truck_name, 'unknown') AS truck_name,
      COUNT(DISTINCT t.transaction_id)   AS n_transactions,
      SUM(CAST(t.total AS DOUBLE))       AS total_pence,
      AVG(CAST(t.total AS DOUBLE))       AS avg_customer_spend_pence
    FROM "{cfg.database}"."{cfg.t_transactions}" t
    LEFT JOIN "{cfg.database}"."{cfg.t_truck}" tr
      ON t.truck_id = tr.truck_id
    WHERE {where_day}
      AND CAST(t.total AS DOUBLE) IS NOT NULL
      AND CAST(t.total AS DOUBLE) > 0
    GROUP BY COALESCE(tr.truck_name, 'unknown')
    """

    by_truck_df = athena_read(by_truck_sql, cfg, session)
    if by_truck_df.empty:
        by_truck_df = pd.DataFrame(
            columns=["truck_name", "n_transactions",
                     "total_pence", "avg_customer_spend_pence"]
        )

    by_truck_df["truck_name"] = by_truck_df["truck_name"].astype(str)
    by_truck_df["n_transactions"] = (
        pd.to_numeric(by_truck_df["n_transactions"],
                      errors="coerce").fillna(0).astype(int)
    )
    by_truck_df["total_pence"] = (
        pd.to_numeric(by_truck_df["total_pence"],
                      errors="coerce").fillna(0.0).astype(float)
    )
    by_truck_df["avg_customer_spend_pence"] = (
        pd.to_numeric(by_truck_df["avg_customer_spend_pence"], errors="coerce").fillna(
            0.0).astype(float)
    )

    by_truck_df["total_gbp"] = (by_truck_df["total_pence"] / 100.0).round(2)
    by_truck_df["avg_customer_spend_gbp"] = (
        by_truck_df["avg_customer_spend_pence"] / 100.0).round(2)
    by_truck_df = by_truck_df.sort_values(
        ["total_gbp", "n_transactions"], ascending=[False, False])

    pm_sql = f"""
    SELECT
      COALESCE(LOWER(TRIM(pm.payment_method)), 'unknown') AS payment_method,
      COUNT(DISTINCT t.transaction_id)                   AS n_transactions
    FROM "{cfg.database}"."{cfg.t_transactions}" t
    LEFT JOIN "{cfg.database}"."{cfg.t_payment_method}" pm
      ON t.payment_method_id = pm.payment_method_id
    WHERE {where_day}
      AND CAST(t.total AS DOUBLE) IS NOT NULL
      AND CAST(t.total AS DOUBLE) > 0
    GROUP BY COALESCE(LOWER(TRIM(pm.payment_method)), 'unknown')
    """

    pm_df = athena_read(pm_sql, cfg, session)
    pm_counts: dict[str, int] = {}
    if not pm_df.empty:
        pm_df["payment_method"] = pm_df["payment_method"].astype(str)
        pm_df["n_transactions"] = pd.to_numeric(
            pm_df["n_transactions"], errors="coerce").fillna(0).astype(int)
        pm_counts = {r["payment_method"]: int(
            r["n_transactions"]) for _, r in pm_df.iterrows()}

    cash_n = pm_counts.get("cash", 0)
    card_n = pm_counts.get("card", 0)
    denom = max(n_tx, 1)
    cash_share = cash_n / denom
    card_share = card_n / denom

    # Highlights
    top_by_rev = None
    bottom_by_rev = None
    top_by_tx = None
    if not by_truck_df.empty:
        top_by_rev = by_truck_df.iloc[0]
        bottom_by_rev = by_truck_df.iloc[-1]
        top_by_tx = by_truck_df.sort_values(
            "n_transactions", ascending=False).iloc[0]

    generated_at_utc = datetime.now(timezone.utc).replace(
        microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "report_date": report_day.isoformat(),
        "generated_at": generated_at_utc,
        "overall": {
            "total_transaction_value_gbp": gbp_from_pence(total_pence),
            "n_transactions": n_tx,
            "avg_customer_spend_gbp": gbp_from_pence(avg_customer_spend_pence),
        },
        "by_truck_df": by_truck_df,
        "payment_mix": {
            "cash_n": cash_n,
            "card_n": card_n,
            "cash_share": cash_share,
            "card_share": card_share,
        },
        "highlights": {
            "top_truck_by_revenue": None if top_by_rev is None else {
                "truck_name": str(top_by_rev["truck_name"]),
                "total_gbp": float(top_by_rev["total_gbp"]),
                "n_transactions": int(top_by_rev["n_transactions"]),
            },
            "lowest_truck_by_revenue": None if bottom_by_rev is None else {
                "truck_name": str(bottom_by_rev["truck_name"]),
                "total_gbp": float(bottom_by_rev["total_gbp"]),
                "n_transactions": int(bottom_by_rev["n_transactions"]),
            },
            "top_truck_by_transactions": None if top_by_tx is None else {
                "truck_name": str(top_by_tx["truck_name"]),
                "total_gbp": float(top_by_tx["total_gbp"]),
                "n_transactions": int(top_by_tx["n_transactions"]),
            },
        },
    }


def df_to_html_table(df: pd.DataFrame) -> str:
    """Converts dataframes from the metrics into HTML tables."""
    if df.empty:
        return "<p><em>No transactions recorded for this date.</em></p>"

    view = df[["truck_name", "n_transactions",
               "total_gbp", "avg_customer_spend_gbp"]].copy()
    view.rename(
        columns={
            "truck_name": "Truck",
            "n_transactions": "Transactions",
            "total_gbp": "Total (GBP)",
            "avg_customer_spend_gbp": "Avg customer spend (GBP)",
        },
        inplace=True,
    )

    view["Total (GBP)"] = view["Total (GBP)"].map(
        lambda x: f"£{float(x):,.2f}")
    view["Avg customer spend (GBP)"] = view["Avg customer spend (GBP)"].map(
        lambda x: f"£{float(x):,.2f}")
    view["Transactions"] = view["Transactions"].map(lambda x: f"{int(x):,}")

    headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in view.columns)
    rows_html = []
    for _, row in view.iterrows():
        cells = "".join(
            f"<td>{html.escape(str(v))}</td>" for v in row.tolist())
        rows_html.append(f"<tr>{cells}</tr>")

    return f"""
    <table>
      <thead><tr>{headers}</tr></thead>
      <tbody>
        {''.join(rows_html)}
      </tbody>
    </table>
    """


def render_html_report(metrics: dict) -> str:
    """Generates HTML string for the report."""
    report_date = metrics["report_date"]
    generated_at = metrics["generated_at"]

    total_gbp = metrics["overall"]["total_transaction_value_gbp"]
    n_tx = metrics["overall"]["n_transactions"]
    avg_gbp = metrics["overall"]["avg_customer_spend_gbp"]

    cash_n = metrics["payment_mix"]["cash_n"]
    card_n = metrics["payment_mix"]["card_n"]
    cash_share = metrics["payment_mix"]["cash_share"]
    card_share = metrics["payment_mix"]["card_share"]

    highlights = metrics["highlights"]

    def highlight_line(label: str, item: dict | None) -> str:
        if not item:
            return f"<li><b>{html.escape(label)}:</b> n/a</li>"
        return (
            f"<li><b>{html.escape(label)}:</b> "
            f"{html.escape(item['truck_name'])} "
            f"({fmt_gbp(item['total_gbp'])}, {fmt_int(item['n_transactions'])} tx)</li>"
        )

    by_truck_table = df_to_html_table(metrics["by_truck_df"])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>T3 Daily Report — {html.escape(report_date)}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      margin: 24px;
      color: #111;
      background: #fff;
    }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
    .meta {{ color: #444; margin-bottom: 1.25rem; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin: 16px 0 18px;
    }}
    .card {{
      border: 1px solid #e6e6e6;
      border-radius: 12px;
      padding: 14px 14px;
    }}
    .label {{ font-size: 0.9rem; color: #555; }}
    .value {{ font-size: 1.35rem; font-weight: 700; margin-top: 6px; }}
    hr {{ border: none; border-top: 1px solid #eaeaea; margin: 18px 0; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    th, td {{
      padding: 10px 10px;
      border-bottom: 1px solid #eee;
      text-align: left;
      font-size: 0.95rem;
    }}
    th {{ background: #fafafa; font-weight: 700; }}
    .small {{ color: #555; font-size: 0.95rem; }}
    ul {{ margin-top: 8px; }}
    @media (max-width: 820px) {{
      .cards {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>T3 Daily Performance Report — {html.escape(report_date)}</h1>
    <div class="meta">
      Generated at {html.escape(generated_at)} (UTC)<br/>
      <span class="small">All monetary values reported in GBP.</span>
    </div>

    <div class="cards">
      <div class="card">
        <div class="label">Total transaction value (all trucks)</div>
        <div class="value">{fmt_gbp(total_gbp)}</div>
      </div>
      <div class="card">
        <div class="label">Total transactions</div>
        <div class="value">{fmt_int(n_tx)}</div>
      </div>
      <div class="card">
        <div class="label">Avg customer spend</div>
        <div class="value">{fmt_gbp(avg_gbp)}</div>
      </div>
    </div>

    <hr/>

    <h2>By-truck performance</h2>
    <p class="small">Total transaction value and number of transactions per truck.</p>
    {by_truck_table}

    <hr/>

    <h2>Payment mix</h2>
    <p class="small">
      Cash: {fmt_int(cash_n)} ({cash_share*100:.1f}%) &nbsp;|&nbsp;
      Card: {fmt_int(card_n)} ({card_share*100:.1f}%)
    </p>

    <hr/>

    <h2>Highlights</h2>
    <ul>
      {highlight_line("Top truck by revenue", highlights.get("top_truck_by_revenue"))}
      {highlight_line("Lowest truck by revenue", highlights.get("lowest_truck_by_revenue"))}
      {highlight_line("Top truck by transactions", highlights.get("top_truck_by_transactions"))}
    </ul>
  </div>
</body>
</html>
"""


def lambda_handler(event, context):
    """AWS Lambda entrypoint."""
    cfg = load_config()
    report_day = parse_report_date(event or {})

    metrics = build_metrics(cfg, report_day)
    html_str = render_html_report(metrics)

    return {
        "report_date": metrics["report_date"],
        "generated_at": metrics["generated_at"],
        "html": html_str,
    }
