import pandas as pd


def validate_required_columns(df: pd.DataFrame, required_cols: list):
    """
    Ensure required columns exist.
    """
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def clean_numeric_columns(df: pd.DataFrame, columns: list):
    """
    Convert columns to numeric safely.
    """
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=columns)

    return df


def remove_invalid_rows(df: pd.DataFrame):
    """
    Remove rows with invalid values.
    """
    df = df.replace([float("inf"), -float("inf")], pd.NA)
    df = df.dropna()

    return df