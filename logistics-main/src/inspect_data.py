"""
inspect_data.py
===============
Automatically inspects all CSV files in data/raw/ and produces:
  reports/dataset_inventory.csv
  reports/dataset_inventory.txt
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def inspect_csv(path: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path, low_memory=False)
    info = {
        "file": path.name,
        "rows": len(df),
        "cols": len(df.columns),
        "columns": ", ".join(df.columns.tolist()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    # Missing values per column
    miss = df.isnull().sum()
    miss_dict = {c: int(v) for c, v in miss.items() if v > 0}
    info["missing_values"] = str(miss_dict) if miss_dict else "None"
    info["total_missing"] = int(miss.sum())

    # Date ranges
    date_info = []
    for col in df.columns:
        if "date" in col.lower():
            try:
                d = pd.to_datetime(df[col], errors="coerce")
                date_info.append(f"{col}: {d.min()} -> {d.max()}")
            except Exception:
                pass
    info["date_ranges"] = " | ".join(date_info) if date_info else "N/A"

    # Unique ID counts
    id_info = []
    for col in df.columns:
        if col.endswith("_id") or col == "truck_id":
            id_info.append(f"{col}: {df[col].nunique()}")
    info["unique_ids"] = " | ".join(id_info) if id_info else "N/A"

    # dtypes summary
    dtype_summary = {c: str(t) for c, t in df.dtypes.items()}
    info["dtypes"] = str(dtype_summary)

    return df, info


def build_report(all_info: list[dict]) -> None:
    # Save CSV
    inv_df = pd.DataFrame(all_info)
    csv_path = REPORTS_DIR / "dataset_inventory.csv"
    inv_df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    # Save TXT (human-readable)
    txt_path = REPORTS_DIR / "dataset_inventory.txt"
    lines = ["=" * 80, "DATASET INVENTORY REPORT", "=" * 80, ""]
    for info in all_info:
        lines.append(f"FILE: {info['file']}")
        lines.append(f"  Rows              : {info['rows']:,}")
        lines.append(f"  Columns           : {info['cols']}")
        lines.append(f"  Column names      : {info['columns']}")
        lines.append(f"  Duplicate rows    : {info['duplicate_rows']}")
        lines.append(f"  Total missing     : {info['total_missing']}")
        lines.append(f"  Missing by col    : {info['missing_values']}")
        lines.append(f"  Date ranges       : {info['date_ranges']}")
        lines.append(f"  Unique IDs        : {info['unique_ids']}")
        lines.append("")
    txt_path.write_text("\n".join(lines))
    print(f"Saved: {txt_path}")


def run_target_analysis(schedule_df: pd.DataFrame) -> None:
    """Analyse the delay target variable and print findings."""
    print("\n" + "=" * 60)
    print("TARGET VARIABLE ANALYSIS: delay")
    print("=" * 60)
    col = schedule_df["delay"]
    print(f"  dtype           : {col.dtype}")
    print(f"  unique values   : {sorted(col.unique().tolist())}")
    print(f"  min             : {col.min()}")
    print(f"  max             : {col.max()}")
    print(f"  value counts    :")
    vc = col.value_counts().sort_index()
    for val, cnt in vc.items():
        pct = 100 * cnt / len(col)
        print(f"    {val} -> {cnt:,}  ({pct:.1f}%)")
    print(f"  null values     : {col.isnull().sum()}")
    print("\n  CONCLUSION: delay is a binary integer (0=on-time, 1=delayed).")
    print("  Primary ML problem: DELAY CLASSIFICATION.")
    print("  No actual arrival time exists -> regression target NOT defensible.")


def main():
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

    print(f"Found {len(csv_files)} CSV files in {RAW_DIR}\n")
    all_info = []
    schedule_df = None

    for path in csv_files:
        print(f"Inspecting: {path.name} ...", end=" ")
        df, info = inspect_csv(path)
        all_info.append(info)
        print(f"{info['rows']:,} rows x {info['cols']} cols")

        # Print sample
        print(f"  Sample row:\n  {df.head(1).to_dict(orient='records')[0]}\n")

        if "truck_schedule" in path.name:
            schedule_df = df

    build_report(all_info)

    if schedule_df is not None:
        run_target_analysis(schedule_df)


if __name__ == "__main__":
    main()
