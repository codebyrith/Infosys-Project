
import os
import pandas as pd
from itertools import product

# ============================================================
# STEP 1: Load the two summary CSV files
# ============================================================

returns_path = os.path.join("data", "processed", "returns_summary.csv")
eta_path = os.path.join("data", "processed", "eta_summary.csv")

print("Loading returns_summary.csv ...")
returns_df = pd.read_csv(returns_path)

print("Loading eta_summary.csv ...")
eta_df = pd.read_csv(eta_path)

print(f"  Returns data shape : {returns_df.shape}")
print(f"  ETA data shape     : {eta_df.shape}")

# ============================================================
# STEP 2: Merge the two DataFrames on crypto_name
# ============================================================
# We use an inner join so only cryptos present in BOTH files are kept.
# Suffix handling avoids column name clashes if both files share columns.

merged_df = pd.merge(
    returns_df,
    eta_df,
    on="crypto_name",
    suffixes=("_ret", "_eta")
)

print(f"\nMerged data shape: {merged_df.shape}")
print(merged_df[["crypto_name"]].to_string(index=False))

# ============================================================
# STEP 3: Extract data for exactly 3 cryptocurrencies
# ============================================================
# Pick the columns we need. If a column appears in both files,
# the suffix tells us which one to use.
# We prefer the returns file for return/risk, eta file for eta.

# Helper: pick the right column name (handles suffix if present)
def pick_col(df, base_name, preferred_suffix="_ret"):
    """Return the actual column name present in the dataframe."""
    if base_name in df.columns:
        return base_name
    elif base_name + preferred_suffix in df.columns:
        return base_name + preferred_suffix
    elif base_name + "_eta" in df.columns:
        return base_name + "_eta"
    else:
        raise KeyError(f"Column '{base_name}' not found in merged data.")

col_return = pick_col(merged_df, "average_daily_return", "_ret")
col_risk   = pick_col(merged_df, "std_daily_return", "_ret")
col_eta    = pick_col(merged_df, "adjusted_eta_pct", "_eta")

# Store crypto info in simple lists (easy to explain in viva)
crypto_names   = merged_df["crypto_name"].tolist()
avg_returns    = merged_df[col_return].tolist()
std_risks      = merged_df[col_risk].tolist()
adjusted_etas  = merged_df[col_eta].tolist()

num_cryptos = len(crypto_names)
print(f"\nNumber of cryptocurrencies: {num_cryptos}")

if num_cryptos != 3:
    print(f"WARNING: Expected exactly 3 cryptos, found {num_cryptos}. "
          f"Using first 3 only.")
    crypto_names  = crypto_names[:3]
    avg_returns   = avg_returns[:3]
    std_risks     = std_risks[:3]
    adjusted_etas = adjusted_etas[:3]

print("\nCrypto details:")
for i in range(3):
    print(f"  {crypto_names[i]:>12s}  |  return={avg_returns[i]:.4f}  "
          f"|  risk={std_risks[i]:.4f}  |  eta={adjusted_etas[i]:.2f}%")

# ============================================================
# STEP 4 & 5: Generate all valid allocation combinations
# ============================================================
# Allocations go from 0% to 100% in steps of 10%.
# Rules:
#   - Total must equal 100%
#   - No single crypto can exceed 60%
#   - At least 2 cryptos must have a non-zero allocation

steps = range(0, 110, 10)  # 0, 10, 20, ..., 100

valid_mixes = []  # will hold tuples like (w1, w2, w3)

for w1, w2, w3 in product(steps, repeat=3):
    # Rule 1: total must be 100%
    if w1 + w2 + w3 != 100:
        continue
    # Rule 2: no single crypto > 60%
    if w1 > 60 or w2 > 60 or w3 > 60:
        continue
    # Rule 3: at least 2 cryptos must be active (non-zero)
    active_count = sum(1 for w in (w1, w2, w3) if w > 0)
    if active_count < 2:
        continue

    valid_mixes.append((w1, w2, w3))

print(f"\nTotal valid allocation mixes: {len(valid_mixes)}")

# ============================================================
# STEP 6: Calculate weighted metrics for each mix
# ============================================================
# For each combination we compute:
#   weighted_return = sum(weight_i * return_i)
#   weighted_eta    = sum(weight_i * eta_i)
#   weighted_risk   = sum(weight_i * risk_i)
# Weights are converted from percentage (e.g. 40) to fraction (0.40).

results = []

for w1, w2, w3 in valid_mixes:
    # Convert percentages to fractions
    weights = [w1 / 100, w2 / 100, w3 / 100]

    # Weighted portfolio return
    weighted_return = sum(weights[i] * avg_returns[i] for i in range(3))

    # Weighted portfolio ETA
    weighted_eta = sum(weights[i] * adjusted_etas[i] for i in range(3))

    # Weighted portfolio risk (standard deviation)
    weighted_risk = sum(weights[i] * std_risks[i] for i in range(3))

    # --------------------------------------------------------
    # STEP 7: Simple scoring formula
    # --------------------------------------------------------
    # Higher ETA is better (more growth potential).
    # Higher risk is worse, so we subtract a penalty.
    # The 0.5 multiplier controls how much we penalise risk.
    score = weighted_eta - (weighted_risk * 0.5)

    results.append({
        f"{crypto_names[0]}_pct": w1,
        f"{crypto_names[1]}_pct": w2,
        f"{crypto_names[2]}_pct": w3,
        "weighted_return": round(weighted_return, 6),
        "weighted_eta": round(weighted_eta, 4),
        "weighted_risk": round(weighted_risk, 6),
        "score": round(score, 4)
    })

# Convert to DataFrame for easy sorting and saving
results_df = pd.DataFrame(results)
print(f"\nCalculated metrics for {len(results_df)} mixes.")

# ============================================================
# STEP 8: Rank mixes by score (highest first)
# ============================================================

results_df = results_df.sort_values(by="score", ascending=False).reset_index(drop=True)

# Add a rank column (1 = best)
results_df.insert(0, "rank", range(1, len(results_df) + 1))

# ============================================================
# STEP 9: Select the top 5 mixes
# ============================================================

top5 = results_df.head(5)

print("\n" + "=" * 70)
print("  TOP 5 INVESTMENT MIXES (ranked by score)")
print("=" * 70)
print(top5.to_string(index=False))
print("=" * 70)

# ============================================================
# STEP 10: Save results to CSV
# ============================================================

output_dir = os.path.join("data", "processed")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "investment_mix_results.csv")
top5.to_csv(output_path, index=False)

print(f"\nTop 5 mixes saved to: {output_path}")
print("Done!")