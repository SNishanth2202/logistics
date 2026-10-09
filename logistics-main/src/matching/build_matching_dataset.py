"""
build_matching_dataset.py
=========================
Generates the dataset for the Phase 2 Freight Matching Model.

Process:
1. Takes the true schedule as positive matches (match=1).
2. Generates N negative samples per load (match=0) using available trucks.
3. Expands the dataset to pairs (load, truck).
4. Runs Phase 1 feature engineering on the expanded dataset.
5. Injects historical features correctly (without leakage).
6. Uses the trained Phase 1 XGBoost model to predict `delay_prob` for all pairs.
7. Saves the resulting matching dataset.
"""

import pandas as pd
import numpy as np
import sys
import json
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from data_preprocessing import load_all
from feature_engineering import build_feature_table

PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "logistics-ai" / "models"
MATCHING_DIR = BASE_DIR / "data" / "processed" / "matching"
MATCHING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = MATCHING_DIR / "matching_dataset.csv"
RANDOM_SEED = 42

def load_phase1_artifacts():
    print("Loading Phase 1 artifacts for delay_prob inference...")
    model = joblib.load(MODELS_DIR / "delay_xgboost.pkl")
    preprocessor = joblib.load(MODELS_DIR / "preprocessor.pkl")
    with open(MODELS_DIR / "feature_columns.json") as f:
        col_spec = json.load(f)
    return model, preprocessor, col_spec

def get_truck_history(schedule: pd.DataFrame):
    """
    Computes a lookup table of truck historical stats before each departure date.
    Returns a dataframe of (truck_id, departure_date, count, rate).
    """
    df = schedule.copy().sort_values(["truck_id", "departure_date"]).reset_index(drop=True)
    truck_grp = df.groupby("truck_id")["delay"]
    
    df["_cumsum"] = truck_grp.cumsum() - df["delay"]
    df["_cumcount"] = truck_grp.cumcount()
    
    df["truck_trip_count_hist"] = df["_cumcount"]
    df["truck_delay_rate_hist"] = np.where(
        df["_cumcount"] > 0,
        df["_cumsum"] / df["_cumcount"],
        np.nan
    )
    # We only need to know this history AT each departure date
    return df[["truck_id", "departure_date", "truck_trip_count_hist", "truck_delay_rate_hist"]]

def get_route_history(schedule: pd.DataFrame):
    df = schedule.copy().sort_values(["route_id", "departure_date"]).reset_index(drop=True)
    route_grp = df.groupby("route_id")["delay"]
    df["_cumsum"] = route_grp.cumsum() - df["delay"]
    df["_cumcount"] = route_grp.cumcount()
    
    df["route_trip_count_hist"] = df["_cumcount"]
    df["route_delay_rate_hist"] = np.where(
        df["_cumcount"] > 0,
        df["_cumsum"] / df["_cumcount"],
        np.nan
    )
    return df[["route_id", "departure_date", "route_trip_count_hist", "route_delay_rate_hist"]]


def generate_negative_samples(schedule: pd.DataFrame, all_trucks: list, n_negatives: int = 4):
    """
    For each true trip, sample `n_negatives` trucks that didn't do this trip.
    """
    print(f"Generating {n_negatives} negative samples per load...")
    rng = np.random.default_rng(RANDOM_SEED)
    
    # Positive pairs
    positives = schedule.copy()
    positives["match"] = 1
    positives["load_id"] = ["L" + str(i).zfill(6) for i in range(len(positives))]
    
    records = []
    all_trucks = np.array(all_trucks)
    
    for idx, row in positives.iterrows():
        # Pos
        records.append(row.to_dict())
        
        # Neg
        true_truck = row["truck_id"]
        # In a real app we'd filter by available trucks at this timestamp.
        # For Phase 2, we randomly sample from all trucks to simulate candidate generation.
        candidates = all_trucks[all_trucks != true_truck]
        neg_trucks = rng.choice(candidates, size=n_negatives, replace=False)
        
        for nt in neg_trucks:
            neg_row = row.to_dict()
            neg_row["truck_id"] = nt
            neg_row["match"] = 0
            records.append(neg_row)
            
    df_expanded = pd.DataFrame(records)
    print(f"Expanded dataset: {len(df_expanded)} rows (1 pos + {n_negatives} neg per load)")
    return df_expanded


