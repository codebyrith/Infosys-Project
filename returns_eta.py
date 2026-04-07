"""
returns_eta.py
--------------
Responsible for calculating investment returns and estimating the
Expected Return (ETA) for each cryptocurrency.

Calculations performed (per crypto):
  • Daily return   = (price_today − price_yesterday) / price_yesterday
  • Average return = mean of all daily returns
  • Total return   = (last_price − first_price) / first_price
  • ETA (Expected Return):
      - Base ETA      = average daily return projected over a chosen horizon
      - Recent trend   = average daily return over the last N days
      - Adjusted ETA   = weighted combination of base ETA and recent trend

All results are saved to data/processed/returns_summary.csv and
data/processed/eta_summary.csv.
"""

import os
import pandas as pd

# ── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR       = os.path.dirname(__file__)
PROC_DATA_DIR  = os.path.join(BASE_DIR, "data", "processed")
PROCESSED_FILE = os.path.join(PROC_DATA_DIR, "processed_prices.csv")
RETURNS_FILE   = os.path.join(PROC_DATA_DIR, "returns_summary.csv")
ETA_FILE       = os.path.join(PROC_DATA_DIR, "eta_summary.csv")

# ── Parameters ──────────────────────────────────────────────────────────────

RECENT_WINDOW  = 7       # Number of recent days used for trend adjustment
ETA_HORIZON    = 30      # Forecast horizon in days for ETA projection
TREND_WEIGHT   = 0.3     # Weight given to recent trend (0 → ignore trend)


# ── Return calculations ────────────────────────────────────────────────────

def calculate_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'daily_return' column to the DataFrame.

    daily_return = (price_today - price_yesterday) / price_yesterday

    The first row for each crypto will be NaN (no previous day).

    Parameters
    ----------
    df : Processed price DataFrame (date, crypto_name, price).

    Returns
    -------
    pd.DataFrame with an additional 'daily_return' column.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["crypto_name", "date"]).reset_index(drop=True)

    # Percentage change within each crypto group
    df["daily_return"] = df.groupby("crypto_name")["price"].pct_change()

    return df


