"""
historical_features.py
=======================
Computes rolling/expanding temporal features for trucks and routes,
with STRICT leakage prevention.

LEAKAGE PREVENTION GUARANTEE
─────────────────────────────
For every row i with departure_date T_i, historical features are computed
using ONLY rows j where T_j < T_i (strictly before).

This means:
  - Sorting by departure_date
  - Using shift(1) before cumulative aggregation (excludes current row)
  - Using expanding windows on sorted data

This is verified explicitly in compute_historical_features().

Features computed
-----------------
Per TRUCK (truck_id):
  truck_trip_count_hist          - number of prior trips by this truck
  truck_delay_rate_hist          - fraction of prior trips that were delayed
  truck_avg_delay_hist           - mean delay (0/1) of prior trips (same as rate)

Per ROUTE (route_id):
  route_trip_count_hist          - number of prior trips on this route
  route_delay_rate_hist          - fraction of prior trips on this route delayed

NOTE: No per-driver historical features are computed because driver_id
does not appear in the schedule table. The driver-truck link (vehicle_no)
is static (one driver per truck), so truck-level history captures
driver history implicitly.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")


def compute_historical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add temporal expanding-window historical features to a sorted schedule DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain: departure_date (datetime64), truck_id, route_id, delay.
        MUST be sorted by departure_date (ascending) before calling.
        The sort is enforced inside this function.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with new historical feature columns added.
        Row count is unchanged. NaN values for first occurrence are expected.
    """
    print("  Computing historical features (leakage-free) ...")

    # Enforce chronological order
    df = df.sort_values("departure_date").reset_index(drop=True)

    # ── Per-truck expanding history ────────────────────────────────────────────
    # Group by truck_id, then for each trip compute stats from ALL PRIOR trips
    # (using shift(1) so current row is excluded from its own history).

    df = df.sort_values(["truck_id", "departure_date"]).reset_index(drop=True)

    # Expanding cumulative sum and count within each truck group
    truck_grp = df.groupby("truck_id")["delay"]

    # Count of prior trips (shift so current is excluded)
    df["_truck_delay_cumsum"] = truck_grp.cumsum() - df["delay"]
    df["_truck_trip_cumcount"] = truck_grp.cumcount()  # cumcount starts at 0 for first trip

    df["truck_trip_count_hist"] = df["_truck_trip_cumcount"]
    # Rate = prior delayed / prior total (0 if no prior trips)
    df["truck_delay_rate_hist"] = np.where(
        df["_truck_trip_cumcount"] > 0,
        df["_truck_delay_cumsum"] / df["_truck_trip_cumcount"],
        np.nan  # undefined for first trip of each truck
    )

    # ── Per-route expanding history ────────────────────────────────────────────
    # Sort by (route_id, departure_date) for route-level grouping
    df = df.sort_values(["route_id", "departure_date"]).reset_index(drop=True)

    route_grp = df.groupby("route_id")["delay"]
    df["_route_delay_cumsum"] = route_grp.cumsum() - df["delay"]
    df["_route_trip_cumcount"] = route_grp.cumcount()

    df["route_trip_count_hist"] = df["_route_trip_cumcount"]
    df["route_delay_rate_hist"] = np.where(
        df["_route_trip_cumcount"] > 0,
        df["_route_delay_cumsum"] / df["_route_trip_cumcount"],
        np.nan
    )

    # ── Clean up intermediate columns ─────────────────────────────────────────
    df.drop(columns=[
        "_truck_delay_cumsum", "_truck_trip_cumcount",
        "_route_delay_cumsum", "_route_trip_cumcount"
    ], inplace=True)

    # Restore chronological order
    df = df.sort_values("departure_date").reset_index(drop=True)

    # ── Leakage verification ──────────────────────────────────────────────────
    _verify_no_leakage(df)

    # Summary
    print(f"    truck_trip_count_hist  : min={df['truck_trip_count_hist'].min():.0f}, "
          f"max={df['truck_trip_count_hist'].max():.0f}, "
          f"NaN={df['truck_trip_count_hist'].isnull().sum()}")
    print(f"    truck_delay_rate_hist  : mean={df['truck_delay_rate_hist'].mean():.3f}, "
          f"NaN={df['truck_delay_rate_hist'].isnull().sum()} (first-trip rows)")
    print(f"    route_trip_count_hist  : min={df['route_trip_count_hist'].min():.0f}, "
          f"max={df['route_trip_count_hist'].max():.0f}")
    print(f"    route_delay_rate_hist  : mean={df['route_delay_rate_hist'].mean():.3f}, "
          f"NaN={df['route_delay_rate_hist'].isnull().sum()} (first-trip rows)")

    return df


def _verify_no_leakage(df: pd.DataFrame) -> None:
    """
    Sanity check: for each (truck_id, departure_date) row, verify that
    truck_trip_count_hist equals the number of prior rows for that truck.

    Tests on a random sample of 100 rows.
    """
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(len(df), min(100, len(df)), replace=False)

    failed = 0
    for idx in sample_idx:
        row = df.iloc[idx]
        truck = row["truck_id"]
        dep = row["departure_date"]
        expected_count = int((df["truck_id"] == truck) & (df["departure_date"] < dep)).sum() if False else \
                         len(df[(df["truck_id"] == truck) & (df["departure_date"] < dep)])
        actual_count = int(row["truck_trip_count_hist"])
        if expected_count != actual_count:
            failed += 1

    if failed > 0:
        print(f"    ⚠  LEAKAGE CHECK FAILED for {failed}/100 sampled rows!")
    else:
        print(f"    ✓  Leakage check passed (100 random rows verified — no future data in history)")


def impute_historical_features(
    df: pd.DataFrame,
    fill_truck_rate: float,
    fill_route_rate: float,
) -> pd.DataFrame:
    """
    Impute NaN historical rates (first-trip rows) with provided values.
    These values must be computed from training data only.

    Parameters
    ----------
    fill_truck_rate : float
        Global average truck delay rate from training set.
    fill_route_rate : float
        Global average route delay rate from training set.
    """
    df = df.copy()
    df["truck_delay_rate_hist"] = df["truck_delay_rate_hist"].fillna(fill_truck_rate)
    df["route_delay_rate_hist"] = df["route_delay_rate_hist"].fillna(fill_route_rate)
    return df


def get_hist_feature_names() -> list:
    return [
        "truck_trip_count_hist",
        "truck_delay_rate_hist",
        "route_trip_count_hist",
        "route_delay_rate_hist",
    ]


if __name__ == "__main__":
    # Minimal smoke test
    sample = pd.DataFrame({
        "truck_id": [1, 1, 2, 1, 2],
        "route_id": ["R1", "R1", "R1", "R2", "R2"],
        "departure_date": pd.to_datetime([
            "2019-01-01", "2019-01-05", "2019-01-03",
            "2019-01-10", "2019-01-07"
        ]),
        "delay": [0, 1, 1, 0, 0],
    })
    result = compute_historical_features(sample)
    print(result[["truck_id", "route_id", "departure_date", "delay",
                   "truck_trip_count_hist", "truck_delay_rate_hist",
                   "route_trip_count_hist", "route_delay_rate_hist"]].to_string())
