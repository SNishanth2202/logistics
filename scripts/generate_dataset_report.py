"""
scripts/generate_dataset_report.py
====================================
Phase 2: Load the raw CSV, print and save a comprehensive dataset report.
Run from logistics-ai/ directory:
  python scripts/generate_dataset_report.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import numpy as np
from data_loader import load_raw

RAW_CSV = ROOT / "data" / "raw" / "delivery_sh.csv"
REPORT_PATH = ROOT / "reports" / "dataset_report.txt"


def build_report(df: pd.DataFrame) -> str:
    lines = []

    def h(title: str) -> None:
        lines.append("\n" + "=" * 60)
        lines.append(title)
        lines.append("=" * 60)

    h("LADES DELIVERY DATASET — INSPECTION REPORT")
    lines.append(f"Generated from: {RAW_CSV}")
    lines.append(f"Dataset year  : 2023 (LaDe paper)")

    h("BASIC SHAPE")
    lines.append(f"  Rows    : {len(df):,}")
    lines.append(f"  Columns : {len(df.columns)}")

    h("COLUMN NAMES & DTYPES")
    for col in df.columns:
        lines.append(f"  {col:<30} {str(df[col].dtype)}")

    h("MISSING VALUES")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        lines.append("  No missing values in any column.")
    else:
        for col, cnt in missing[missing > 0].items():
            lines.append(f"  {col}: {cnt:,}  ({cnt/len(df):.3%})")

    h("DUPLICATE ROWS")
    lines.append(f"  {df.duplicated().sum():,} duplicate rows")

    h("UNIQUE VALUE COUNTS")
    for col in ["courier_id", "region_id", "aoi_id", "aoi_type", "city"]:
        lines.append(f"  {col:<20} {df[col].nunique():,} unique values")

    h("DATE RANGE (reconstructed from timestamps)")
    lines.append(f"  accept_time  : {df['accept_time_dt'].min()} -> {df['accept_time_dt'].max()}")
    lines.append(f"  delivery_time: {df['delivery_time_dt'].min()} -> {df['delivery_time_dt'].max()}")

    h("GPS COORDINATE RANGES")
    for col in ["lng", "lat", "accept_gps_lng", "accept_gps_lat", "delivery_gps_lng", "delivery_gps_lat"]:
        lines.append(f"  {col:<24} min={df[col].min():.5f}  max={df[col].max():.5f}")

    h("DELIVERY DURATION (PRELIMINARY — before cleaning)")
    df["_dur"] = (df["delivery_time_dt"] - df["accept_time_dt"]).dt.total_seconds() / 60
    lines.append(f"  Count     : {df['_dur'].count():,}")
    lines.append(f"  Mean      : {df['_dur'].mean():.2f} min")
    lines.append(f"  Median    : {df['_dur'].median():.2f} min")
    lines.append(f"  Std       : {df['_dur'].std():.2f} min")
    lines.append(f"  P25       : {df['_dur'].quantile(0.25):.2f} min")
    lines.append(f"  P75       : {df['_dur'].quantile(0.75):.2f} min")
    lines.append(f"  P95       : {df['_dur'].quantile(0.95):.2f} min")
    lines.append(f"  P99       : {df['_dur'].quantile(0.99):.2f} min")
    lines.append(f"  Max       : {df['_dur'].max():.2f} min")
    lines.append(f"  Negative  : {(df['_dur'] < 0).sum():,} rows")
    lines.append(f"  Zero      : {(df['_dur'] == 0).sum():,} rows")
    lines.append(f"  > 24h     : {(df['_dur'] > 1440).sum():,} rows")
    lines.append(f"  > 12h     : {(df['_dur'] > 720).sum():,} rows")

    h("SAMPLE ROWS (first 5, formatted)")
    cols_to_show = ["order_id", "courier_id", "region_id", "aoi_id", "aoi_type",
                    "accept_time", "delivery_time", "lng", "lat"]
    lines.append(df[cols_to_show].head(5).to_string())

    h("COLUMN INTERPRETATIONS")
    interpretations = {
        "order_id": "Unique identifier for each delivery order.",
        "region_id": "Sub-region of Shanghai (52 unique sub-areas). Likely administrative zones.",
        "city": "Always 'Shanghai' in this file — constant, not a useful feature.",
        "courier_id": "Identifier for the delivery courier/driver (1,733 unique).",
        "lng": "Longitude of the DELIVERY DESTINATION (not pickup). Shanghai range ≈ 120.8–122.2.",
        "lat": "Latitude of the DELIVERY DESTINATION. Shanghai range ≈ 30.6–31.5.",
        "aoi_id": "Area-of-Interest zone ID (1,047 unique). Defines micro delivery zones.",
        "aoi_type": "Category of the AOI (0–15). Likely zone type: residential, commercial, etc. Type 1 is dominant.",
        "accept_time": "Timestamp when the courier accepted/received the order. Format: MM-DD HH:MM:SS (year=2023).",
        "accept_gps_time": "GPS log timestamp at accept moment. Essentially matches accept_time.",
        "accept_gps_lng": "Courier's GPS longitude at the moment of order acceptance.",
        "accept_gps_lat": "Courier's GPS latitude at the moment of order acceptance.",
        "delivery_time": "Timestamp when the courier marked delivery complete.",
        "delivery_gps_time": "GPS log timestamp at delivery. Matches delivery_time closely.",
        "delivery_gps_lng": "Courier GPS longitude at delivery completion. May differ from destination lng due to GPS noise.",
        "delivery_gps_lat": "Courier GPS latitude at delivery completion.",
        "ds": "Date integer in MMDD format (e.g. 604 = June 4). Redundant with accept_time date component.",
    }
    for col, interp in interpretations.items():
        lines.append(f"\n  {col}:")
        lines.append(f"    {interp}")

    h("DATA QUALITY ISSUES FOUND")
    issues = [
        "1. Timestamps lack year — must prepend '2023-' before parsing.",
        "2. 3,148 zero-duration records (delivery_time == accept_time) — data-entry artefacts.",
        "3. ~2 records with destination GPS in Yunnan (lng≈102) — clearly outside Shanghai.",
        "4. ~2 records with delivery_gps near (0,0) — GPS sensor dropout.",
        "5. 3,578 records with duration > 24h — likely abandoned/re-assigned orders.",
        "6. Max duration of 47,739 min (~33 days) — clearly corrupt/open order records.",
        "7. delivery_time for some orders extends into November 2023 (beyond the October cutoff).",
        "   This is valid: orders accepted Oct 31 may be delivered in November.",
    ]
    for issue in issues:
        lines.append(f"  {issue}")

    return "\n".join(lines)


def main():
    print("Loading raw dataset ...")
    df = load_raw(RAW_CSV, verbose=True)

    print("\nGenerating report ...")
    report_text = build_report(df)

    print(report_text)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(f"\nReport saved → {REPORT_PATH}")


if __name__ == "__main__":
    main()
