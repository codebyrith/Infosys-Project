"""
Spreading Rule Setter Module
Applies rule-based checks on investment spreading and generates
recommendations based on risk levels, trends, and allocation limits.
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
REPORT_PATH = os.path.join(REPORT_DIR, "spreading_rules_report.txt")


# ── Step 1: Load risk results from SQLite ────────────────────────────
def load_risk_results() -> pd.DataFrame:
    """Load the most recent risk result per crypto from the database."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT crypto_name, risk_level, trend, adjusted_eta, timestamp
        FROM risk_results
        WHERE timestamp = (SELECT MAX(timestamp) FROM risk_results)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"Loaded {len(df)} risk results from database.")
    return df


# ── Step 2: Load top investment mix from CSV ─────────────────────────
def load_top_mix() -> pd.Series:
    """Load the rank-1 investment mix from the CSV file."""
    mix_df = pd.read_csv(MIX_CSV)
    top_mix = mix_df.iloc[0]
    print(f"Loaded top investment mix (rank {int(top_mix['rank'])}).")
    return top_mix


# ── Step 3: Apply spreading rules ───────────────────────────────────
def apply_rules(risk_df: pd.DataFrame, top_mix: pd.Series) -> list[str]:
    """Apply rule-based checks and return a list of recommendations."""
    recommendations = []

    # Build a dict of allocations: crypto_name -> percentage
    allocations = {}
    for _, row in risk_df.iterrows():
        name = row["crypto_name"]
        col = f"{name}_pct"
        if col in top_mix.index:
            allocations[name] = top_mix[col]
        else:
            allocations[name] = 0

    # ── Rule 1: HIGH risk → reduce allocation ────────────────────────
    for _, row in risk_df.iterrows():
        name = row["crypto_name"]
        if row["risk_level"] == "HIGH":
            recommendations.append(
                f"{name} risk HIGH -> reduce allocation "
                f"(current: {allocations.get(name, 0):.0f}%)."
            )

    # ── Rule 2: DOWNWARD trend → avoid investing ─────────────────────
    for _, row in risk_df.iterrows():
        name = row["crypto_name"]
        if row["trend"] == "DOWNWARD":
            recommendations.append(
                f"{name} trend DOWNWARD -> avoid investing."
            )
        else:
            recommendations.append(
                f"{name} trend {row['trend']} -> safe to increase allocation."
            )

    # ── Rule 3: Any allocation > 60% → rebalance ────────────────────
    for name, pct in allocations.items():
        if pct > 60:
            recommendations.append(
                f"{name} allocation is {pct:.0f}% (> 60%) -> recommend rebalancing."
            )

    # ── Rule 4: Suggest a safer distribution ─────────────────────────
    safe_cryptos = [
        row["crypto_name"]
        for _, row in risk_df.iterrows()
        if row["risk_level"] != "HIGH" and row["trend"] != "DOWNWARD"
    ]

    if safe_cryptos:
        equal_pct = round(100 / len(safe_cryptos), 1)
        parts = ", ".join(f"{c}: {equal_pct}%" for c in safe_cryptos)
        recommendations.append(
            f"Suggested safer portfolio -> {parts}."
        )
    else:
        recommendations.append(
            "All cryptos are high-risk or downward-trending "
            "-> consider holding cash or stablecoins."
        )

    return recommendations


# ── Step 4: Generate and save recommendations ───────────────────────
def save_report(recommendations: list[str]) -> None:
    """Write recommendations to a text report and print to console."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "=" * 65,
        "  SPREADING RULES – INVESTMENT RECOMMENDATIONS",
        f"  Generated: {timestamp}",
        "=" * 65,
        "",
    ]
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"  {i}. {rec}")
    lines.append("")
    lines.append("=" * 65)
    lines.append("  END OF SPREADING RULES REPORT")
    lines.append("=" * 65)

    report_text = "\n".join(lines)

    # Print to console
    print(report_text)

    # Save to file
    with open(REPORT_PATH, "w") as f:
        f.write(report_text + "\n")
    print(f"\nReport saved to {REPORT_PATH}")


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading risk results from database...")
    risk_df = load_risk_results()

    print("Loading top investment mix from CSV...")
    top_mix = load_top_mix()

    print("Applying spreading rules...\n")
    recommendations = apply_rules(risk_df, top_mix)

    save_report(recommendations)


if __name__ == "__main__":
    main()
