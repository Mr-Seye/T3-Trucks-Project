"""Script that queries the Athena database and returns the results"""
from datetime import date
import pandas as pd
import streamlit as st
import awswrangler as wr

from .clients import get_boto3_session
from .config import AppConfig


@st.cache_data(ttl=900, show_spinner=False)
def load_transactions_joined(cfg: AppConfig, start_dt: date, end_dt: date) -> pd.DataFrame:
    """
    Query to return date partitioned transaction data.
    Uses partition columns year/month/day/hour to separate data.
    """
    if not cfg.athena_s3_output:
        raise RuntimeError(
            "ATHENA_S3_OUTPUT is not set. Set it to an S3 URI for Athena query results, "
            "e.g. s3://<bucket>/athena-results/."
        )

    session = get_boto3_session(cfg.aws_region)

    sql = f"""
    SELECT
      t.transaction_id,
      t.truck_id,
      tr.truck_name,
      t.payment_method_id,
      pm.payment_method,
      CAST(t.total AS DOUBLE) AS total,

      date_parse(concat(t.year, '-', t.month, '-', t.day), '%Y-%m-%d') AS day_dt,
      date_parse(
        concat(t.year, '-', t.month, '-', t.day, ' ', t.hour, ':00:00'),
        '%Y-%m-%d %H:%i:%s'
      ) AS hour_ts

    FROM "{cfg.athena_database}"."{cfg.transactions_table}" t
    LEFT JOIN "{cfg.athena_database}"."{cfg.truck_table}" tr
      ON t.truck_id = tr.truck_id
    LEFT JOIN "{cfg.athena_database}"."{cfg.payment_method_table}" pm
      ON t.payment_method_id = pm.payment_method_id

    WHERE CAST(t.total AS DOUBLE) IS NOT NULL
      AND CAST(t.total AS DOUBLE) > 0
      AND date_parse(concat(t.year, '-', t.month, '-', t.day), '%Y-%m-%d')
          BETWEEN DATE '{start_dt.isoformat()}' AND DATE '{end_dt.isoformat()}'
    """

    return wr.athena.read_sql_query(
        sql=sql,
        database=cfg.athena_database,
        s3_output=cfg.athena_s3_output,
        boto3_session=session,
        ctas_approach=False,
    )
