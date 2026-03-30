"""Script that fetches environment variables from a .env file"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Defines a class that holds environment variables."""
    athena_database: str
    transactions_table: str
    truck_table: str
    payment_method_table: str
    athena_s3_output: str
    aws_region: str


def load_config() -> AppConfig:
    """Returns an AppConfig object containing environment variables from a .env file."""
    return AppConfig(
        athena_database=os.environ.get("ATHENA_DATABASE", ""),
        transactions_table=os.environ.get(
            "ATHENA_TABLE_TRANSACTIONS", "transaction"),
        truck_table=os.environ.get("ATHENA_TABLE_TRUCK", "truck"),
        payment_method_table=os.environ.get(
            "ATHENA_TABLE_PAYMENT_METHOD", "payment_method"),
        athena_s3_output=os.environ.get("ATHENA_S3_OUTPUT", ""),
        aws_region=os.environ.get("AWS_REGION", "eu-west-2"),
    )
