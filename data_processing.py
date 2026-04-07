"""
data_processing.py
-------------------
Responsible for loading raw CSV files, cleaning them, and producing
a single processed CSV ready for analysis.

Processing steps:
  1. Load every raw CSV from data/raw/.
  2. Tag each row with the cryptocurrency name.
  3. Sort by date.
  4. Handle missing / duplicate values.
  5. Add change_percent.
  6. Keep only: date, crypto_name, open_price, high_price, low_price,
      price, volume, change_percent.
  7. Save the cleaned data to data/processed/processed_prices.csv.
"""

import os
import glob
import pandas as pd

# ── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR       = os.path.dirname(__file__)
RAW_DATA_DIR   = os.path.join(BASE_DIR, "data", "raw")
PROC_DATA_DIR  = os.path.join(BASE_DIR, "data", "processed")
PROCESSED_FILE = os.path.join(PROC_DATA_DIR, "processed_prices.csv")


# ── Helper functions ────────────────────────────────────────────────────────

def load_raw_files() -> pd.DataFrame:
    """
    Read all *_raw.csv files from data/raw/ and combine them into one
    DataFrame with an extra 'crypto_name' column derived from the filename.

    Returns
    -------
    pd.DataFrame  – Combined raw data with columns: date, open_price,
                    high_price, low_price, price, volume, crypto_name
    """
    pattern = os.path.join(RAW_DATA_DIR, "*_raw.csv")
    files   = glob.glob(pattern)

    if not files:
        raise FileNotFoundError(
            f"No raw CSV files found in {RAW_DATA_DIR}. "
            "Run data_collection.py first."
        )

    frames = []
    for filepath in files:
        # Extract coin name from filename: "bitcoin_raw.csv" → "Bitcoin"
        basename   = os.path.basename(filepath)                # bitcoin_raw.csv
        coin_name  = basename.replace("_raw.csv", "").title()  # Bitcoin

        df = pd.read_csv(filepath)
        df["crypto_name"] = coin_name
        frames.append(df)
        print(f"  -> Loaded {len(df)} rows from {basename}")

    combined = pd.concat(frames, ignore_index=True)
    return combined


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardise the combined DataFrame.

    Steps
    -----
    1. Ensure 'date' is a proper datetime and then format as YYYY-MM-DD string.
    2. Drop rows where price is missing (NaN).
    3. Remove duplicate (date, crypto_name) entries – keep the first.
    4. Sort by crypto_name then by date.
    5. Add change_percent.
    6. Keep only the required columns.

    Parameters
    ----------
    df : Raw combined DataFrame.

    Returns
    -------
    pd.DataFrame  – Cleaned DataFrame with columns: date, crypto_name,
                    open_price, high_price, low_price, price, volume,
                    change_percent
    """
    print("  -> Cleaning data ...")

    # --- 1. Parse dates -------------------------------------------------------
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop rows where date couldn't be parsed
    before = len(df)
    df = df.dropna(subset=["date"])
    dropped_dates = before - len(df)
    if dropped_dates:
        print(f"    • Dropped {dropped_dates} rows with unparseable dates.")

    # --- 2. Drop rows with missing prices ------------------------------------
    before = len(df)
    df = df.dropna(subset=["price"])
    dropped_prices = before - len(df)
    if dropped_prices:
        print(f"    • Dropped {dropped_prices} rows with missing prices.")

    # --- 3. Remove duplicates ------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["date", "crypto_name"], keep="first")
    dropped_dups = before - len(df)
    if dropped_dups:
        print(f"    • Removed {dropped_dups} duplicate rows.")

    # --- 4. Sort -------------------------------------------------------------
    df = df.sort_values(by=["crypto_name", "date"]).reset_index(drop=True)

    # Format date back to string for CSV readability
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # --- 5. Add change_percent ----------------------------------------------
    df["change_percent"] = df.groupby("crypto_name")["price"].pct_change() * 100

    # --- 6. Keep required columns -------------------------------------------
    df = df[[
        "date",
        "crypto_name",
        "open_price",
        "high_price",
        "low_price",
        "price",
        "volume",
        "change_percent",
    ]]

    print(f"  [OK] Cleaned data: {len(df)} rows across "
          f"{df['crypto_name'].nunique()} cryptocurrencies.")
    return df


def save_processed_data(df: pd.DataFrame) -> str:
    """
    Save the cleaned DataFrame to data/processed/processed_prices.csv.

    Returns
    -------
    str – Path to the saved file.
    """
    os.makedirs(PROC_DATA_DIR, exist_ok=True)
    df.to_csv(PROCESSED_FILE, index=False)
    print(f"  [OK] Saved processed data -> {PROCESSED_FILE}")
    return PROCESSED_FILE


# ── Main entry point for this module ────────────────────────────────────────

def process_all() -> pd.DataFrame:
    """
    Full processing pipeline: load → clean → save.

    Returns
    -------
    pd.DataFrame – The cleaned, processed data.
    """
    raw_df       = load_raw_files()
    cleaned_df   = clean_data(raw_df)
    save_processed_data(cleaned_df)
    return cleaned_df


# ── Stand-alone execution ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Data Processing (standalone) ===")
    result = process_all()
    print(result.head(10))
