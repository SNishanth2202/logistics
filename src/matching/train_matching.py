"""
train_matching.py
=================
Trains the XGBoost Ranker for the freight matching model.
"""
import pandas as pd
import numpy as np
import joblib
import json
import time
import sys
from pathlib import Path
import warnings
import xgboost as xgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

MATCHING_DIR = BASE_DIR / "data" / "processed" / "matching"
MODELS_DIR = BASE_DIR / "logistics-ai" / "models"
REPORTS_DIR = BASE_DIR / "logistics-ai" / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RANDOM_SEED = 42

def chronological_split(df):
    """
    Split the dataset chronologically based on departure_date, 
    but ensure loads are not split across sets.
    """
    print("\nSplitting dataset chronologically...")
    df = df.sort_values(["departure_date", "load_id", "match"], ascending=[True, True, False]).reset_index(drop=True)
    loads = df["load_id"].unique()
    n = len(loads)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    
    train_loads = set(loads[:n_train])
    val_loads = set(loads[n_train:n_train+n_val])
    test_loads = set(loads[n_train+n_val:])
    
    train_df = df[df["load_id"].isin(train_loads)].copy()
    val_df = df[df["load_id"].isin(val_loads)].copy()
    test_df = df[df["load_id"].isin(test_loads)].copy()
    
    print(f"  Train: {len(train_loads):,} loads ({len(train_df):,} rows)")
    print(f"  Val  : {len(val_loads):,} loads ({len(val_df):,} rows)")
    print(f"  Test : {len(test_loads):,} loads ({len(test_df):,} rows)")
    
    return train_df, val_df, test_df

def build_preprocessor(train_df, num_cols, cat_cols):
    print("Building preprocessor...")
    
    num_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    cat_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("encode", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])

    preprocessor = ColumnTransformer([
        ("num", num_pipeline, num_cols),
        ("cat", cat_pipeline, cat_cols),
    ], remainder="drop")
    
    return preprocessor

def get_X_y_q(df, preprocessor, fit=False):
    """
    Returns X (features), y (target), and q (group sizes for ranking)
    """
    # X and y
    if fit:
        X_trans = preprocessor.fit_transform(df)
    else:
        X_trans = preprocessor.transform(df)
        
    y = df["match"].values
    
    # Calculate group sizes (number of trucks per load)
    # The dataframe must be sorted by load_id!
    group_sizes = df.groupby("load_id", sort=False).size().values
    
    return X_trans, y, group_sizes

def main():
    t0 = time.time()
    print("=" * 70)
    print("FREIGHT MATCHING — XGBOOST RANKER TRAINING")
    print("=" * 70)
    
    df = pd.read_csv(MATCHING_DIR / "matching_dataset.csv")
    print(f"Loaded dataset: {df.shape}")
    
    # Identify feature columns
    exclude = ["load_id", "truck_id", "match", "departure_date"]
    all_features = [c for c in df.columns if c not in exclude]
    
    # We can infer cat vs num from Phase 1 or just hardcode known categoricals
    cat_cols = ["fuel_type", "driving_style", "truck_age_category"]
    cat_cols = [c for c in cat_cols if c in all_features]
    num_cols = [c for c in all_features if c not in cat_cols]
    
    print(f"Features: {len(num_cols)} numeric, {len(cat_cols)} categorical")
    
    train_df, val_df, test_df = chronological_split(df)
    
    # Ensure they are sorted by load_id for ranking
    train_df = train_df.sort_values("load_id").reset_index(drop=True)
    val_df = val_df.sort_values("load_id").reset_index(drop=True)
    test_df = test_df.sort_values("load_id").reset_index(drop=True)
    
    preprocessor = build_preprocessor(train_df, num_cols, cat_cols)
    
    X_train, y_train, q_train = get_X_y_q(train_df, preprocessor, fit=True)
    X_val, y_val, q_val = get_X_y_q(val_df, preprocessor, fit=False)
    X_test, y_test, q_test = get_X_y_q(test_df, preprocessor, fit=False)
    
    # Create XGBoost DMatrices with grouping
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtrain.set_group(q_train)
    
    dval = xgb.DMatrix(X_val, label=y_val)
    dval.set_group(q_val)
    
    dtest = xgb.DMatrix(X_test, label=y_test)
    dtest.set_group(q_test)
    
    print("\nTraining XGBoost Ranker (LambdaMART)...")
    # objective: rank:pairwise or rank:ndcg
    params = {
        "objective": "rank:pairwise",
        "eval_metric": "ndcg@5",
        "learning_rate": 0.1,
        "max_depth": 6,
        "subsample": 0.8,
        "tree_method": "hist",
        "random_state": RANDOM_SEED
    }
    
    evals = [(dtrain, "train"), (dval, "val")]
    
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=500,
        evals=evals,
        early_stopping_rounds=30,
        verbose_eval=50
    )
    
    # Evaluate on test
    test_ndcg = model.eval(dtest, name="test")
    print(f"\nTest evaluation: {test_ndcg}")
    
    # Compute MRR & Precision@1 on test set manually
    test_df["score"] = model.predict(dtest)
    test_df = test_df.sort_values(["load_id", "score"], ascending=[True, False])
    
    # Rank of the true match (1-indexed)
    test_df["rank"] = test_df.groupby("load_id").cumcount() + 1
    
    # Where is match == 1?
    matches = test_df[test_df["match"] == 1]
    
    mrr = (1.0 / matches["rank"]).mean()
    p_at_1 = (matches["rank"] == 1).mean()
    
    print(f"Test MRR        : {mrr:.4f}")
    print(f"Test Precision@1: {p_at_1:.4f}")
    
    # Feature importance
    feature_names = num_cols + cat_cols
    importance = model.get_score(importance_type="gain")
    # Map f0, f1 back to names
    imp_dict = {}
    for k, v in importance.items():
        idx = int(k[1:])
        name = feature_names[idx] if idx < len(feature_names) else k
        imp_dict[name] = v
        
    imp_df = pd.DataFrame(list(imp_dict.items()), columns=["feature", "gain"]).sort_values("gain", ascending=False).head(20)
    
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(imp_df["feature"][::-1], imp_df["gain"][::-1], color="#4A90D9")
    ax.set_xlabel("Gain")
    ax.set_title("Matching Model Feature Importance")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "matching_importance.png")
    
    print("\nTop Features by Gain:")
    print(imp_df.head(10).to_string(index=False))
    
    # Save artifacts
    print("\nSaving artifacts...")
    model_path = MODELS_DIR / "matching_xgboost.json"
    model.save_model(model_path)
    joblib.dump(preprocessor, MODELS_DIR / "matching_preprocessor.pkl")
    with open(MODELS_DIR / "matching_features.json", "w") as f:
        json.dump({
            "numeric": num_cols,
            "categorical": cat_cols
        }, f, indent=2)
        
    print(f"Saved to {model_path}")
    print(f"Done in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
