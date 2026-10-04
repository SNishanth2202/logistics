"""
data_preprocessing.py
=====================
Loads all 7 raw CSV tables, applies type casts, basic cleaning,
and returns a clean dict of DataFrames ready for feature engineering.

NO joins are performed here — that is done in build_dataset.py.
NO train/test split is done here — preprocessing is fit-agnostic
(imputation medians are always computed from the passed DataFrame subset
by the caller, typically from training data only).
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"


# ─── Loaders ──────────────────────────────────────────────────────────────────

def load_schedule() -> pd.DataFrame:
    """Load and clean truck_schedule_table.csv (spine table)."""
    df = pd.read_csv(RAW_DIR / "truck_schedule_table.csv")

    df["truck_id"] = df["truck_id"].astype(int)
    df["route_id"] = df["route_id"].astype(str)
    df["departure_date"] = pd.to_datetime(df["departure_date"], errors="coerce")
    df["estimated_arrival"] = pd.to_datetime(df["estimated_arrival"], errors="coerce")
    df["delay"] = df["delay"].astype(int)

    # Drop rows with invalid departure timestamps (critical key)
    n_before = len(df)
    df = df.dropna(subset=["departure_date"])
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        print(f"  [schedule] Dropped {n_dropped} rows with unparseable departure_date")

    # Drop duplicates on (truck_id, departure_date) — keep first
    dup_mask = df.duplicated(subset=["truck_id", "departure_date"])
    if dup_mask.sum() > 0:
        print(f"  [schedule] Dropped {dup_mask.sum()} duplicate (truck_id, departure_date) rows")
        df = df[~dup_mask].reset_index(drop=True)

    # Derived time columns from departure_date
    df["departure_hour"] = df["departure_date"].dt.hour
    df["departure_date_only"] = df["departure_date"].dt.normalize()  # date at midnight

    print(f"  [schedule] {len(df):,} rows loaded")
    return df.reset_index(drop=True)


def load_trucks() -> pd.DataFrame:
    """Load and clean trucks_table.csv."""
    df = pd.read_csv(RAW_DIR / "trucks_table.csv")

    df["truck_id"] = df["truck_id"].astype(int)
    df["truck_age"] = df["truck_age"].astype(int)
    df["mileage_mpg"] = df["mileage_mpg"].astype(int)

    # Clamp invalid ages
    df.loc[df["truck_age"] < 0, "truck_age"] = np.nan

    # Clamp invalid MPG
    df.loc[df["mileage_mpg"] <= 0, "mileage_mpg"] = np.nan

    # fuel_type: fill missing with 'Unknown'
    df["fuel_type"] = df["fuel_type"].fillna("Unknown").str.strip().str.lower()

    # load_capacity_pounds: keep NaN for now (imputed on train set later)
    print(f"  [trucks] {len(df):,} rows loaded")
    return df


def load_drivers() -> pd.DataFrame:
    """Load and clean drivers_table.csv."""
    df = pd.read_csv(RAW_DIR / "drivers_table.csv")

    df["driver_id"] = df["driver_id"].astype(str)
    df["vehicle_no"] = df["vehicle_no"].astype(int)  # FK to trucks.truck_id

    # gender: fill missing
    df["gender"] = df["gender"].fillna("Unknown").str.strip().str.lower()

    # driving_style: fill missing
    df["driving_style"] = df["driving_style"].fillna("Unknown").str.strip().str.lower()

    # Clamp impossible values (keep but flag)
    df.loc[df["experience"] < 0, "experience"] = np.nan
    df.loc[df["age"] < 18, "age"] = np.nan

    print(f"  [drivers] {len(df):,} rows loaded")
    return df


def load_routes() -> pd.DataFrame:
    """Load and clean routes_table.csv."""
    df = pd.read_csv(RAW_DIR / "routes_table.csv")

    df["route_id"] = df["route_id"].astype(str)
    df["origin_id"] = df["origin_id"].astype(str)
    df["destination_id"] = df["destination_id"].astype(str)

    # Clamp invalid distances
    df.loc[df["distance"] <= 0, "distance"] = np.nan
    df.loc[df["average_hours"] <= 0, "average_hours"] = np.nan

    print(f"  [routes] {len(df):,} rows loaded")
    return df


def load_traffic() -> pd.DataFrame:
    """
    Load and clean traffic_table.csv.

    NOTE: The 'hour' column uses a non-standard encoding:
      0 -> midnight, 100 -> 1am, 200 -> 2am, ... 2300 -> 11pm
    We normalize this to standard 0-23 integer hours by dividing by 100.
    """
    df = pd.read_csv(RAW_DIR / "traffic_table.csv", low_memory=False)

    df["route_id"] = df["route_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Normalize non-standard hour encoding (0, 100, 200, ..., 2300)
    df["hour"] = (df["hour"] / 100).astype(int)

    # Clamp invalid vehicle counts
    df.loc[df["no_of_vehicles"] < 0, "no_of_vehicles"] = np.nan

    # accident: ensure binary
    df["accident"] = df["accident"].clip(0, 1).astype(int)

    print(f"  [traffic] {len(df):,} rows loaded")
    return df


def load_routes_weather() -> pd.DataFrame:
    """
    Load and clean routes_weather.csv.
    Date column: 'Date', format: datetime with time (6-hourly).
    """
    df = pd.read_csv(RAW_DIR / "routes_weather.csv")

    df["route_id"] = df["route_id"].astype(str)
    df["date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.drop(columns=["Date"], inplace=True)

    # Clip invalid values
    df["precip"] = df["precip"].clip(lower=0)
    df["visibility"] = df["visibility"].clip(lower=0)
    for col in ["chanceofrain", "chanceoffog", "chanceofsnow", "chanceofthunder"]:
        df[col] = df[col].clip(0, 100)

    print(f"  [routes_weather] {len(df):,} rows loaded")
    return df


def load_city_weather() -> pd.DataFrame:
    """
    Load and clean city_weather.csv.
    Hourly weather per city. Used as fallback if route weather unavailable.
    """
    df = pd.read_csv(RAW_DIR / "city_weather.csv")

    df["city_id"] = df["city_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Normalize hour (same non-standard encoding as traffic)
    df["hour"] = (df["hour"] / 100).astype(int)

    df["precip"] = df["precip"].clip(lower=0)
    df["visibility"] = df["visibility"].clip(lower=0)
    for col in ["chanceofrain", "chanceoffog", "chanceofsnow", "chanceofthunder"]:
        df[col] = df[col].clip(0, 100)

    print(f"  [city_weather] {len(df):,} rows loaded")
    return df


def load_all() -> dict:
    """Load all tables. Returns dict keyed by table name."""
    print("Loading all tables ...")
    tables = {
        "schedule": load_schedule(),
        "trucks": load_trucks(),
        "drivers": load_drivers(),
        "routes": load_routes(),
        "traffic": load_traffic(),
        "routes_weather": load_routes_weather(),
        "city_weather": load_city_weather(),
    }
    print("\nAll tables loaded successfully.")
    return tables


if __name__ == "__main__":
    tables = load_all()
    for name, df in tables.items():
        print(f"  {name}: {df.shape}")
