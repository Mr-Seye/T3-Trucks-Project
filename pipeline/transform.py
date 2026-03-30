"""Transform function for the pipeline"""

import pandas as pd


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean transaction dataset: types, invalid rows, duplicates."""
    df = df.copy()

    # Strip text
    text_cols = ["payment_method", "truck_name", "truck_description"]
    for c in text_cols:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip()

    # Total handling
    df["total"] = df["total"].astype("string").str.strip()
    df.loc[df["total"].str.upper().eq("VOID"), "total"] = pd.NA
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df = df[df["total"].notna() & (df["total"] > 0)]

    # Timestamp
    df["at"] = pd.to_datetime(df["at"], errors="coerce")
    df = df[df["at"].notna()]

    # Domain checks
    if "has_card_reader" in df.columns:
        df["has_card_reader"] = pd.to_numeric(
            df["has_card_reader"], errors="coerce")
        df = df[df["has_card_reader"].isin([0, 1])]

    if "fsa_rating" in df.columns:
        df["fsa_rating"] = pd.to_numeric(df["fsa_rating"], errors="coerce")
        df = df[df["fsa_rating"].between(0, 5, inclusive="both")]

    if "payment_method" in df.columns:
        df["payment_method"] = df["payment_method"].str.lower()
        df = df[df["payment_method"].isin(["cash", "card"])]

    # Remove Duplicates
    if "transaction_id" in df.columns:
        df = df.drop_duplicates(subset=["transaction_id"], keep="first")

    # Type cast ids and ints
    int_cols = ["truck_id", "payment_method_id",
                "transaction_id", "fsa_rating", "has_card_reader"]
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    df["total"] = df["total"].astype("float64")

    if "has_card_reader" in df.columns:
        df["has_card_reader"] = df["has_card_reader"].astype("boolean")

    preferred_order = [
        "transaction_id", "at", "truck_name", "payment_method", "total",
        "truck_id", "payment_method_id", "fsa_rating", "has_card_reader", "truck_description"
    ]
    df = df[[c for c in preferred_order if c in df.columns] +
            [c for c in df.columns if c not in preferred_order]]

    return df


def build_truck_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Create DIM_Truck metadata table from cleaned transactions."""
    truck_cols = ["truck_id", "truck_name",
                  "truck_description", "has_card_reader", "fsa_rating"]
    meta = df[truck_cols].drop_duplicates(subset=["truck_id"]).copy()

    meta["truck_id"] = pd.to_numeric(
        meta["truck_id"], errors="coerce").astype("Int64")
    meta["has_card_reader"] = pd.to_numeric(
        meta["has_card_reader"], errors="coerce").astype("Int64").astype("boolean")
    meta["fsa_rating"] = pd.to_numeric(
        meta["fsa_rating"], errors="coerce").astype("Int64")

    meta["truck_name"] = meta["truck_name"].astype("string").str.strip()
    meta["truck_description"] = meta["truck_description"].astype(
        "string").str.strip()

    meta = meta[meta["truck_id"].notna()]
    return meta


def build_payment_method_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Create DIM_Payment_Method  metadata table from cleaned transactions."""
    pm_cols = ["payment_method_id", "payment_method"]
    meta = df[pm_cols].drop_duplicates(subset=["payment_method_id"]).copy()

    meta["payment_method_id"] = pd.to_numeric(
        meta["payment_method_id"], errors="coerce").astype("Int64")
    meta["payment_method"] = meta["payment_method"].astype(
        "string").str.strip().str.lower()

    meta = meta[meta["payment_method_id"].notna()]
    return meta
