"""
scripts/preprocess.py
=====================
Phase 3: Run the full preprocessing pipeline.
Loads raw CSV → cleans → saves cleaned_delivery_sh.csv.
Also runs feature engineering and historical feature computation,
saving the fully-featurised dataset ready for training.

Run from logistics-ai/ directory:
  python scripts/preprocess.py
"""

import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_loader import load_raw
from preprocessing import clean, save_cleaned, duration_summary
from feature_engineering import engineer_features
from historical_features import compute_historical_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

RAW_CSV = ROOT / "data" / "raw" / "delivery_sh.csv"
CLEANED_CSV = ROOT / "data" / "processed" / "cleaned_delivery_sh.csv"
FIGURES_DIR = ROOT / "reports" / "figures"


def plot_duration_distribution(df, output_dir: Path):
    """Phase 4: Plot delivery duration distribution."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    dur = df["delivery_duration_minutes"]
    axes[0].hist(dur, bins=100, color="#4A90D9", edgecolor="none", alpha=0.85)
    axes[0].set_xlabel("Delivery Duration (minutes)", fontsize=12)
    axes[0].set_ylabel("Count", fontsize=12)
    axes[0].set_title("Delivery Duration Distribution (Full Range)", fontsize=13)
    for p, label in [(0.25, "P25"), (0.5, "Median"), (0.75, "P75"), (0.95, "P95")]:
        axes[0].axvline(dur.quantile(p), color="red", linestyle="--", alpha=0.7, linewidth=1)
        axes[0].text(dur.quantile(p), axes[0].get_ylim()[1]*0.9, label, color="red", fontsize=8, ha="center")

    axes[1].hist(dur[dur <= 360], bins=80, color="#5BAD6F", edgecolor="none", alpha=0.85)
    axes[1].set_xlabel("Delivery Duration (minutes, ≤ 6h)", fontsize=12)
    axes[1].set_ylabel("Count", fontsize=12)
    axes[1].set_title("Delivery Duration — Zoomed (≤ 360 min)", fontsize=13)

    fig.suptitle("Target Variable: delivery_duration_minutes", fontsize=14, y=1.01)
    fig.tight_layout()
    fig.savefig(output_dir / "duration_distribution.png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Duration distribution plot → {output_dir}/duration_distribution.png")


def main():
    t0 = time.time()

    # Phase 2: Load
    print("\n[Phase 2] Loading raw data ...")
    df = load_raw(RAW_CSV, verbose=True)

    # Phase 3: Clean
    print("\n[Phase 3] Cleaning ...")
    df_clean = clean(df, verbose=True)

    # Phase 4: Duration summary + plot
    print("\n[Phase 4] Duration statistics ...")
    duration_summary(df_clean)
    plot_duration_distribution(df_clean, FIGURES_DIR)

    # Phase 5a: Static feature engineering
    print("\n[Phase 5a] Static feature engineering ...")
    df_feat = engineer_features(df_clean)
    print(f"  Added: hour, day_of_week, day_of_month, month, is_weekend, straight_line_distance_km")
    print(f"  Distance range: {df_feat['straight_line_distance_km'].min():.4f} — {df_feat['straight_line_distance_km'].max():.4f} km")

    # Phase 5b: Historical features
    print("\n[Phase 5b] Historical features (leakage-safe expanding window) ...")
    print("  This may take several minutes on 1.4M rows ...")
    t_hist = time.time()
    df_feat = compute_historical_features(df_feat)
    print(f"  Historical features computed in {(time.time()-t_hist)/60:.1f} min")

    # Save
    print("\nSaving cleaned + featurised dataset ...")
    save_cleaned(df_feat, CLEANED_CSV)

    print(f"\nTotal preprocessing time: {(time.time()-t0)/60:.1f} min")
    print("Done. Ready to run src/train.py")


if __name__ == "__main__":
    main()
