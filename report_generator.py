"""
Report Generator Module
Produces a final CSV and text report combining risk analysis
results from SQLite with the top investment mixes from CSV.
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "risk_analysis.db")
MIX_CSV = os.path.join(BASE_DIR, "data", "processed", "investment_mix_results.csv")
REPORT_DIR = os.path.join(BASE_DIR, "data", "reports")
REPORT_CSV = os.path.join(REPORT_DIR, "final_report.csv")
REPORT_TXT = os.path.join(REPORT_DIR, "final_report.txt")


# ── Data loading ─────────────────────────────────────────────────────
def load_risk_results() -> pd.DataFrame:
    """Read risk_results table from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM risk_results", conn)
    conn.close()
    return df


def load_investment_mixes(top_n: int = 5) -> pd.DataFrame:
    """Load investment mix CSV and return the top N rows."""
    df = pd.read_csv(MIX_CSV)
    return df.head(top_n)


# ── Report builders ──────────────────────────────────────────────────
def build_csv_report(risk_df: pd.DataFrame, mix_df: pd.DataFrame) -> pd.DataFrame:
    """Combine risk and mix data into a single CSV-friendly DataFrame."""
    # Risk section – one row per crypto
    risk_section = risk_df[["crypto_name", "risk_level", "trend", "adjusted_eta"]].copy()
    risk_section.insert(0, "section", "Risk Analysis")

    # Mix section – one row per ranked mix
    mix_section = mix_df.copy()
    mix_section.insert(0, "section", "Investment Mix")

    # Combine both sections into one report DataFrame
    report_df = pd.concat([risk_section, mix_section], ignore_index=True)
    return report_df


def build_text_report(risk_df: pd.DataFrame, mix_df: pd.DataFrame) -> str:
    """Build a human-readable plain-text report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    width = 65
    lines: list[str] = []

    lines.append("=" * width)
    lines.append("CRYPTO INVESTMENT MANAGER – FINAL REPORT")
    lines.append(f"Generated: {now}")
    lines.append("=" * width)

    # ── Risk Analysis ────────────────────────────────────────────
    lines.append("")
    lines.append("SECTION 1: RISK ANALYSIS")
    lines.append("-" * width)
    lines.append(f"{'Crypto':<15} {'Risk':<10} {'Trend':<12} {'Adj. ETA %':>10}")
    lines.append("-" * width)
    for _, r in risk_df.iterrows():
        lines.append(
            f"{r['crypto_name']:<15} {r['risk_level']:<10} {r['trend']:<12} "
            f"{r['adjusted_eta']:>10.4f}"
        )
    lines.append("")

    # ── Investment Mixes ─────────────────────────────────────────
    lines.append("SECTION 2: TOP 5 INVESTMENT MIXES")
    lines.append("-" * width)
    lines.append(
        f"{'Rank':<6} {'BNB %':>6} {'BTC %':>6} {'ETH %':>6} "
        f"{'W.Return':>10} {'W.ETA':>8} {'Score':>8}"
    )
    lines.append("-" * width)
    for _, m in mix_df.iterrows():
        lines.append(
            f"{int(m['rank']):<6} {m['Binancecoin_pct']:>6.0f} "
            f"{m['Bitcoin_pct']:>6.0f} {m['Ethereum_pct']:>6.0f} "
            f"{m['weighted_return']:>10.6f} {m['weighted_eta']:>8.4f} "
            f"{m['score']:>8.4f}"
        )
    lines.append("")
    lines.append("=" * width)
    lines.append("END OF REPORT")
    lines.append("=" * width)

    return "\n".join(lines)


# ── Save helpers ─────────────────────────────────────────────────────
def save_csv(report_df: pd.DataFrame) -> None:
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_df.to_csv(REPORT_CSV, index=False)
    print(f"CSV report saved to {REPORT_CSV}")


def save_text(text: str) -> None:
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Text report saved to {REPORT_TXT}")


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading risk results from database...")
    risk_df = load_risk_results()

    print("Loading investment mixes...")
    mix_df = load_investment_mixes(top_n=5)

    # Build and save CSV report
    report_df = build_csv_report(risk_df, mix_df)
    save_csv(report_df)

    # Build and save text report
    text_report = build_text_report(risk_df, mix_df)
    save_text(text_report)

    # Print the text report to console as well
    print("\n" + text_report)


if __name__ == "__main__":
    main()