def main():
    print("=" * 60)
    print("BUILD MATCHING DATASET (PHASE 2)")
    print("=" * 60)
    
    # 1. Load data
    tables = load_all()
    schedule = tables["schedule"]
    trucks = tables["trucks"]
    all_truck_ids = trucks["truck_id"].unique().tolist()
    
    # 2. Extract historical features mapping from true schedule BEFORE negative sampling
    # We do asof merge later to avoid data leakage.
    truck_hist = get_truck_history(schedule).sort_values("departure_date")
    route_hist = get_route_history(schedule).sort_values("departure_date")
    
    # 3. Generate expanded dataset with negatives
    df_matching_spine = generate_negative_samples(schedule, all_truck_ids, n_negatives=4)
    
    # 4. Run Phase 1 Feature Engineering on the expanded spine
    # This joins truck, driver, route, weather, and traffic features
    df_features = build_feature_table(
        df_matching_spine,
        tables["trucks"],
        tables["drivers"],
        tables["routes"],
        tables["routes_weather"],
        tables["traffic"]
    )
    
    # 5. Inject historical features (using backward asof merge to prevent leakage)
    print("Injecting historical features...")
    df_features = df_features.sort_values("departure_date")
    
    # We need to map historical features from the true schedule to the expanded dataset
    # For route history, it's exact since route_id doesn't change for negatives
    df_features = pd.merge_asof(
        df_features, 
        route_hist, 
        on="departure_date", 
        by="route_id", 
        direction="backward"
    )
    
    # For truck history, negatives might not have exact timestamp matches in true schedule
    df_features = pd.merge_asof(
        df_features,
        truck_hist,
        on="departure_date",
        by="truck_id",
        direction="backward"
    )
    
    # Impute missing history (first trips)
    impute_json_path = PROCESSED_DIR / "imputation_medians.json"
    if impute_json_path.exists():
        with open(impute_json_path) as f:
            phase1_medians = json.load(f)
    else:
        phase1_medians = {}
        
    global_rate = phase1_medians.get("truck_delay_rate_hist", 0.349)
    df_features["truck_delay_rate_hist"] = df_features["truck_delay_rate_hist"].fillna(global_rate)
    df_features["route_delay_rate_hist"] = df_features["route_delay_rate_hist"].fillna(global_rate)
    df_features["truck_trip_count_hist"] = df_features["truck_trip_count_hist"].fillna(0)
    df_features["route_trip_count_hist"] = df_features["route_trip_count_hist"].fillna(0)
    
    # 6. Predict delay_prob using Phase 1 Model
    p1_model, p1_preprocessor, p1_col_spec = load_phase1_artifacts()
    
    print("Predicting delay_prob using Phase 1 model...")
    num_cols = p1_col_spec["numeric_features"]
    cat_cols = p1_col_spec["categorical_features"]
    
    # Impute remaining missing values for Phase 1 prediction
    X_df = df_features.copy()
    for c in num_cols:
        if c in phase1_medians and c in X_df.columns:
            X_df[c] = X_df[c].fillna(phase1_medians[c])
            
    for c in cat_cols:
        if c in X_df.columns:
            X_df[c] = X_df[c].fillna("Unknown").astype(str)
            
    # Keep only the columns expected by the preprocessor
    missing_cols = [c for c in num_cols + cat_cols if c not in X_df.columns]
    if missing_cols:
        print(f"Warning: Missing columns for Phase 1 predict: {missing_cols}")
        for c in missing_cols:
            X_df[c] = 0 # dummy fill
            
    X = p1_preprocessor.transform(X_df[num_cols + cat_cols])
    delay_probs = p1_model.predict_proba(X)[:, 1]
    
    df_features["delay_prob"] = delay_probs
    
    # 7. Add matching-specific features
    print("Adding matching-specific features...")
    # e.g. Capacity Utilization
    # load_capacity_pounds is truck's capacity. We don't have load weight in dataset yet.
    # Let's mock a load_weight for Phase 2 based on chosen truck's capacity
    
    # To avoid leakage, we'll assign load_weight based on the true truck's capacity * random factor (0.5 to 0.95)
    rng = np.random.default_rng(RANDOM_SEED)
    true_capacities = df_features[df_features["match"] == 1][["load_id", "load_capacity_pounds"]]
    true_capacities["load_weight_pounds"] = true_capacities["load_capacity_pounds"] * rng.uniform(0.5, 0.95, size=len(true_capacities))
    true_capacities = true_capacities.drop(columns=["load_capacity_pounds"])
    
    df_features = df_features.merge(true_capacities, on="load_id", how="left")
    df_features["capacity_utilization"] = df_features["load_weight_pounds"] / df_features["load_capacity_pounds"]
    # Handle trucks that are too small for the load (utilization > 1)
    df_features["is_overweight"] = (df_features["capacity_utilization"] > 1.0).astype(int)
    
    # 8. Select final columns and save
    keep_cols = [
        "load_id", "truck_id", "match", "departure_date", 
        "delay_prob", "capacity_utilization", "is_overweight",
        "distance", "average_hours"
    ] + num_cols + cat_cols
    
    # Deduplicate columns just in case
    keep_cols = list(dict.fromkeys(keep_cols))
    
    df_out = df_features[keep_cols].copy()
    df_out = df_out.sort_values(["load_id", "match"], ascending=[True, False]).reset_index(drop=True)
    
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved matching dataset to {OUTPUT_CSV}")
    print(f"Shape: {df_out.shape}")
    print(f"Match distribution:\n{df_out['match'].value_counts(normalize=True)}")

if __name__ == "__main__":
    main()
