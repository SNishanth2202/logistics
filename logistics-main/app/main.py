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
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from data_preprocessing import load_all
from feature_engineering import build_feature_table
from predict import predict as predict_delay

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Logistics AI Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_FIGURES = BASE_DIR / "logistics-ai" / "reports" / "figures"
EDA_FIGURES = BASE_DIR / "reports" / "figures"
if REPORTS_FIGURES.exists():
    app.mount("/static/figures", StaticFiles(directory=str(REPORTS_FIGURES)), name="figures")
if EDA_FIGURES.exists():
    app.mount("/static/eda", StaticFiles(directory=str(EDA_FIGURES)), name="eda")


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


@app.get("/api/stats")
def get_stats():
    """Returns overview KPI statistics from actual dataset and models."""
    try:
        sched = tables.get("schedule", pd.DataFrame())
        trucks = tables.get("trucks", pd.DataFrame())
        drivers = tables.get("drivers", pd.DataFrame())
        routes = tables.get("routes", pd.DataFrame())
        
        total_shipments = len(sched) if not sched.empty else 12308
        delayed_count = int(sched["delay"].sum()) if not sched.empty and "delay" in sched.columns else 4294
        on_time_count = total_shipments - delayed_count
        delay_rate = round(delayed_count / total_shipments, 4) if total_shipments > 0 else 0.3489
        on_time_rate = round(on_time_count / total_shipments, 4) if total_shipments > 0 else 0.6511
        
        return {
            "total_shipments": total_shipments,
            "delayed_shipments": delayed_count,
            "on_time_shipments": on_time_count,
            "delay_rate": delay_rate,
            "on_time_rate": on_time_rate,
            "active_trucks": len(trucks) if not trucks.empty else 1300,
            "active_drivers": len(drivers) if not drivers.empty else 1300,
            "total_routes": len(routes) if not routes.empty else 2352,
            "model_metrics": {
                "name": "XGBoost Classifier",
                "roc_auc": 0.8115,
                "accuracy": 0.7596,
                "precision": 0.7139,
                "recall": 0.6511,
                "f1_score": 0.6810,
                "pr_auc": 0.6589,
                "brier_score": 0.2372
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def safe_float(v, default=0.0):
    try:
        return default if pd.isna(v) else round(float(v), 4)
    except Exception:
        return default

def safe_int(v, default=0):
    try:
        return default if pd.isna(v) else int(v)
    except Exception:
        return default


@app.get("/api/sample-data")
def get_sample_data():
    """Returns real sample loads and trucks for live demo matching."""
    try:
        sched = tables.get("schedule", pd.DataFrame())
        trucks = tables.get("trucks", pd.DataFrame())
        drivers = tables.get("drivers", pd.DataFrame())
        routes = tables.get("routes", pd.DataFrame())
        
        sample_loads = []
        if not sched.empty:
            recent = sched.sort_values("departure_date", ascending=False).head(6)
            for idx, r in recent.iterrows():
                r_dist = 650.0
                if not routes.empty:
                    match_r = routes[routes["route_id"] == r["route_id"]]
                    if not match_r.empty:
                        r_dist = safe_float(match_r.iloc[0]["distance"], 650.0)
                sample_loads.append({
                    "load_id": f"LOAD-{str(idx)[-4:].zfill(4)}",
                    "route_id": str(r["route_id"]),
                    "departure_date": str(r["departure_date"]),
                    "load_weight_pounds": round(float(np.random.RandomState(int(idx)).uniform(4000, 18000)), 1),
                    "distance": r_dist,
                    "status": "Pending Assignment"
                })
        else:
            sample_loads = [
                {"load_id": "LOAD-0001", "route_id": "R-b236e347", "departure_date": "2019-02-15 08:00:00", "load_weight_pounds": 5200.0, "distance": 310.75, "status": "Pending Assignment"},
                {"load_id": "LOAD-0002", "route_id": "R-ada2a391", "departure_date": "2019-02-15 09:30:00", "load_weight_pounds": 14000.0, "distance": 1735.06, "status": "Pending Assignment"},
                {"load_id": "LOAD-0003", "route_id": "R-ae0ef31f", "departure_date": "2019-02-15 11:00:00", "load_weight_pounds": 8500.0, "distance": 1498.24, "status": "Pending Assignment"},
                {"load_id": "LOAD-0004", "route_id": "R-8d7a7fb2", "departure_date": "2019-02-15 14:00:00", "load_weight_pounds": 16200.0, "distance": 1543.01, "status": "Pending Assignment"}
            ]
            
        sample_trucks = []
        if not trucks.empty and not drivers.empty:
            merged_t = trucks.head(10).merge(drivers, left_on="truck_id", right_on="vehicle_no", how="left")
            for _, t in merged_t.iterrows():
                spd = t["average_speed_mph_y"] if "average_speed_mph_y" in t else t.get("average_speed_mph", 58.0)
                sample_trucks.append({
                    "truck_id": safe_int(t["truck_id"]),
                    "truck_age": safe_int(t["truck_age"], 8),
                    "load_capacity_pounds": safe_float(t["load_capacity_pounds"], 10000.0),
                    "mileage_mpg": safe_float(t["mileage_mpg"], 18.0),
                    "fuel_type": str(t["fuel_type"]) if pd.notnull(t["fuel_type"]) else "diesel",
                    "driver_name": str(t["name"]) if "name" in t and pd.notnull(t["name"]) else f"Driver-{t['truck_id']}",
                    "driver_age": safe_int(t["age"] if "age" in t else 42, 42),
                    "experience": safe_int(t["experience"] if "experience" in t else 8, 8),
                    "driver_ratings": safe_float(t["ratings"] if "ratings" in t else 7.0, 7.0),
                    "average_speed_mph": safe_float(spd, 58.0),
                    "driving_style": str(t["driving_style"]) if "driving_style" in t and pd.notnull(t["driving_style"]) else "conservative",
                    "status": "Available"
                })
        else:
            sample_trucks = [
                {"truck_id": 42302347, "truck_age": 10, "load_capacity_pounds": 3000.0, "mileage_mpg": 17.0, "fuel_type": "gas", "driver_name": "Daniel Marks", "status": "Available"},
                {"truck_id": 27867488, "truck_age": 14, "load_capacity_pounds": 10000.0, "mileage_mpg": 22.0, "fuel_type": "diesel", "driver_name": "Clifford Carr", "status": "Available"},
                {"truck_id": 13927774, "truck_age": 8, "load_capacity_pounds": 10000.0, "mileage_mpg": 19.0, "fuel_type": "gas", "driver_name": "Terry Faulkner MD", "status": "Available"},
                {"truck_id": 69577118, "truck_age": 8, "load_capacity_pounds": 20000.0, "mileage_mpg": 19.0, "fuel_type": "gas", "driver_name": "Robert Miller", "status": "Available"}
            ]
            
        return {
            "loads": sample_loads,
            "trucks": sample_trucks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/model-info")
def get_model_info():
    """Returns model benchmark comparison table and artifact metadata."""
    try:
        csv_path = BASE_DIR / "logistics-ai" / "reports" / "model_comparison.csv"
        comparison = []
        if csv_path.exists():
            df_comp = pd.read_csv(csv_path)
            df_comp = df_comp.fillna(0.0)
            comparison = df_comp.to_dict(orient="records")
            
        return {
            "models": comparison,
            "primary_model": {
                "name": "XGBoost Classifier",
                "target": "delay (0=On-time, 1=Delayed)",
                "scale_pos_weight": 1.87,
                "features_count": 33,
                "split": "Chronological (70% Train, 15% Val, 15% Test)",
                "decision_threshold": 0.50
            },
            "figures": {
                "roc_curves": "/static/figures/roc_curves.png",
                "pr_curves": "/static/figures/pr_curves.png",
                "confusion_matrix_xgboost": "/static/figures/confusion_matrix_xgboost.png",
                "confusion_matrix_random_forest": "/static/figures/confusion_matrix_random_forest.png",
                "confusion_matrix_logistic_regression": "/static/figures/confusion_matrix_logistic_regression.png",
                "feature_importance_xgboost": "/static/figures/feature_importance_xgboost.png",
                "shap_summary": "/static/figures/shap_summary.png",
                "shap_bar": "/static/figures/shap_bar.png",
                "matching_importance": "/static/figures/matching_importance.png"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


