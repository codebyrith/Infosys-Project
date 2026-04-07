"""
main.py
-------
Entry point for the Crypto Investment Manager.

Execution order:
  1. Collect              – fetch raw price data from CoinGecko
  2. Process              – clean and standardise the raw data
  3. Returns & ETA        – calculate returns and estimate ETA
  4. Investment Mix       – compute optimal investment mix   (subprocess)
  5. Risk Checker         – classify risk levels & trends    (subprocess)
  6. Report Generator     – build the final report           (subprocess)
  7. Email Alert          – send alert if high-risk found    (subprocess)

Run:
    python main.py
"""

import sys
import subprocess

from data_collection import collect_all
from data_processing import process_all
from returns_eta     import compute_all


# ── Helpers ──────────────────────────────────────────────────────────

def print_header(step_number: int, total: int, title: str) -> None:
    """Print a clear section header for each pipeline step."""
    print()
    print("=" * 60)
    print(f"  [{step_number}/{total}]  {title}")
    print("=" * 60)


def run_script(script_name: str) -> None:
    """Run a standalone Python script as a subprocess.

    Raises SystemExit if the script returns a non-zero exit code.
    """
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=False,          # let output stream to console
    )
    if result.returncode != 0:
        print(f"\n  ERROR: {script_name} failed (exit code {result.returncode}).")
        sys.exit(result.returncode)


# ── Main pipeline ────────────────────────────────────────────────────

TOTAL_STEPS = 8


def main():
    """Execute the full pipeline: Collect → Process → Analyse → Mix → Risk → Report → Alert."""

    print("=" * 60)
    print("  CRYPTO INVESTMENT MANAGER  –  Full Pipeline")
    print("=" * 60)

    # ── Step 1: Data Collection ──────────────────────────────────────
    print_header(1, TOTAL_STEPS, "Data Collection")
    saved_files = collect_all()
    if not saved_files:
        print("  No data was collected. Exiting.")
        sys.exit(1)
    print(f"  Collected data for: {', '.join(saved_files.keys())}")

    # ── Step 2: Data Processing ──────────────────────────────────────
    print_header(2, TOTAL_STEPS, "Data Processing")
    processed_df = process_all()
    print("  Data processing complete.")

    # ── Step 3: Returns & ETA ────────────────────────────────────────
    print_header(3, TOTAL_STEPS, "Returns & ETA Calculation")
    returns_summary, eta_summary = compute_all(processed_df)
    print("  Returns & ETA calculation complete.")

    # ── Step 4: Investment Mix Calculator (standalone) ───────────────
    print_header(4, TOTAL_STEPS, "Investment Mix Calculator")
    run_script("investment_mix_calculator.py")
    print("  Investment mix calculation complete.")

    # ── Step 5: Risk Checker (standalone) ────────────────────────────
    print_header(5, TOTAL_STEPS, "Risk Checker")
    run_script("risk_checker.py")
    print("  Risk check complete.")

    # ── Step 6: Report Generator (standalone) ────────────────────────
    print_header(6, TOTAL_STEPS, "Report Generator")
    run_script("report_generator.py")
    print("  Report generation complete.")

    # ── Step 7: Spreading Rule Setter (standalone) ──────────────────
    print_header(7, TOTAL_STEPS, "Spreading Rule Setter")
    run_script("spreading_rule_setter.py")
    print("  Spreading rules complete.")

    # ── Step 8: Email Alert (standalone) ─────────────────────────────
    print_header(8, TOTAL_STEPS, "Email Alert")
    run_script("email_alert.py")
    print("  Email alert step complete.")

    # ── Done ─────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  Pipeline finished successfully!")
    print("  Check data/reports/ for the final report.")
    print("=" * 60)


if __name__ == "__main__":
    main()
