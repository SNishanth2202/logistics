"""
build_dataset.py
================
Orchestrates the full pipeline:
  1. Load all raw tables (data_preprocessing)
  2. Join and create static features (feature_engineering)
  3. Add temporal historical features (historical_features)
  4. Impute missing values (fit on whole dataset here; train.py re-fits on train only)
  5. Save master_modeling.csv to data/processed/

Run directly to rebuild the dataset:
  python src/build_dataset.py
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from data_preprocessing import load_all
from feature_engineering import build_feature_table
from historical_features import compute_historical_features, get_hist_feature_names

PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = PROCESSED_DIR / "master_modeling.csv"


# ─── Feature column specification ─────────────────────────────────────────────

# These are the columns selected for modeling.
# Excludes: IDs, raw timestamps, post-delivery info, target-derived columns.
FEATURE_COLS = [
    # Time features (from departure_date)
    "hour",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
    "is_peak_hour",

    # Truck features
    "truck_age",
    "load_capacity_pounds",
    "mileage_mpg",
    "fuel_type",               # categorical → encoded in train.py

    # Driver features (linked via vehicle_no → truck_id)
    "driver_age",
    "experience",
    "driving_style",           # categorical → encoded in train.py
    "driver_ratings",
    "average_speed_mph",

    # Route features (static)
    "distance",
    "average_hours",           # historical average duration for this route

    # Weather features (from routes_weather, daily average on departure date)
    "weather_temp",
    "weather_wind_speed",
    "weather_precip",
    "weather_humidity",
    "weather_visibility",
    "weather_chanceofrain",
    "weather_chanceoffog",
    "weather_chanceofsnow",
    "weather_chanceofthunder",

    # Traffic features (at departure hour)
    "traffic_vehicles",
    "traffic_accident",
    "daily_accident_count",    # total accidents on route that day (if available)

    # Truck age category (derived)
    "truck_age_category",      # categorical → encoded in train.py

    # Historical features (temporal, leakage-free)
    "truck_trip_count_hist",
    "truck_delay_rate_hist",
    "route_trip_count_hist",
    "route_delay_rate_hist",
]

# Target
TARGET = "delay"

# Metadata columns (kept in CSV but not fed to model)
META_COLS = ["truck_id", "route_id", "departure_date", "estimated_arrival"]


def impute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply defensible imputation to missing values.

    NOTE: In train.py, imputation parameters are re-fit on training data only.
    Here we impute on the full dataset for the purposes of building master_modeling.csv.
    """
    df = df.copy()

    # Numeric: median imputation
    numeric_medians = {}
    for col in ["load_capacity_pounds", "mileage_mpg", "truck_age", "driver_age",
                "experience", "driver_ratings", "average_speed_mph",
                "distance", "average_hours"]:
        if col in df.columns:
            med = df[col].median()
            df[col] = df[col].fillna(med)
            numeric_medians[col] = float(med)

    # Weather: median per route-date combination (already joined; fill remaining with global median)
    for col in [c for c in df.columns if c.startswith("weather_")]:
        med = df[col].median()
        df[col] = df[col].fillna(med)
        numeric_medians[col] = float(med)

    # Traffic: 0 for missing (assume no unusual traffic)
    for col in ["traffic_vehicles", "traffic_accident", "daily_accident_count"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Categorical: 'Unknown'
    for col in ["fuel_type", "driving_style", "truck_age_category"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)

    # Historical rates: global mean delay (will be properly fit on train in train.py)
    global_rate = df[TARGET].mean()
    df["truck_delay_rate_hist"] = df["truck_delay_rate_hist"].fillna(global_rate)
    df["route_delay_rate_hist"] = df["route_delay_rate_hist"].fillna(global_rate)
    df["truck_trip_count_hist"] = df["truck_trip_count_hist"].fillna(0)
    df["route_trip_count_hist"] = df["route_trip_count_hist"].fillna(0)

    return df, numeric_medians


def print_feature_summary(df: pd.DataFrame) -> None:
    avail_features = [c for c in FEATURE_COLS if c in df.columns]
    missing_features = [c for c in FEATURE_COLS if c not in df.columns]

    print(f"\n{'='*60}")
    print("FEATURE TABLE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total rows           : {len(df):,}")
    print(f"  Target distribution  : delay=0: {(df[TARGET]==0).sum():,} | delay=1: {(df[TARGET]==1).sum():,}")
    print(f"  Delay rate           : {df[TARGET].mean():.3f}")
    print(f"\n  Features available   : {len(avail_features)}/{len(FEATURE_COLS)}")
    if missing_features:
        print(f"  Features MISSING     : {missing_features}")
    print(f"\n  Missing values after imputation:")
    miss = df[avail_features].isnull().sum()
    miss = miss[miss > 0]
    if miss.empty:
        print("    (none)")
    else:
        for col, cnt in miss.items():
            print(f"    {col}: {cnt:,}")
    print(f"\n  Date range: {df['departure_date'].min()} -> {df['departure_date'].max()}")


def main():
    print("=" * 60)
    print("BUILD MASTER MODELING DATASET")
    print("=" * 60)

    # 1. Load all tables
    tables = load_all()

    # 2. Build static features (join + time + truck features)
    df = build_feature_table(
        tables["schedule"],
        tables["trucks"],
        tables["drivers"],
        tables["routes"],
        tables["routes_weather"],
        tables["traffic"],
    )

    # Deduplicate: traffic join can produce fan-out for multi-match hours
    n_before = len(df)
    df = df.drop_duplicates(subset=["truck_id", "departure_date"]).reset_index(drop=True)
    if len(df) < n_before:
        print(f"  Deduplication: removed {n_before - len(df)} fan-out rows -> {len(df):,} rows")

    # 3. Add historical features (temporal, leakage-free)
    df = compute_historical_features(df)

    # 4. Impute missing values
    print("\nImputing missing values ...")
    df, medians = impute_features(df)
    print(f"  Imputation applied. Global delay rate for hist NaN fill: {df[TARGET].mean():.3f}")

    # 5. Select and order columns
    avail_features = [c for c in FEATURE_COLS if c in df.columns]
    keep_cols = META_COLS + avail_features + [TARGET]
    keep_cols = [c for c in keep_cols if c in df.columns]
    df_out = df[keep_cols].copy()

    # 6. Save
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved: {OUTPUT_CSV}")
    print(f"  Shape: {df_out.shape}")

    # 7. Summary
    print_feature_summary(df_out)

    # Save imputation values for reference
    medians_path = PROCESSED_DIR / "imputation_medians.json"
    with open(medians_path, "w") as f:
        json.dump(medians, f, indent=2)
    print(f"\nImputation medians saved: {medians_path}")

    return df_out


if __name__ == "__main__":
    main()
