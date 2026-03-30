"""Load functions for the pipeline"""
from pathlib import Path
from os import environ
import pandas as pd
import boto3


def write_unpartitioned_parquet(df: pd.DataFrame, out_path: Path) -> None:
    """Creates the un-partitioned parquet metadata"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, engine="pyarrow")


def write_time_partitioned_transactions(
    transactions: pd.DataFrame,
    root_dir: Path,
    timestamp_col: str = "at",
    filename: str = "transaction.parquet",
) -> None:
    """Creates the time-partitioned transactions"""
    root_dir.mkdir(parents=True, exist_ok=True)

    df = transactions.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    df = df.dropna(subset=[timestamp_col])

    df["year"] = df[timestamp_col].dt.year.astype("Int64").astype(str)
    df["month"] = df[timestamp_col].dt.month.map(lambda x: f"{int(x):02d}")
    df["day"] = df[timestamp_col].dt.day.map(lambda x: f"{int(x):02d}")
    df["hour"] = df[timestamp_col].dt.hour.map(lambda x: f"{int(x):02d}")

    for (y, m, d, h), chunk in df.groupby(["year", "month", "day", "hour"], sort=False):
        out_dir = root_dir / f"year={y}" / \
            f"month={m}" / f"day={d}" / f"hour={h}"
        out_dir.mkdir(parents=True, exist_ok=True)

        chunk_out = chunk.drop(columns=["year", "month", "day", "hour"])
        chunk_out.to_parquet(out_dir / filename, index=False, engine="pyarrow")


def write_data_lake_structure(
    dim_truck: pd.DataFrame,
    dim_payment_method: pd.DataFrame,
    transactions: pd.DataFrame,
    base_dir: str = "input",
) -> Path:
    """Constructs the data lake file structure to be uploaded to the S3"""
    base = Path(base_dir)

    write_unpartitioned_parquet(dim_truck, base / "truck" / "truck.parquet")
    write_unpartitioned_parquet(
        dim_payment_method, base / "payment_method" / "payment_method.parquet")
    write_time_partitioned_transactions(
        transactions, base / "transaction", timestamp_col="at")

    return base


def upload_directory_to_s3(local_dir: Path, bucket: str, prefix: str = "input") -> None:
    """
    Uploads local_dir to s3://bucket/prefix/...
    """
    s3 = boto3.client("s3", region_name=environ.get("AWS_REGION"))

    for file in local_dir.rglob("*"):
        if file.is_file():
            key = f"{prefix}/{file.relative_to(local_dir).as_posix()}"
            s3.upload_file(str(file), bucket, key)
            print(f"Uploaded: s3://{bucket}/{key}")
