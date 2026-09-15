"""
preprocessing.py
================
Reusable cleaning pipeline for the LaDe Shanghai delivery dataset.

Cleaning rules (documented):
  1. Remove rows where accept_time or delivery_time failed to parse (NaT).
  2. Remove rows where delivery_time <= accept_time  (zero or negative duration).
     Rationale: 3,148 zero-duration rows found — likely data-entry artefacts
     (courier marking delivery before accepting, or batch inserts with same ts).
  3. Remove records with GPS coordinates outside the Shanghai bounding box.
     Shanghai bbox: lng [120.0, 122.5], lat [30.0, 32.0]
     Rows outside this (≈2) have destination lng ≈ 102 (Yunnan) — corrupt.
  4. Remove rows where delivery_gps_lng < 1 or delivery_gps_lat < 1
     (near-zero GPS — sensor dropout).
  5. Cap extreme delivery durations.
     Outlier analysis:
       - 99th pct ≈ 652 min, 99.5th pct ≈ 787 min
       - >24h (1440 min): 3,578 rows — unlikely for last-mile courier,
         almost certainly abandoned/re-assigned orders or data errors.
     Rule: retain records with duration <= 1440 minutes (24 hours).
     This removes only 0.24 % of the data and is documented here.
     The upper bound is conservative to avoid arbitrarily shrinking the set.

Outputs
-------
  data/processed/cleaned_delivery_sh.csv
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Bounding box for Shanghai ─────────────────────────────────────────────────
# Conservative bbox that covers all of Shanghai municipality
SHANGHAI_LNG_MIN, SHANGHAI_LNG_MAX = 120.5, 122.5
SHANGHAI_LAT_MIN, SHANGHAI_LAT_MAX = 30.5, 32.0

# ── Outlier cap ───────────────────────────────────────────────────────────────
# Any delivery taking longer than 24 hours is treated as corrupt / abandoned.
DURATION_CAP_MINUTES = 1440  # 24 hours


def clean(df: pd.DataFrame, *, verbose: bool = True) -> pd.DataFrame:
    """
    Apply the full cleaning pipeline and return a cleaned DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Output of data_loader.load_raw().  Must contain *_dt datetime columns.
    verbose : bool
        Print a step-by-step cleaning report.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with `delivery_duration_minutes` column added.
    """
    original_len = len(df)
    report_lines: list[str] = []

    def _drop(mask: pd.Series, reason: str) -> pd.DataFrame:
        n = mask.sum()
        report_lines.append(f"  [{reason}] removed {n:,} rows ({n/original_len:.3%})")
        return df[~mask].copy()

    # ── Step 1: failed timestamp parses ──────────────────────────────────────
    mask_bad_ts = df["accept_time_dt"].isna() | df["delivery_time_dt"].isna()
    df = _drop(mask_bad_ts, "bad timestamp parse")

    # ── Step 2: compute duration; drop zero / negative ────────────────────────
    df["delivery_duration_minutes"] = (
        (df["delivery_time_dt"] - df["accept_time_dt"]).dt.total_seconds() / 60.0
    )
    mask_non_positive = df["delivery_duration_minutes"] <= 0
    df = _drop(mask_non_positive, "zero or negative duration")

    # ── Step 3: destination GPS outside Shanghai ──────────────────────────────
    mask_bad_dest = (
        (df["lng"] < SHANGHAI_LNG_MIN) | (df["lng"] > SHANGHAI_LNG_MAX)
        | (df["lat"] < SHANGHAI_LAT_MIN) | (df["lat"] > SHANGHAI_LAT_MAX)
    )
    df = _drop(mask_bad_dest, "destination GPS outside Shanghai")

    # ── Step 4: corrupt delivery GPS (negative or near-zero — sensor dropout) ──
    mask_zero_gps = (
        (df["delivery_gps_lng"] < 1.0) | (df["delivery_gps_lat"] < 1.0)
        | (df["delivery_gps_lng"] < 0) | (df["delivery_gps_lat"] < 0)
    )
    df = _drop(mask_zero_gps, "corrupt delivery GPS (< 1 or negative)")

    # ── Step 4b: corrupt accept GPS (courier position outside Shanghai) ───────
    # This causes wildly wrong Haversine distances (e.g. 1446 km).
    mask_bad_accept_gps = (
        (df["accept_gps_lng"] < SHANGHAI_LNG_MIN) | (df["accept_gps_lng"] > SHANGHAI_LNG_MAX)
        | (df["accept_gps_lat"] < SHANGHAI_LAT_MIN) | (df["accept_gps_lat"] > SHANGHAI_LAT_MAX)
    )
    df = _drop(mask_bad_accept_gps, "accept GPS outside Shanghai bbox")

    # ── Step 5: extreme duration outliers ────────────────────────────────────
    if verbose:
        q99 = df["delivery_duration_minutes"].quantile(0.99)
        q995 = df["delivery_duration_minutes"].quantile(0.995)
        report_lines.append(
            f"  [outlier info] 99th pct={q99:.1f} min | "
            f"99.5th pct={q995:.1f} min | cap={DURATION_CAP_MINUTES} min"
        )
    mask_extreme = df["delivery_duration_minutes"] > DURATION_CAP_MINUTES
    df = _drop(mask_extreme, f"duration > {DURATION_CAP_MINUTES} min")

    if verbose:
        print("=" * 60)
        print("CLEANING REPORT")
        print("=" * 60)
        print(f"  Original rows     : {original_len:,}")
        for line in report_lines:
            print(line)
        print(f"  Remaining rows    : {len(df):,}  "
              f"({len(df)/original_len:.2%} retained)")
        print("=" * 60)

    return df.reset_index(drop=True)


def save_cleaned(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save the cleaned DataFrame to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Saved cleaned data → %s  (%d rows)", output_path, len(df))
    print(f"Saved cleaned data → {output_path}  ({len(df):,} rows)")


def duration_summary(df: pd.DataFrame) -> dict:
    """
    Return summary statistics for delivery_duration_minutes.

    Returns
    -------
    dict with keys: mean, median, std, p25, p75, p95, p99
    """
    s = df["delivery_duration_minutes"]
    stats = {
        "mean": s.mean(),
        "median": s.median(),
        "std": s.std(),
        "p25": s.quantile(0.25),
        "p75": s.quantile(0.75),
        "p95": s.quantile(0.95),
        "p99": s.quantile(0.99),
    }
    print("\nDelivery Duration Summary (minutes):")
    print(f"  Mean   : {stats['mean']:.2f}")
    print(f"  Median : {stats['median']:.2f}")
    print(f"  Std    : {stats['std']:.2f}")
    print(f"  P25    : {stats['p25']:.2f}")
    print(f"  P75    : {stats['p75']:.2f}")
    print(f"  P95    : {stats['p95']:.2f}")
    print(f"  P99    : {stats['p99']:.2f}")
    return stats
