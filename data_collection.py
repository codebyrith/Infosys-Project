""" this is the first code for execution
data_collection.py
-------------------
Responsible for fetching historical cryptocurrency price data
from the CoinGecko public API and saving it as CSV files in data/raw/.

Supported coins: Bitcoin, Ethereum, Binance Coin.
API used: CoinGecko (free, no API key required).
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime

# ── Configuration ───────────────────────────────────────────────────────────

# CoinGecko API endpoint for historical market-chart data
BASE_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

# Coins we want to track  (CoinGecko id → friendly name)
COINS = {
    "bitcoin":      "Bitcoin",
    "ethereum":     "Ethereum",
    "binancecoin":  "BinanceCoin",
}

# How many days of history to fetch (max 365 for daily granularity on free tier)
DAYS = 365

# Target currency for prices
VS_CURRENCY = "usd"

# Directory where raw CSV files will be stored
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")


# ── Helper functions ────────────────────────────────────────────────────────

def fetch_price_data(coin_id: str, days: int = DAYS,
                     vs_currency: str = VS_CURRENCY) -> pd.DataFrame:
    """
    Fetch daily historical prices for a single cryptocurrency from CoinGecko.

    Parameters
    ----------
    coin_id     : CoinGecko coin identifier (e.g. "bitcoin").
    days        : Number of past days to retrieve.
    vs_currency : Quote currency (default "usd").

    Returns
    -------
    pd.DataFrame with columns: date, open_price, high_price,
    low_price, price, volume
    """
    url = BASE_URL.format(coin_id=coin_id)
    params = {
        "vs_currency": vs_currency,
        "days":        days,
        "interval":    "daily",       # one data-point per day
    }

    print(f"  -> Fetching {days}-day price history for '{coin_id}' ...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()       # raise an error on bad HTTP status

    data = response.json()

    # CoinGecko returns prices and total_volumes as [[timestamp_ms, value], …]
    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])

    # Convert to a DataFrame
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    vol_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
    df = df.merge(vol_df, on="timestamp", how="left")

    # Convert millisecond timestamps to readable dates (YYYY-MM-DD)
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")

    # Derive OHLC from daily close price (CoinGecko market_chart provides one
    # daily price point in this free tier endpoint)
    df["open_price"] = df["price"]
    df["high_price"] = df["price"]
    df["low_price"] = df["price"]

    # Keep only the columns we need
    df = df[["date", "open_price", "high_price", "low_price", "price", "volume"]]

    return df


def save_raw_data(df: pd.DataFrame, coin_name: str) -> str:
    """
    Save a DataFrame of raw price data to a CSV file in data/raw/.

    Parameters
    ----------
    df        : DataFrame with columns [date, open_price, high_price,
                low_price, price, volume].
    coin_name : Friendly name used in the filename (e.g. "Bitcoin").

    Returns
    -------
    The full path of the saved CSV file.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    filename = f"{coin_name.lower()}_raw.csv"
    filepath = os.path.join(RAW_DATA_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"  [OK] Saved raw data -> {filepath}")
    return filepath


# ── Main entry point for this module ────────────────────────────────────────

def collect_all() -> dict:
    """
    Fetch and save raw price data for every coin in the COINS dictionary.

    Returns
    -------
    dict  –  {coin_name: filepath} for each coin successfully collected.
    """
    saved_files = {}

    for coin_id, coin_name in COINS.items():
        try:
            df = fetch_price_data(coin_id)
            path = save_raw_data(df, coin_name)
            saved_files[coin_name] = path
        except requests.exceptions.RequestException as e:
            print(f"  [FAIL] Failed to fetch data for {coin_name}: {e}")

        # Respect CoinGecko rate-limits (≈10-30 req/min on free tier)
        time.sleep(5)

    return saved_files


# ── Run stand-alone for quick testing ───────────────────────────────────────

if __name__ == "__main__":
    print("=== Data Collection (standalone) ===")
    files = collect_all()
    print(f"\nCollected {len(files)} file(s):", list(files.keys()))
