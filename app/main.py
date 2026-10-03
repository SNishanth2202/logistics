"""
app/main.py
===========
FastAPI app for real-time freight delay prediction and freight matching.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import warnings
import sys
from pathlib import Path
import xgboost as xgb
import joblib
import json
from scipy.optimize import linear_sum_assignment

warnings.filterwarnings("ignore")
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from data_preprocessing import load_all
from feature_engineering import build_feature_table
from predict import predict as predict_delay

app = FastAPI(title="Logistics AI Platform")

# --- Load artifacts globally for fast inference ---
MODELS_DIR = BASE_DIR / "logistics-ai" / "models"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Matching artifacts
try:
    m_model = xgb.Booster()
    m_model.load_model(MODELS_DIR / "matching_xgboost.json")
    m_prep = joblib.load(MODELS_DIR / "matching_preprocessor.pkl")
    with open(MODELS_DIR / "matching_features.json") as f:
        m_spec = json.load(f)
        
    # Imputations
    with open(PROCESSED_DIR / "imputation_medians.json") as f:
        phase1_medians = json.load(f)
        
    # Delay artifacts
    p1_model = joblib.load(MODELS_DIR / "delay_xgboost.pkl")
    p1_prep = joblib.load(MODELS_DIR / "preprocessor.pkl")
    with open(MODELS_DIR / "feature_columns.json") as f:
        p1_spec = json.load(f)
        
except Exception as e:
    print(f"Warning: Model artifacts not found. {e}")

# Preload static tables (in a real app, this would be queried from DB)
try:
    tables = load_all()
except Exception as e:
    tables = {}
    print(f"Warning: Static tables not found. {e}")

# Models for request payloads
class DelayRequest(BaseModel):
    record: Dict[str, Any]
    
class Load(BaseModel):
    load_id: str
    route_id: str
    departure_date: str
    load_weight_pounds: float
    
class MatchRequest(BaseModel):
    loads: List[Load]
    available_truck_ids: List[int]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/delay")
def predict_delay_endpoint(request: DelayRequest):
    """Phase 1: Predict delay probability for a single shipment"""
    try:
        result = predict_delay(request.record)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match")
def predict_match_endpoint(request: MatchRequest):
    """Phase 2: Freight Matching API"""
    if not tables:
        raise HTTPException(status_code=500, detail="Static tables not loaded")
        
    if not request.loads or not request.available_truck_ids:
        return {"assignments": []}
        
    try:
        loads_df = pd.DataFrame([l.dict() for l in request.loads])
        loads_df["departure_date"] = pd.to_datetime(loads_df["departure_date"])
        
        # 1. Expand pairs
        records = []
        for _, l in loads_df.iterrows():
            for t in request.available_truck_ids:
                row = l.to_dict()
                row["truck_id"] = t
                records.append(row)
                
        df_pairs = pd.DataFrame(records)
        
        # 2. Build Features
        df_features = build_feature_table(
            df_pairs,
            tables["trucks"],
            tables["drivers"],
            tables["routes"],
            tables["routes_weather"],
            tables["traffic"]
        )
        
        # 3. Impute Historical
        global_rate = phase1_medians.get("truck_delay_rate_hist", 0.349)
        df_features["truck_delay_rate_hist"] = global_rate
        df_features["route_delay_rate_hist"] = global_rate
        df_features["truck_trip_count_hist"] = 0
        df_features["route_trip_count_hist"] = 0
        
        # 4. Predict delay_prob
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
        
        # 5. Matching features
        df_features["capacity_utilization"] = df_features["load_weight_pounds"] / df_features["load_capacity_pounds"]
        df_features["is_overweight"] = (df_features["capacity_utilization"] > 1.0).astype(int)
        
        # 6. Predict Match Score
        X_m = df_features.copy()
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
        
        score_matrix = np.zeros((len(load_ids), len(truck_ids)))
        for i, l_id in enumerate(load_ids):
            for j, t_id in enumerate(truck_ids):
                score = df_features[(df_features["load_id"] == l_id) & (df_features["truck_id"] == t_id)]["score"].values[0]
                score_matrix[i, j] = score
                
        row_ind, col_ind = linear_sum_assignment(score_matrix, maximize=True)
        
        assignments = []
        for i, j in zip(row_ind, col_ind):
            l_id = load_ids[i]
            t_id = truck_ids[j]
            row = df_features[(df_features["load_id"] == l_id) & (df_features["truck_id"] == t_id)].iloc[0]
            
            assignments.append({
                "load_id": l_id,
                "truck_id": int(t_id),
                "match_score": float(row["score"]),
                "delay_probability": float(row["delay_prob"]),
                "route_id": row["route_id"],
                "distance": float(row["distance"]),
                "capacity_utilization": float(row["capacity_utilization"])
            })
            
        return {"assignments": assignments}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
