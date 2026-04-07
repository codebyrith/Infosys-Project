"""
Risk Checker Module
Classifies each cryptocurrency by risk level and trend direction,
then stores results in a SQLite database.
"""

import os
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RETURNS_CSV = os.path.join(BASE_DIR, "data", "processed", "returns_summary.csv")
ETA_CSV = os.path.join(BASE_DIR, "data", "processed", "eta_summary.csv")
DB_DIR = os.path.join(BASE_DIR, "data", "database")
DB_PATH = os.path.join(DB_DIR, "risk_analysis.db")


# ── Helper functions ─────────────────────────────────────────────────
def load_and_merge() -> pd.DataFrame:
    """Load both CSVs and merge on crypto_name."""
    returns_df = pd.read_csv(RETURNS_CSV)
    eta_df = pd.read_csv(ETA_CSV)
    merged = pd.merge(returns_df, eta_df, on="crypto_name", suffixes=("", "_eta"))
    return merged


def classify_risk(row: dict) -> dict:
    """Determine risk_level and trend for a single cryptocurrency."""
    std = row["std_daily_return"]
    if std > 0.05:
        risk_level = "HIGH"
    elif std >= 0.02:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    trend = "UPWARD" if row["adjusted_eta_pct"] > 0 else "DOWNWARD"

    return {
        "crypto_name": row["crypto_name"],
        "risk_level": risk_level,
        "trend": trend,
        "adjusted_eta": row["adjusted_eta_pct"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def classify_all(merged_df: pd.DataFrame) -> list[dict]:
    """Run risk classification in parallel using ThreadPoolExecutor."""
    rows = merged_df.to_dict(orient="records")
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(classify_risk, rows))
    return results


# ── Database ─────────────────────────────────────────────────────────
def save_to_sqlite(results: list[dict]) -> None:
    """Save classification results to SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_results (
            crypto_name TEXT,
            risk_level  TEXT,
            trend       TEXT,
            adjusted_eta REAL,
            timestamp   TEXT
        )
        """
    )

    cursor.executemany(
        """
        INSERT INTO risk_results (crypto_name, risk_level, trend, adjusted_eta, timestamp)
        VALUES (:crypto_name, :risk_level, :trend, :adjusted_eta, :timestamp)
        """,
        results,
    )

    conn.commit()
    conn.close()
    print(f"Results saved to {DB_PATH}")


# ── Summary ──────────────────────────────────────────────────────────
def print_summary(results: list[dict]) -> None:
    """Print a readable summary table."""
    print("\n" + "=" * 65)
    print(f"{'Crypto':<15} {'Risk':<10} {'Trend':<12} {'Adj. ETA %':>10}")
    print("-" * 65)
    for r in results:
        print(
            f"{r['crypto_name']:<15} {r['risk_level']:<10} {r['trend']:<12} "
            f"{r['adjusted_eta']:>10.4f}"
        )
    print("=" * 65 + "\n")


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading and merging data...")
    merged_df = load_and_merge()

    print("Classifying risk in parallel...")
    results = classify_all(merged_df)

    print_summary(results)
    save_to_sqlite(results)


if __name__ == "__main__":
    main()
