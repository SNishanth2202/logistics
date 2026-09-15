"""
data_loader.py
==============
Responsible for loading the raw LaDe delivery CSV and performing
type-safe timestamp parsing. All downstream modules consume the
DataFrame returned by load_raw().

Dataset: LaDe Shanghai delivery dataset
Columns discovered via inspection (2026-09):
  order_id, region_id, city, courier_id,
  lng, lat,                            <- delivery DESTINATION GPS
  aoi_id, aoi_type,
  accept_time, accept_gps_time,        <- MM-DD HH:MM:SS strings (year=2023)
  accept_gps_lng, accept_gps_lat,      <- courier position at accept
  delivery_time, delivery_gps_time,    <- MM-DD HH:MM:SS strings
  delivery_gps_lng, delivery_gps_lat,  <- courier position at delivery complete
  ds                                   <- MMDD integer (e.g. 604 = June 4)
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# The LaDe dataset covers 2023.  Timestamps are stored without a year.
DATASET_YEAR = 2023

# Timestamp columns that need year-prefix injection before parsing
_TIMESTAMP_COLS = [
    "accept_time",
    "accept_gps_time",
    "delivery_time",
    "delivery_gps_time",
]

_TS_FORMAT = f"%Y-%m-%d %H:%M:%S"


def _parse_timestamp_col(series: pd.Series) -> pd.Series:
    """Prepend the dataset year and parse to datetime64[ns]."""
    prefixed = f"{DATASET_YEAR}-" + series.astype(str)
    return pd.to_datetime(prefixed, format=_TS_FORMAT, errors="coerce")


def load_raw(csv_path: str | Path, *, verbose: bool = True) -> pd.DataFrame:
    """
    Load the raw delivery CSV, parse timestamps, and return a typed DataFrame.

    Parameters
    ----------
    csv_path : str or Path
        Absolute path to delivery_sh.csv.
    verbose : bool
        If True, print a concise summary after loading.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with datetime columns added (_dt suffix).
        Original string timestamp columns are retained for debugging.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    logger.info("Loading %s ...", csv_path)
    df = pd.read_csv(
        csv_path,
        dtype={
            "order_id": "int64",
            "region_id": "int16",
            "city": "category",
            "courier_id": "int32",
            "aoi_id": "int32",
            "aoi_type": "int8",
            "ds": "int32",
        },
    )

    # Parse all four timestamp columns
    for col in _TIMESTAMP_COLS:
        dt_col = f"{col}_dt"
        df[dt_col] = _parse_timestamp_col(df[col])
        n_failed = df[dt_col].isna().sum()
        if n_failed > 0:
            logger.warning("  %d rows failed timestamp parse in '%s'", n_failed, col)

    if verbose:
        _print_summary(df)

    return df


def _print_summary(df: pd.DataFrame) -> None:
    """Print a concise dataset summary to stdout."""
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"  Rows              : {len(df):,}")
    print(f"  Columns           : {len(df.columns)}")
    print(f"  Unique couriers   : {df['courier_id'].nunique():,}")
    print(f"  Unique regions    : {df['region_id'].nunique()}")
    print(f"  Unique AOIs       : {df['aoi_id'].nunique()}")
    print()
    print(f"  accept_time range :")
    print(f"    {df['accept_time_dt'].min()}  ->  {df['accept_time_dt'].max()}")
    print("  delivery_time range:")
    print(f"    {df['delivery_time_dt'].min()}  ->  {df['delivery_time_dt'].max()}")
    print()
    print("  Missing values per column:")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("    (none)")
    else:
        for col, cnt in missing.items():
            print(f"    {col}: {cnt:,}")
    print()
    print("  Duplicated rows   :", df.duplicated().sum())
    print("=" * 60)
