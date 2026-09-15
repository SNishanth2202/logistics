"""
predict.py
==========
Inference script for freight delay classification.

Accepts a new shipment record and returns:
  {
    "delay_probability": 0.78,
    "predicted_class": 1
  }

Usage:
  python src/predict.py --example           # run with a built-in example
  python src/predict.py --json '{"truck_id": 12345, ...}'  # custom JSON input

Note: Regression target is NOT supported because no actual arrival time
exists in the source data. Only delay probability is returned.
"""
import json
import joblib
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "logistics-ai" / "models"

# ─── Load artifacts ───────────────────────────────────────────────────────────

def load_artifacts():
    """Load model, preprocessor, and feature column spec."""
    model_path = MODELS_DIR / "delay_xgboost.pkl"
    prep_path = MODELS_DIR / "preprocessor.pkl"
    cols_path = MODELS_DIR / "feature_columns.json"

    for p in [model_path, prep_path, cols_path]:
        if not p.exists():
            raise FileNotFoundError(
                f"Artifact not found: {p}\n"
                f"Run 'python src/train.py' first to generate model artifacts."
            )

    model = joblib.load(model_path)
    preprocessor = joblib.load(prep_path)
    with open(cols_path) as f:
        col_spec = json.load(f)

    return model, preprocessor, col_spec


# ─── Record validation ────────────────────────────────────────────────────────

def validate_and_fill(record: dict, col_spec: dict) -> pd.DataFrame:
    """
    Convert a raw input dict into a single-row DataFrame with the
    correct feature columns. Fill missing fields with sensible defaults.
    """
    numeric_features = col_spec["numeric_features"]
    categorical_features = col_spec["categorical_features"]

    # Defaults for missing fields (will also be imputed by preprocessor median)
    defaults = {
        # Time (derive from departure_date if provided)
        "hour": 7, "day_of_week": 0, "day_of_month": 1, "month": 1,
        "is_weekend": 0, "is_peak_hour": 1,
        # Truck
        "truck_age": None, "load_capacity_pounds": None, "mileage_mpg": None,
        "fuel_type": "Unknown",
        # Driver
        "driver_age": None, "experience": None, "driver_ratings": None,
        "average_speed_mph": None, "driving_style": "Unknown",
        # Route
        "distance": None, "average_hours": None,
        # Weather
        "weather_temp": 20, "weather_wind_speed": 10, "weather_precip": 0.0,
        "weather_humidity": 50, "weather_visibility": 10,
        "weather_chanceofrain": 0, "weather_chanceoffog": 0,
        "weather_chanceofsnow": 0, "weather_chanceofthunder": 0,
        # Traffic
        "traffic_vehicles": None, "traffic_accident": 0, "daily_accident_count": 0,
        # Truck derived
        "truck_age_category": "Unknown",
        # Historical
        "truck_trip_count_hist": 0, "truck_delay_rate_hist": None,
        "route_trip_count_hist": 0, "route_delay_rate_hist": None,
    }

    # If departure_date is provided, derive time features
    if "departure_date" in record:
        try:
            dt = pd.to_datetime(record["departure_date"])
            defaults["hour"] = dt.hour
            defaults["day_of_week"] = dt.dayofweek
            defaults["day_of_month"] = dt.day
            defaults["month"] = dt.month
            defaults["is_weekend"] = int(dt.dayofweek >= 5)
            defaults["is_peak_hour"] = int(dt.hour in [7, 8, 9, 17, 18, 19])
        except Exception:
            pass

    # Merge defaults with provided record
    merged = {**defaults, **record}

    # Build single-row DataFrame with the right columns
    all_cols = numeric_features + categorical_features
    row = {col: merged.get(col, np.nan) for col in all_cols}
    df = pd.DataFrame([row])

    return df


# ─── Predict ──────────────────────────────────────────────────────────────────

def predict(record: dict, threshold: float = 0.5) -> dict:
    """
    Generate delay probability and predicted class for a new delivery record.

    Parameters
    ----------
    record : dict
        Input features. Unknown fields are imputed by the preprocessor.
    threshold : float
        Decision threshold for predicted_class. Default 0.5.
        Consider lowering to 0.4 to increase recall for delayed deliveries.

    Returns
    -------
    dict
        {"delay_probability": float, "predicted_class": int}
    """
    model, preprocessor, col_spec = load_artifacts()

    df = validate_and_fill(record, col_spec)

    numeric_features = col_spec["numeric_features"]
    categorical_features = col_spec["categorical_features"]

    X = preprocessor.transform(df[numeric_features + categorical_features])
    prob = float(model.predict_proba(X)[0, 1])
    pred_class = int(prob >= threshold)

    return {
        "delay_probability": round(prob, 4),
        "predicted_class": pred_class,
    }


# ─── Example record ───────────────────────────────────────────────────────────

EXAMPLE_RECORD = {
    "departure_date": "2019-02-10 07:00:00",
    "truck_age": 8,
    "load_capacity_pounds": 20000.0,
    "mileage_mpg": 18,
    "fuel_type": "diesel",
    "driver_age": 42,
    "experience": 10,
    "driver_ratings": 7,
    "average_speed_mph": 58.5,
    "driving_style": "proactive",
    "distance": 1200.0,
    "average_hours": 24.0,
    "weather_temp": 28,
    "weather_wind_speed": 15,
    "weather_precip": 2.5,
    "weather_humidity": 75,
    "weather_visibility": 6,
    "weather_chanceofrain": 60,
    "weather_chanceoffog": 10,
    "weather_chanceofsnow": 0,
    "weather_chanceofthunder": 5,
    "traffic_vehicles": 850.0,
    "traffic_accident": 0,
    "daily_accident_count": 1,
    "truck_trip_count_hist": 15,
    "truck_delay_rate_hist": 0.35,
    "route_trip_count_hist": 50,
    "route_delay_rate_hist": 0.28,
}


def main():
    parser = argparse.ArgumentParser(description="Freight delay prediction")
    parser.add_argument("--example", action="store_true",
                        help="Run prediction on built-in example record")
    parser.add_argument("--json", type=str, default=None,
                        help="JSON string of input record")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Decision threshold (default 0.5)")
    args = parser.parse_args()

    if args.json:
        record = json.loads(args.json)
    elif args.example:
        record = EXAMPLE_RECORD
        print("Running example prediction:")
        print(json.dumps(record, indent=2))
    else:
        print("No input provided. Running built-in example:")
        record = EXAMPLE_RECORD

    result = predict(record, threshold=args.threshold)

    print("\n" + "=" * 40)
    print("PREDICTION RESULT")
    print("=" * 40)
    print(json.dumps(result, indent=2))
    label = "DELAYED" if result["predicted_class"] == 1 else "ON-TIME"
    print(f"\n  Decision: {label}  (threshold={args.threshold})")
    print(f"  Delay probability: {result['delay_probability']:.1%}")
    print("=" * 40)

    return result


if __name__ == "__main__":
    main()
