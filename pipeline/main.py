from dotenv import load_dotenv
from os import environ

from extract import get_db_connection, fetch_transactions_joined
from transform import clean_transactions, build_truck_metadata, build_payment_method_metadata
from load import write_data_lake_structure, upload_directory_to_s3


def main() -> None:
    load_dotenv()

    # Extract
    conn = get_db_connection()
    raw = fetch_transactions_joined(conn)

    # Transform
    transactions = clean_transactions(raw)
    dim_truck = build_truck_metadata(transactions)
    dim_payment_method = build_payment_method_metadata(transactions)

    # Load (local lake)
    output_dir = write_data_lake_structure(
        dim_truck, dim_payment_method, transactions, base_dir="input")

    # Load (S3)
    bucket = environ["S3_BUCKET"]
    upload_directory_to_s3(output_dir, bucket=bucket, prefix="input")


if __name__ == "__main__":
    main()
