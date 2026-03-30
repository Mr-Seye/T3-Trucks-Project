"""Extract functions for pipeline"""

from os import environ
from pymysql import connect, cursors
import pandas as pd
from dotenv import load_dotenv


def get_db_connection():
    """Create a connection to the RDS database."""
    return connect(
        database=environ["DB_NAME"],
        host=environ["DB_HOST"],
        port=int(environ["DB_PORT"]),
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        cursorclass=cursors.DictCursor,
    )


def fetch_transactions_joined(conn) -> pd.DataFrame:
    """Extract joined transaction dataset from fact and dimensions."""
    query = """
        SELECT
            ta.transaction_id,
            ta.truck_id,
            tu.truck_name,
            tu.truck_description,
            tu.has_card_reader,
            tu.fsa_rating,
            ta.payment_method_id,
            pm.payment_method,
            ta.total,
            ta.at
        FROM FACT_Transaction AS ta
        INNER JOIN DIM_Payment_Method AS pm
            ON pm.payment_method_id = ta.payment_method_id
        INNER JOIN DIM_Truck AS tu
            ON tu.truck_id = ta.truck_id
        WHERE ta.total IS NOT NULL
            AND ta.total > 0
            AND ta.at >= NOW() - INTERVAL 3 HOUR
        ;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Left in the case I need to delete the S3 for any reason
    load_dotenv()
    conn = get_db_connection()
    df = fetch_transactions_joined(conn)
    print(df)