def summarise_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each cryptocurrency compute:
      • average_daily_return  – mean of daily returns
      • total_return          – (last_price − first_price) / first_price
      • std_daily_return      – standard deviation of daily returns
      • min_price / max_price – price range observed

    Parameters
    ----------
    df : DataFrame that already contains a 'daily_return' column.

    Returns
    -------
    pd.DataFrame – One row per crypto with summary statistics.
    """
    summary_rows = []

    for crypto, group in df.groupby("crypto_name"):
        group = group.sort_values("date")
        first_price = group["price"].iloc[0]
        last_price  = group["price"].iloc[-1]

        total_return    = (last_price - first_price) / first_price
        avg_daily_ret   = group["daily_return"].mean()
        std_daily_ret   = group["daily_return"].std()
        min_price       = group["price"].min()
        max_price       = group["price"].max()
        num_days        = len(group)

        summary_rows.append({
            "crypto_name":          crypto,
            "first_price":          round(first_price, 2),
            "last_price":           round(last_price, 2),
            "total_return":         round(total_return, 6),
            "average_daily_return": round(avg_daily_ret, 6),
            "std_daily_return":     round(std_daily_ret, 6),
            "min_price":            round(min_price, 2),
            "max_price":            round(max_price, 2),
            "num_days":             num_days,
        })

    summary_df = pd.DataFrame(summary_rows)
    return summary_df


# ── ETA (Expected Return) estimation ───────────────────────────────────────

def estimate_eta(df: pd.DataFrame,
                 horizon: int = ETA_HORIZON,
                 recent_window: int = RECENT_WINDOW,
                 trend_weight: float = TREND_WEIGHT) -> pd.DataFrame:
    """
    Estimate the Expected Return (ETA) for each cryptocurrency.

    Method
    ------
    1. **Base ETA** = average_daily_return × horizon
       → assumes history repeats uniformly.

    2. **Recent trend** = mean daily return over the last `recent_window` days
       → captures momentum / slowdown.

    3. **Adjusted ETA** = (1 − trend_weight) × base_eta
                        +      trend_weight  × (recent_avg × horizon)
       → blends long-term average with short-term momentum.

    Parameters
    ----------
    df             : DataFrame with 'daily_return' column.
    horizon        : Number of days to project into the future.
    recent_window  : How many recent days to consider for trend.
    trend_weight   : Weight given to the recent trend (0.0 – 1.0).

    Returns
    -------
    pd.DataFrame – One row per crypto with ETA values.
    """
    eta_rows = []

    for crypto, group in df.groupby("crypto_name"):
        group = group.sort_values("date")

        # Overall average daily return (excluding NaN)
        avg_daily = group["daily_return"].mean()

        # Recent trend: average of last N days' returns
        recent = group["daily_return"].dropna().tail(recent_window)
        recent_avg = recent.mean() if len(recent) > 0 else avg_daily

        # Base ETA (simple projection)
        base_eta = avg_daily * horizon

        # Recent-trend projection
        trend_eta = recent_avg * horizon

        # Adjusted ETA (weighted blend)
        adjusted_eta = (1 - trend_weight) * base_eta + trend_weight * trend_eta

        last_price = group["price"].iloc[-1]
        estimated_future_price = last_price * (1 + adjusted_eta)

        eta_rows.append({
            "crypto_name":            crypto,
            "current_price":          round(last_price, 2),
            "avg_daily_return":       round(avg_daily, 6),
            "recent_avg_return":      round(recent_avg, 6),
            "base_eta_pct":           round(base_eta * 100, 4),
            "trend_eta_pct":          round(trend_eta * 100, 4),
            "adjusted_eta_pct":       round(adjusted_eta * 100, 4),
            "estimated_future_price": round(estimated_future_price, 2),
            "horizon_days":           horizon,
        })

    eta_df = pd.DataFrame(eta_rows)
    return eta_df


# ── Save helpers ────────────────────────────────────────────────────────────

def save_returns(summary_df: pd.DataFrame) -> str:
    """Save the returns summary to CSV."""
    os.makedirs(PROC_DATA_DIR, exist_ok=True)
    summary_df.to_csv(RETURNS_FILE, index=False)
    print(f"  [OK] Returns summary saved -> {RETURNS_FILE}")
    return RETURNS_FILE


def save_eta(eta_df: pd.DataFrame) -> str:
    """Save the ETA summary to CSV."""
    os.makedirs(PROC_DATA_DIR, exist_ok=True)
    eta_df.to_csv(ETA_FILE, index=False)
    print(f"  [OK] ETA summary saved     -> {ETA_FILE}")
    return ETA_FILE


# ── Main entry point for this module ────────────────────────────────────────

def compute_all(processed_df: pd.DataFrame = None) -> tuple:
    """
    Full returns + ETA pipeline.

    Parameters
    ----------
    processed_df : If None, loads from data/processed/processed_prices.csv.

    Returns
    -------
    (returns_summary_df, eta_summary_df)
    """
    if processed_df is None:
        if not os.path.exists(PROCESSED_FILE):
            raise FileNotFoundError(
                f"Processed file not found: {PROCESSED_FILE}. "
                "Run data_processing.py first."
            )
        processed_df = pd.read_csv(PROCESSED_FILE)

    # Step 1 – daily returns
    df_with_returns = calculate_daily_returns(processed_df)

    # Step 2 – summary statistics
    returns_summary = summarise_returns(df_with_returns)
    save_returns(returns_summary)

    # Step 3 – ETA estimation
    eta_summary = estimate_eta(df_with_returns)
    save_eta(eta_summary)

    return returns_summary, eta_summary


# ── Stand-alone execution ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Returns & ETA (standalone) ===")
    ret_df, eta_df = compute_all()
    print("\n— Returns Summary —")
    print(ret_df.to_string(index=False))
    print("\n— ETA Summary —")
    print(eta_df.to_string(index=False))
