"""
assign.py
=========
Inference script for freight matching.
Takes loads and available trucks, predicts matching scores for all pairs,
and uses the Hungarian algorithm to find the globally optimal 1:1 assignment.
"""

import pandas as pd
import numpy as np
import joblib
import json
import xgboost as xgb
from scipy.optimize import linear_sum_assignment
from pathlib import Path
import sys
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "src" / "matching"))

from build_matching_dataset import load_phase1_artifacts
from data_preprocessing import load_all
from feature_engineering import build_feature_table

MODELS_DIR = BASE_DIR / "logistics-ai" / "models"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def load_matching_artifacts():
    model = xgb.Booster()
    model.load_model(MODELS_DIR / "matching_xgboost.json")
    preprocessor = joblib.load(MODELS_DIR / "matching_preprocessor.pkl")
    with open(MODELS_DIR / "matching_features.json") as f:
        col_spec = json.load(f)
    return model, preprocessor, col_spec

def optimize_assignments(score_matrix, load_ids, truck_ids):
    """
    Hungarian algorithm for optimal 1:1 matching.
    score_matrix: array of shape (n_loads, n_trucks) containing match scores.
    """
    print("Running Hungarian assignment algorithm...")
    # scipy's linear_sum_assignment minimizes cost. 
    # To maximize score, we pass maximize=True
    row_ind, col_ind = linear_sum_assignment(score_matrix, maximize=True)
    
    assignments = []
    for i, j in zip(row_ind, col_ind):
        assignments.append({
            "load_id": load_ids[i],
            "truck_id": truck_ids[j],
            "score": float(score_matrix[i, j])
        })
    return assignments

def main():
    # Example scenario: 5 loads, 10 available trucks
    # In a real app, this would be passed dynamically
    tables = load_all()
    schedule = tables["schedule"]
    trucks = tables["trucks"]
    
    # Take a few recent loads
    loads = schedule.sort_values("departure_date", ascending=False).head(5).copy()
    loads["load_id"] = [f"NEW_L{i}" for i in range(len(loads))]
    
    # Take 10 available trucks
    available_truck_ids = trucks["truck_id"].sample(10, random_state=42).tolist()
    
    print("\n" + "="*50)
    print("MATCHING INFERENCE SIMULATION")
    print("="*50)
    print(f"Loads to assign: {len(loads)}")
    print(f"Available trucks: {len(available_truck_ids)}")
    
    # 1. Expand pairs
    records = []
    for _, l in loads.iterrows():
        for t in available_truck_ids:
            row = l.to_dict()
            row["truck_id"] = t
            records.append(row)
            
    df_pairs = pd.DataFrame(records)
    
    # 2. Extract features for all pairs
    print("\nBuilding features for all pairs...")
    df_features = build_feature_table(
        df_pairs,
        tables["trucks"],
        tables["drivers"],
        tables["routes"],
        tables["routes_weather"],
        tables["traffic"]
    )
    
    # 3. Impute Historical Features (use training medians for new/current queries)
    with open(PROCESSED_DIR / "imputation_medians.json") as f:
        phase1_medians = json.load(f)
        
    global_rate = phase1_medians.get("truck_delay_rate_hist", 0.349)
    # Actually, we should look up their real historical state, but for this simulation:
    df_features["truck_delay_rate_hist"] = global_rate
    df_features["route_delay_rate_hist"] = global_rate
    df_features["truck_trip_count_hist"] = 0
    df_features["route_trip_count_hist"] = 0
    
    # 4. Predict Phase 1 delay_prob
    p1_model, p1_prep, p1_spec = load_phase1_artifacts()
    
    X_p1 = df_features.copy()
    for c in p1_spec["numeric_features"]:
        if c in phase1_medians and c in X_p1.columns:
            X_p1[c] = X_p1[c].fillna(phase1_medians[c])
    for c in p1_spec["categorical_features"]:
        if c in X_p1.columns:
            X_p1[c] = X_p1[c].fillna("Unknown").astype(str)
            
    for c in p1_spec["numeric_features"] + p1_spec["categorical_features"]:
        if c not in X_p1.columns:
            X_p1[c] = 0
            
    X = p1_prep.transform(X_p1[p1_spec["numeric_features"] + p1_spec["categorical_features"]])
    df_features["delay_prob"] = p1_model.predict_proba(X)[:, 1]
    
    # 5. Matching Features
    rng = np.random.default_rng(42)
    # mock load_weight
    df_features["load_weight_pounds"] = df_features["load_capacity_pounds"] * rng.uniform(0.5, 0.9, size=len(df_features))
    df_features["capacity_utilization"] = df_features["load_weight_pounds"] / df_features["load_capacity_pounds"]
    df_features["is_overweight"] = (df_features["capacity_utilization"] > 1.0).astype(int)
    
    # 6. Predict Match Score
    m_model, m_prep, m_spec = load_matching_artifacts()
    X_m = df_features.copy()
    
    # Impute for matching model
    for c in m_spec["numeric"]:
        if c in phase1_medians and c in X_m.columns:
            X_m[c] = X_m[c].fillna(phase1_medians[c])
    for c in m_spec["categorical"]:
        if c in X_m.columns:
            X_m[c] = X_m[c].fillna("Unknown").astype(str)
            
    X_trans = m_prep.transform(X_m[m_spec["numeric"] + m_spec["categorical"]])
    dtest = xgb.DMatrix(X_trans)
    df_features["score"] = m_model.predict(dtest)
    
    # 7. Assignment
    load_ids = df_features["load_id"].unique()
    truck_ids = df_features["truck_id"].unique()
    
    # Build score matrix (loads x trucks)
    score_matrix = np.zeros((len(load_ids), len(truck_ids)))
    
    for i, l_id in enumerate(load_ids):
        for j, t_id in enumerate(truck_ids):
            # find score
            score = df_features[(df_features["load_id"] == l_id) & (df_features["truck_id"] == t_id)]["score"].values[0]
            score_matrix[i, j] = score
            
    assignments = optimize_assignments(score_matrix, load_ids, truck_ids)
    
    print("\nFINAL ASSIGNMENTS:")
    for a in assignments:
        row = df_features[(df_features["load_id"] == a["load_id"]) & (df_features["truck_id"] == a["truck_id"])].iloc[0]
        print(f"  Load {a['load_id']} -> Truck {a['truck_id']}")
        print(f"      Score: {a['score']:.4f} | Delay Prob: {row['delay_prob']:.1%} | Route: {row['route_id']}")
        
if __name__ == "__main__":
    main()
