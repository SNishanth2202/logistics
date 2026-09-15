"""
feature_engineering.py
=======================
Creates static (non-historical) features by joining:
  schedule + trucks + drivers + routes + routes_weather (daily avg) + traffic (departure hour)

Features are leakage-free because they are either:
  - Static attributes (truck/driver/route properties)
  - Environmental conditions AT the departure time (weather/traffic)
  - Derived time features from departure_date

Historical/rolling features (per driver/truck/route) are computed
separately in historical_features.py using temporal expanding windows.

Join strategy:
  1. schedule → trucks (truck_id:truck_id)  [inner — truck must exist]
  2. merged → drivers (truck_id:vehicle_no)  [left — some trucks may have no driver]
  3. merged → routes (route_id:route_id)     [inner — route must exist]
  4. merged → routes_weather (route_id + date)  [left, daily average]
  5. merged → traffic (route_id + date + departure_hour)  [left, closest hour]
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent


# ─── Weather aggregation ───────────────────────────────────────────────────────

def aggregate_routes_weather_daily(rw: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate 6-hourly routes_weather to daily per route.
    Returns one row per (route_id, date_only).
    All numeric weather columns are averaged.
    """
    rw = rw.copy()
    rw["date_only"] = rw["date"].dt.normalize()

    numeric_cols = ["temp", "wind_speed", "precip", "humidity", "visibility",
                    "pressure", "chanceofrain", "chanceoffog", "chanceofsnow", "chanceofthunder"]
    available = [c for c in numeric_cols if c in rw.columns]

    daily = (
        rw.groupby(["route_id", "date_only"], as_index=False)[available]
        .mean()
        .rename(columns={c: f"weather_{c}" for c in available})
    )
    return daily


# ─── Traffic aggregation ───────────────────────────────────────────────────────

def aggregate_traffic_departure(traffic: pd.DataFrame) -> pd.DataFrame:
    """
    For each (route_id, date, hour) record, keep as-is (already hourly).
    We'll join on the closest available hour to departure.

    Returns traffic with date_only column for joining.
    """
    t = traffic.copy()
    t["date_only"] = t["date"].dt.normalize()
    return t


def join_traffic_to_schedule(sched: pd.DataFrame, traffic: pd.DataFrame) -> pd.DataFrame:
    """
    Join traffic features to schedule on (route_id, date_only, closest hour).
    We match the departure_hour to the traffic hour using exact match first,
    then fall back to the same-day route average if no exact hour match.
    """
    # Daily average traffic per route as fallback
    daily_traffic = (
        traffic.groupby(["route_id", "date_only"], as_index=False)
        .agg(
            avg_no_of_vehicles=("no_of_vehicles", "mean"),
            max_accident=("accident", "max"),
            daily_accident_count=("accident", "sum"),
        )
    )

    # Exact hour match
    traffic_hour = traffic.rename(columns={
        "no_of_vehicles": "traffic_no_of_vehicles",
        "accident": "traffic_accident",
    })[["route_id", "date_only", "hour", "traffic_no_of_vehicles", "traffic_accident"]]

    # Merge exact hour
    sched = sched.copy()
    sched["_date_only"] = sched["departure_date"].dt.normalize()
    sched["_dep_hour"] = sched["departure_date"].dt.hour

    merged = sched.merge(
        traffic_hour.rename(columns={"hour": "_dep_hour"}),
        left_on=["route_id", "_date_only", "_dep_hour"],
        right_on=["route_id", "date_only", "_dep_hour"],
        how="left",
        suffixes=("", "_tw")
    )
    if "date_only" in merged.columns:
        merged.drop(columns=["date_only"], inplace=True, errors="ignore")

    # Fill unmatched with daily average
    merged = merged.merge(daily_traffic, left_on=["route_id", "_date_only"],
                          right_on=["route_id", "date_only"], how="left")
    if "date_only" in merged.columns:
        merged.drop(columns=["date_only"], inplace=True, errors="ignore")

    # Use exact if available, otherwise daily avg
    merged["traffic_no_of_vehicles"] = merged["traffic_no_of_vehicles"].fillna(merged["avg_no_of_vehicles"])
    merged["traffic_accident"] = merged["traffic_accident"].fillna(merged["max_accident"])
    merged.drop(columns=["avg_no_of_vehicles", "max_accident"], inplace=True, errors="ignore")

    return merged


# ─── Static time features ─────────────────────────────────────────────────────

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add departure time-based features. All from departure_date (known before trip)."""
    dt = df["departure_date"]
    df = df.copy()
    df["hour"] = dt.dt.hour.astype("int8")
    df["day_of_week"] = dt.dt.dayofweek.astype("int8")     # 0=Mon, 6=Sun
    df["day_of_month"] = dt.dt.day.astype("int8")
    df["month"] = dt.dt.month.astype("int8")
    df["is_weekend"] = (dt.dt.dayofweek >= 5).astype("int8")
    df["is_peak_hour"] = (dt.dt.hour.isin([7, 8, 9, 17, 18, 19])).astype("int8")
    return df


# ─── Derived truck features ───────────────────────────────────────────────────

def add_truck_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived truck features from joined truck columns."""
    df = df.copy()
    # Truck age category: 0-5 new, 6-10 mid, 11+ old
    if "truck_age" in df.columns:
        df["truck_age_category"] = pd.cut(
            df["truck_age"],
            bins=[-1, 5, 10, 100],
            labels=["new", "mid", "old"]
        ).astype(str)
    return df


