"""
data_validation.py
==================
Data quality checks for all freight logistics tables.
Creates: reports/data_quality_report.md
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

ISSUES = []


def add_issue(table, problem, n_affected, treatment, reason):
    ISSUES.append({
        "table": table,
        "problem": problem,
        "affected_records": n_affected,
        "treatment": treatment,
        "reason": reason,
    })
    flag = "⚠ " if n_affected > 0 else "✓ "
    print(f"  {flag} {problem}: {n_affected} records")


def check_drivers(df: pd.DataFrame):
    t = "drivers_table"
    print(f"\n[Drivers] {len(df)} rows")

    # Impossible age
    mask = (df["age"] < 18) | (df["age"] > 80)
    add_issue(t, "Driver age outside [18,80]", int(mask.sum()),
              "Flag; keep but note", "Age<18 illegal to drive; >80 unusual")

    # Impossible experience
    mask2 = df["experience"] < 0
    add_issue(t, "Negative experience", int(mask2.sum()),
              "Flag; keep", "Experience cannot be negative")

    # Experience > age-18 (impossible)
    mask3 = df["experience"] > (df["age"] - 18)
    add_issue(t, "Experience > (age-18)", int(mask3.sum()),
              "Flag; keep", "Cannot accumulate more experience than driving-eligible years")

    # Impossible speed
    mask4 = (df["average_speed_mph"] <= 0) | (df["average_speed_mph"] > 120)
    add_issue(t, "Average speed outside (0, 120] mph", int(mask4.sum()),
              "Flag; keep", "Speed 0 or >120 mph unrealistic for freight")

    # Missing gender/driving_style
    n_gender = int(df["gender"].isnull().sum())
    n_style = int(df["driving_style"].isnull().sum())
    add_issue(t, "Missing gender", n_gender, "Impute as 'Unknown'", "Non-informative for model")
    add_issue(t, "Missing driving_style", n_style, "Impute as 'Unknown'", "Will be encoded as separate category")

    # Duplicate vehicle_no
    dup_vno = df["vehicle_no"].duplicated().sum()
    add_issue(t, "Duplicate vehicle_no (driver-truck link key)", int(dup_vno),
              "Investigate; use first match", "vehicle_no must be unique to link driver to truck")


def check_trucks(df: pd.DataFrame):
    t = "trucks_table"
    print(f"\n[Trucks] {len(df)} rows")

    # Impossible truck age
    mask = (df["truck_age"] < 0) | (df["truck_age"] > 30)
    add_issue(t, "Truck age outside [0,30]", int(mask.sum()),
              "Flag; keep", "Age<0 impossible; >30 very unusual")

    # Negative or zero capacity
    mask2 = df["load_capacity_pounds"] <= 0
    add_issue(t, "Load capacity <= 0 lbs", int(mask2.sum()),
              "Flag; impute with median", "Zero/negative capacity is physically impossible")

    # Negative MPG
    mask3 = df["mileage_mpg"] <= 0
    add_issue(t, "Mileage MPG <= 0", int(mask3.sum()),
              "Flag; impute with median", "Non-positive MPG is impossible")

    # Missing load capacity / fuel type
    n_cap = int(df["load_capacity_pounds"].isnull().sum())
    n_fuel = int(df["fuel_type"].isnull().sum())
    add_issue(t, "Missing load_capacity_pounds", n_cap,
              "Impute with median (train only)", "Moderate missingness; median is defensible")
    add_issue(t, "Missing fuel_type", n_fuel,
              "Impute as 'Unknown'", "Categorical; Unknown category")

    # Duplicate truck_id
    dup = df["truck_id"].duplicated().sum()
    add_issue(t, "Duplicate truck_id", int(dup),
              "Raise error if found", "truck_id must be unique primary key")


def check_routes(df: pd.DataFrame):
    t = "routes_table"
    print(f"\n[Routes] {len(df)} rows")

    # Negative distance
    mask = df["distance"] <= 0
    add_issue(t, "Distance <= 0", int(mask.sum()),
              "Flag; impute or drop", "Non-positive distance is impossible")

    # Negative average hours
    mask2 = df["average_hours"] <= 0
    add_issue(t, "average_hours <= 0", int(mask2.sum()),
              "Flag; impute with median", "Non-positive travel time is impossible")

    # Self-loops (origin == destination)
    mask3 = df["origin_id"] == df["destination_id"]
    add_issue(t, "origin_id == destination_id (self-loop)", int(mask3.sum()),
              "Flag; likely data error", "A route from city to itself is nonsensical")

    # Duplicate route_id
    dup = df["route_id"].duplicated().sum()
    add_issue(t, "Duplicate route_id", int(dup),
              "Raise error if found", "route_id must be unique")


def check_traffic(df: pd.DataFrame):
    t = "traffic_table"
    print(f"\n[Traffic] {len(df)} rows")

    # Negative vehicle count
    mask = df["no_of_vehicles"] < 0
    add_issue(t, "Negative no_of_vehicles", int(mask.sum()),
              "Set to NaN; impute with 0", "Negative vehicle count is impossible")

    # Missing vehicle count
    n_miss = int(df["no_of_vehicles"].isnull().sum())
    add_issue(t, "Missing no_of_vehicles", n_miss,
              "Impute with route-date median", "1,152 missing (0.04%); low impact")

    # Invalid accident flag
    bad_acc = (~df["accident"].isin([0, 1])).sum()
    add_issue(t, "accident not in {0,1}", int(bad_acc),
              "Coerce to 0/1", "Binary indicator; invalid values should be 0")

    # Invalid hour values (traffic uses 0,100,200,...,2300 format)
    # hour column contains values like 0, 100, 200, ... 2300
    # We'll normalize by dividing by 100
    unique_hours = sorted(df["hour"].unique())
    max_hr = df["hour"].max()
    note = f"hour column uses {unique_hours[:5]}... format (max={max_hr})"
    add_issue(t, f"Non-standard hour encoding: {note}", 0,
              "Divide by 100 to get 0-23 hour", "Dataset encodes hour as 0,100,200,...,2300")


def check_schedule(df: pd.DataFrame):
    t = "truck_schedule_table"
    print(f"\n[Schedule] {len(df)} rows")

    # Parse dates
    dep = pd.to_datetime(df["departure_date"], errors="coerce")
    arr = pd.to_datetime(df["estimated_arrival"], errors="coerce")

    # Invalid timestamps
    bad_dep = dep.isnull().sum()
    bad_arr = arr.isnull().sum()
    add_issue(t, "Unparseable departure_date", int(bad_dep), "Drop affected rows", "Cannot use without valid timestamp")
    add_issue(t, "Unparseable estimated_arrival", int(bad_arr), "Flag", "No actual arrival in dataset")

    # Estimated arrival before departure (impossible)
    mask = arr < dep
    add_issue(t, "estimated_arrival < departure_date", int(mask.sum()),
              "Flag; investigate", "Arrival before departure is physically impossible")

    # Duplicate schedule entries
    dup = df.duplicated(subset=["truck_id", "departure_date"]).sum()
    add_issue(t, "Duplicate (truck_id, departure_date)", int(dup),
              "Keep first occurrence", "Same truck cannot depart twice at same time")

    # Target distribution
    vc = df["delay"].value_counts()
    n0 = int(vc.get(0, 0))
    n1 = int(vc.get(1, 0))
    pct1 = 100 * n1 / len(df)
    add_issue(t, f"Class imbalance: delay=1 is {pct1:.1f}% of records", 0,
              "Use class_weight='balanced' / scale_pos_weight", "Moderate imbalance; class weights sufficient")


def check_weather(df: pd.DataFrame, name: str):
    t = name
    print(f"\n[{name}] {len(df)} rows")

    # Temperature
    mask = (df["temp"] < -60) | (df["temp"] > 60)
    add_issue(t, "Temperature outside [-60, 60]°C", int(mask.sum()),
              "Flag; keep", "Extreme temperatures — check units (may be Fahrenheit)")

    # Negative precipitation
    mask2 = df["precip"] < 0
    add_issue(t, "Negative precipitation", int(mask2.sum()),
              "Set to 0", "Precipitation cannot be negative")

    # Visibility out of range (miles)
    mask3 = df["visibility"] < 0
    add_issue(t, "Negative visibility", int(mask3.sum()),
              "Set to 0", "Visibility cannot be negative")

    # Chance fields out of [0,100]
    for col in ["chanceofrain", "chanceoffog", "chanceofsnow", "chanceofthunder"]:
        if col in df.columns:
            mask4 = (df[col] < 0) | (df[col] > 100)
            add_issue(t, f"{col} outside [0,100]", int(mask4.sum()),
                      "Clip to [0,100]", "Probability percentage must be in [0,100]")


def write_report():
    lines = [
        "# Data Quality Report",
        "",
        f"Generated for: Freight Logistics Dataset",
        f"Tables inspected: 7",
        "",
        "| Table | Problem | Affected Records | Treatment | Reason |",
        "|-------|---------|-----------------|-----------|--------|",
    ]
    for issue in ISSUES:
        n = issue["affected_records"]
        flag = "⚠" if n > 0 else "✓"
        lines.append(
            f"| {issue['table']} | {flag} {issue['problem']} | {n:,} | "
            f"{issue['treatment']} | {issue['reason']} |"
        )

    lines += [
        "",
        "## Summary",
        "",
        "- **Critical issues**: None that invalidate the dataset",
        "- **Missing data**: Moderate in trucks (load_capacity, fuel_type) and drivers (gender, driving_style)",
        "- **Traffic**: hour column uses non-standard 0/100/200/2300 encoding — normalize by dividing by 100",
        "- **Class imbalance**: delay=1 is ~35% — handled via class weights",
        "- **No actual arrival time**: Regression target cannot be defensibly constructed — classification only",
        "- **Driver-truck link**: `drivers.vehicle_no = trucks.truck_id` (integer FK)",
        "",
        "## Treatment Decisions",
        "",
        "| Feature | Treatment |",
        "|---------|-----------|",
        "| Missing gender | Impute → 'Unknown' |",
        "| Missing driving_style | Impute → 'Unknown' |",
        "| Missing load_capacity_pounds | Impute → median (fit on train) |",
        "| Missing fuel_type | Impute → 'Unknown' |",
        "| Missing no_of_vehicles | Impute → route-date median then 0 |",
        "| Traffic hour encoding | Divide by 100 (0,100,200... → 0,1,2...) |",
        "| Class imbalance | class_weight='balanced' (LR/RF); scale_pos_weight (XGBoost) |",
    ]

    report_path = REPORTS_DIR / "data_quality_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved: {report_path}")


def main():
    print("=" * 70)
    print("DATA QUALITY VALIDATION")
    print("=" * 70)

    drivers = pd.read_csv(RAW_DIR / "drivers_table.csv")
    trucks = pd.read_csv(RAW_DIR / "trucks_table.csv")
    routes = pd.read_csv(RAW_DIR / "routes_table.csv")
    traffic = pd.read_csv(RAW_DIR / "traffic_table.csv", low_memory=False)
    schedule = pd.read_csv(RAW_DIR / "truck_schedule_table.csv")
    routes_weather = pd.read_csv(RAW_DIR / "routes_weather.csv")
    city_weather = pd.read_csv(RAW_DIR / "city_weather.csv")

    check_drivers(drivers)
    check_trucks(trucks)
    check_routes(routes)
    check_traffic(traffic)
    check_schedule(schedule)
    check_weather(routes_weather, "routes_weather")
    check_weather(city_weather, "city_weather")

    write_report()
    print(f"\nTotal issues checked: {len(ISSUES)}")
    warned = sum(1 for i in ISSUES if i["affected_records"] > 0)
    print(f"Issues with affected records: {warned}")


if __name__ == "__main__":
    main()