# ─── Master join ──────────────────────────────────────────────────────────────

def build_feature_table(
    schedule: pd.DataFrame,
    trucks: pd.DataFrame,
    drivers: pd.DataFrame,
    routes: pd.DataFrame,
    routes_weather: pd.DataFrame,
    traffic: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the master feature table by joining all tables to the schedule spine.

    Returns a DataFrame with all features + target ('delay').
    """
    print("\nBuilding master feature table ...")
    n0 = len(schedule)
    print(f"  Schedule rows: {n0:,}")

    # ── 1. Schedule → Trucks ─────────────────────────────────────────────────
    truck_cols = ["truck_id", "truck_age", "load_capacity_pounds", "mileage_mpg", "fuel_type"]
    df = schedule.merge(trucks[truck_cols], on="truck_id", how="inner")
    n1 = len(df)
    print(f"  After → Trucks join : {n1:,}  (dropped {n0-n1} unmatched)")

    # ── 2. Trucks → Drivers (via vehicle_no = truck_id) ──────────────────────
    driver_cols = ["vehicle_no", "age", "experience", "driving_style",
                   "ratings", "average_speed_mph"]
    # vehicle_no in drivers == truck_id in trucks
    df = df.merge(
        drivers[driver_cols].rename(columns={"vehicle_no": "truck_id",
                                              "age": "driver_age",
                                              "ratings": "driver_ratings"}),
        on="truck_id",
        how="left"  # some trucks may have no driver listed
    )
    n2 = len(df)
    unmatched_drivers = df["driver_age"].isnull().sum()
    print(f"  After → Drivers join: {n2:,}  ({unmatched_drivers} rows with no driver info)")

    # ── 3. → Routes ──────────────────────────────────────────────────────────
    route_cols = ["route_id", "origin_id", "destination_id", "distance", "average_hours"]
    df = df.merge(routes[route_cols], on="route_id", how="inner")
    n3 = len(df)
    print(f"  After → Routes join : {n3:,}  (dropped {n2-n3} unmatched)")

    # ── 4. → Routes Weather (daily avg) ──────────────────────────────────────
    daily_weather = aggregate_routes_weather_daily(routes_weather)
    df["_date_only"] = df["departure_date"].dt.normalize()
    df = df.merge(
        daily_weather,
        left_on=["route_id", "_date_only"],
        right_on=["route_id", "date_only"],
        how="left"
    )
    df.drop(columns=["date_only"], inplace=True, errors="ignore")
    n4 = len(df)
    weather_miss = df["weather_temp"].isnull().sum()
    print(f"  After → Weather join: {n4:,}  ({weather_miss} rows with no weather data)")

    # ── 5. → Traffic (hourly, departure hour) ────────────────────────────────
    traffic_clean = aggregate_traffic_departure(traffic)
    df["_dep_hour"] = df["departure_date"].dt.hour

    # Daily avg per route for fallback
    daily_traffic = (
        traffic_clean.groupby(["route_id", "date_only"], as_index=False)
        .agg(
            avg_no_of_vehicles=("no_of_vehicles", "mean"),
            daily_accident=("accident", "max"),
        )
    )

    # Hour-exact traffic
    traffic_hour = traffic_clean[["route_id", "date_only", "hour",
                                   "no_of_vehicles", "accident"]].copy()
    df = df.merge(
        traffic_hour.rename(columns={"hour": "_dep_hour", "date_only": "_date_only_t",
                                     "no_of_vehicles": "traffic_vehicles",
                                     "accident": "traffic_accident"}),
        left_on=["route_id", "_date_only", "_dep_hour"],
        right_on=["route_id", "_date_only_t", "_dep_hour"],
        how="left"
    )
    df.drop(columns=["_date_only_t"], inplace=True, errors="ignore")

    # Fallback: fill with daily average
    df = df.merge(
        daily_traffic.rename(columns={"date_only": "_date_only"}),
        on=["route_id", "_date_only"],
        how="left"
    )
    df["traffic_vehicles"] = df["traffic_vehicles"].fillna(df["avg_no_of_vehicles"])
    df["traffic_accident"] = df["traffic_accident"].fillna(df["daily_accident"])
    df.drop(columns=["avg_no_of_vehicles", "daily_accident"], inplace=True, errors="ignore")

    n5 = len(df)
    traffic_miss = df["traffic_vehicles"].isnull().sum()
    print(f"  After → Traffic join: {n5:,}  ({traffic_miss} rows with no traffic data)")

    # ── 6. Static feature engineering ────────────────────────────────────────
    df = add_time_features(df)
    df = add_truck_features(df)

    # Clean up temporary columns
    for col in ["_date_only", "_dep_hour", "departure_date_only", "departure_hour"]:
        df.drop(columns=[col], inplace=True, errors="ignore")

    print(f"\n  Final feature table: {len(df):,} rows x {len(df.columns)} cols")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    # Quick smoke test
    from data_preprocessing import load_all
    tables = load_all()
    df = build_feature_table(
        tables["schedule"], tables["trucks"], tables["drivers"],
        tables["routes"], tables["routes_weather"], tables["traffic"]
    )
    print(f"\nFeature table shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\ndelay distribution:\n{df['delay'].value_counts()}")
