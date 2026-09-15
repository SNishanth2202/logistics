"""
train.py
========
Training pipeline for freight delivery delay classification.

Models trained (in order):
  1. Majority-class baseline
  2. Logistic Regression (with class_weight='balanced')
  3. Random Forest Classifier (with class_weight='balanced')
  4. XGBoost Classifier (scale_pos_weight + lightweight tuning)

Split strategy:
  Chronological 70% train / 15% val / 15% test
  (Never random — this is temporal data)

Outputs:
  models/delay_xgboost.pkl
  models/preprocessor.pkl
  models/feature_columns.json
  reports/model_comparison.csv
  reports/figures/*.png
"""
import json
import time
import joblib
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from evaluate import (
    compute_metrics, print_metrics, plot_confusion_matrix,
    plot_roc_curves, plot_pr_curves,
    save_comparison_table, print_comparison_table,
)

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────────────

MASTER_CSV = BASE_DIR / "data" / "processed" / "master_modeling.csv"
MODELS_DIR = BASE_DIR / "logistics-ai" / "models"
REPORTS_DIR = BASE_DIR / "logistics-ai" / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
TARGET = "delay"

# ─── Feature specification ────────────────────────────────────────────────────

NUMERIC_FEATURES = [
    "hour", "day_of_week", "day_of_month", "month", "is_weekend", "is_peak_hour",
    "truck_age", "load_capacity_pounds", "mileage_mpg",
    "driver_age", "experience", "driver_ratings", "average_speed_mph",
    "distance", "average_hours",
    "weather_temp", "weather_wind_speed", "weather_precip", "weather_humidity",
    "weather_visibility", "weather_chanceofrain", "weather_chanceoffog",
    "weather_chanceofsnow", "weather_chanceofthunder",
    "traffic_vehicles", "traffic_accident", "daily_accident_count",
    "truck_trip_count_hist", "truck_delay_rate_hist",
    "route_trip_count_hist", "route_delay_rate_hist",
]

CATEGORICAL_FEATURES = [
    "fuel_type",
    "driving_style",
    "truck_age_category",
]


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_master(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["departure_date"])
    print(f"Loaded master dataset: {len(df):,} rows x {len(df.columns)} cols")
    print(f"  delay distribution: {df[TARGET].value_counts().to_dict()}")
    print(f"  date range: {df['departure_date'].min().date()} → {df['departure_date'].max().date()}")
    return df


# ─── Chronological split ──────────────────────────────────────────────────────

def chronological_split(df: pd.DataFrame, train_frac=0.70, val_frac=0.15):
    """
    Split by time — never random.
    train_frac + val_frac + (1-train_frac-val_frac) = 1.0
    """
    df = df.sort_values("departure_date").reset_index(drop=True)
    n = len(df)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)

    train_df = df.iloc[:n_train].copy()
    val_df = df.iloc[n_train: n_train + n_val].copy()
    test_df = df.iloc[n_train + n_val:].copy()

    print(f"\nChronological split:")
    print(f"  Train : {len(train_df):,} rows  {train_df['departure_date'].min().date()} → {train_df['departure_date'].max().date()}")
    print(f"  Val   : {len(val_df):,} rows  {val_df['departure_date'].min().date()} → {val_df['departure_date'].max().date()}")
    print(f"  Test  : {len(test_df):,} rows  {test_df['departure_date'].min().date()} → {test_df['departure_date'].max().date()}")
    return train_df, val_df, test_df


# ─── Preprocessing ────────────────────────────────────────────────────────────

def build_preprocessor(train_df: pd.DataFrame):
    """
    Build sklearn ColumnTransformer preprocessor fitted on training data only.
    """
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, OrdinalEncoder
    from sklearn.impute import SimpleImputer
    from sklearn.compose import ColumnTransformer

    avail_num = [c for c in NUMERIC_FEATURES if c in train_df.columns]
    avail_cat = [c for c in CATEGORICAL_FEATURES if c in train_df.columns]

    num_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    cat_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("encode", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])

    preprocessor = ColumnTransformer([
        ("num", num_pipeline, avail_num),
        ("cat", cat_pipeline, avail_cat),
    ], remainder="drop")

    return preprocessor, avail_num, avail_cat


def get_X_y(df: pd.DataFrame, preprocessor, avail_num, avail_cat, fit=False):
    feat_cols = [c for c in avail_num + avail_cat if c in df.columns]
    X = df[feat_cols]
    y = df[TARGET].values.astype(int)
    if fit:
        X_transformed = preprocessor.fit_transform(X)
    else:
        X_transformed = preprocessor.transform(X)
    return X_transformed, y


# ─── Re-fit historical rate imputation on train only ─────────────────────────

def refit_hist_imputation(train_df, val_df, test_df, global_rate):
    """Fill NaN historical rates using training-set global rate."""
    for df in [train_df, val_df, test_df]:
        df["truck_delay_rate_hist"] = df["truck_delay_rate_hist"].fillna(global_rate)
        df["route_delay_rate_hist"] = df["route_delay_rate_hist"].fillna(global_rate)
        df["truck_trip_count_hist"] = df["truck_trip_count_hist"].fillna(0)
        df["route_trip_count_hist"] = df["route_trip_count_hist"].fillna(0)
    return train_df, val_df, test_df


# ─── Models ──────────────────────────────────────────────────────────────────

def train_majority_baseline(y_train):
    from sklearn.dummy import DummyClassifier
    clf = DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED)
    clf.fit(np.zeros((len(y_train), 1)), y_train)
    return clf


def train_logistic_regression(X_train, y_train):
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=RANDOM_SEED,
        solver="lbfgs",
        C=1.0,
    )
    clf.fit(X_train, y_train)
    return clf


def train_random_forest(X_train, y_train):
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=10,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_SEED,
    )
    clf.fit(X_train, y_train)
    return clf


def train_xgboost(X_train, y_train, X_val, y_val):
    from xgboost import XGBClassifier

    # scale_pos_weight: ratio of negative to positive class (handles imbalance)
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    spw = n_neg / n_pos
    print(f"  XGBoost scale_pos_weight: {spw:.2f} (neg/pos = {n_neg}/{n_pos})")

    search_space = [
        {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.8},
        {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.05, "subsample": 0.8},
        {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.02, "subsample": 0.9},
    ]

    best_auc = -1
    best_model = None
    best_params = None

    for params in search_space:
        clf = XGBClassifier(
            **params,
            scale_pos_weight=spw,
            min_child_weight=10,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective="binary:logistic",
            eval_metric="auc",
            early_stopping_rounds=30,
            n_jobs=-1,
            random_state=RANDOM_SEED,
            verbosity=0,
        )
        clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        from sklearn.metrics import roc_auc_score
        y_val_prob = clf.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_val_prob)
        print(f"    params={params}  val_AUC={auc:.4f}")
        if auc > best_auc:
            best_auc = auc
            best_model = clf
            best_params = params

    print(f"  Best XGBoost params: {best_params}  val_AUC={best_auc:.4f}")
    return best_model


# ─── Feature importance ───────────────────────────────────────────────────────

def plot_xgb_feature_importance(model, feature_names: list, output_dir: Path):
    importance = model.get_booster().get_score(importance_type="gain")
    named = {}
    for k, v in importance.items():
        if k.startswith("f") and k[1:].isdigit():
            idx = int(k[1:])
            name = feature_names[idx] if idx < len(feature_names) else k
        else:
            name = k
        named[name] = v

    imp_df = (
        pd.DataFrame({"feature": list(named.keys()), "importance": list(named.values())})
        .sort_values("importance", ascending=False)
        .head(20)
    )

    fig, ax = plt.subplots(figsize=(9, 7))
    bars = ax.barh(imp_df["feature"][::-1], imp_df["importance"][::-1], color="#4A90D9")
    ax.set_xlabel("Feature Importance (Gain)", fontsize=12)
    ax.set_title("XGBoost — Top 20 Features by Gain", fontsize=13)
    fig.tight_layout()
    fig.savefig(output_dir / "feature_importance_xgboost.png", dpi=120)
    plt.close(fig)
    print(f"\n  Feature importance plot saved → {output_dir}/feature_importance_xgboost.png")
    print("\n  Top 10 features by gain:")
    for _, row in imp_df.head(10).iterrows():
        print(f"    {row['feature']:<40} {row['importance']:>10.2f}")


def plot_shap_importance(model, X_val: np.ndarray, feature_names: list, output_dir: Path):
    try:
        import shap
        rng = np.random.default_rng(RANDOM_SEED)
        sample_idx = rng.choice(len(X_val), min(2000, len(X_val)), replace=False)
        X_sample = X_val[sample_idx]

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)

        # SHAP summary (beeswarm)
        plt.figure(figsize=(9, 7))
        shap.summary_plot(shap_values, X_sample, feature_names=feature_names,
                          max_display=15, show=False, plot_type="dot")
        plt.tight_layout()
        plt.savefig(output_dir / "shap_summary.png", dpi=120, bbox_inches="tight")
        plt.close()
        print(f"  SHAP beeswarm plot saved → {output_dir}/shap_summary.png")

        # SHAP bar plot (mean absolute)
        plt.figure(figsize=(9, 7))
        shap.summary_plot(shap_values, X_sample, feature_names=feature_names,
                          max_display=15, show=False, plot_type="bar")
        plt.tight_layout()
        plt.savefig(output_dir / "shap_bar.png", dpi=120, bbox_inches="tight")
        plt.close()
        print(f"  SHAP bar plot saved → {output_dir}/shap_bar.png")
    except Exception as e:
        print(f"  SHAP skipped: {e}")


# ─── Save artifacts ───────────────────────────────────────────────────────────

def save_artifacts(model, preprocessor, feature_names: list, avail_num, avail_cat):
    joblib.dump(model, MODELS_DIR / "delay_xgboost.pkl")
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.pkl")
    with open(MODELS_DIR / "feature_columns.json", "w") as f:
        json.dump({
            "feature_names": feature_names,
            "numeric_features": avail_num,
            "categorical_features": avail_cat,
            "target": TARGET,
        }, f, indent=2)
    print(f"\n  Model saved     → {MODELS_DIR}/delay_xgboost.pkl")
    print(f"  Preprocessor    → {MODELS_DIR}/preprocessor.pkl")
    print(f"  Feature columns → {MODELS_DIR}/feature_columns.json")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("=" * 70)
    print("FREIGHT DELAY CLASSIFICATION — TRAINING PIPELINE")
    print("=" * 70)

    # 1. Load master dataset
    df = load_master(MASTER_CSV)

    # 2. Chronological split
    train_df, val_df, test_df = chronological_split(df)

    # 3. Re-fit historical rate imputation on train global rate
    global_rate = train_df[TARGET].mean()
    print(f"\n  Training-set global delay rate: {global_rate:.3f}")
    train_df, val_df, test_df = refit_hist_imputation(train_df, val_df, test_df, global_rate)

    # 4. Build preprocessor (fit on train only)
    preprocessor, avail_num, avail_cat = build_preprocessor(train_df)
    all_feature_names = avail_num + avail_cat

    X_train, y_train = get_X_y(train_df, preprocessor, avail_num, avail_cat, fit=True)
    X_val, y_val = get_X_y(val_df, preprocessor, avail_num, avail_cat, fit=False)
    X_test, y_test = get_X_y(test_df, preprocessor, avail_num, avail_cat, fit=False)

    print(f"\n  Feature matrix shapes:")
    print(f"    Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

    all_metrics = []
    all_results = []

    # ── 5a. Majority class baseline ───────────────────────────────────────────
    print("\n[1/4] Majority-class baseline ...")
    dummy = train_majority_baseline(y_train)
    y_pred = dummy.predict(np.zeros((len(y_test), 1)))
    y_prob = np.full(len(y_test), global_rate)
    m = compute_metrics(y_test, y_pred, y_prob, "Majority Baseline")
    print_metrics(m)
    all_metrics.append(m)
    all_results.append({"model_name": "Majority Baseline", "y_true": y_test, "y_prob": y_prob, "metrics": m})

    # ── 5b. Logistic Regression ───────────────────────────────────────────────
    print("\n[2/4] Logistic Regression (class_weight=balanced) ...")
    lr = train_logistic_regression(X_train, y_train)
    y_pred = lr.predict(X_test)
    y_prob = lr.predict_proba(X_test)[:, 1]
    m = compute_metrics(y_test, y_pred, y_prob, "Logistic Regression")
    print_metrics(m)
    all_metrics.append(m)
    all_results.append({"model_name": "Logistic Regression", "y_true": y_test, "y_prob": y_prob, "metrics": m})
    plot_confusion_matrix(y_test, y_pred, "Logistic Regression", FIGURES_DIR)

    # ── 5c. Random Forest ─────────────────────────────────────────────────────
    print("\n[3/4] Random Forest (n_estimators=200, class_weight=balanced) ...")
    t_rf = time.time()
    rf = train_random_forest(X_train, y_train)
    print(f"  Trained in {time.time()-t_rf:.1f}s")
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]
    m = compute_metrics(y_test, y_pred, y_prob, "Random Forest")
    print_metrics(m)
    all_metrics.append(m)
    all_results.append({"model_name": "Random Forest", "y_true": y_test, "y_prob": y_prob, "metrics": m})
    plot_confusion_matrix(y_test, y_pred, "Random Forest", FIGURES_DIR)

    # ── 5d. XGBoost ───────────────────────────────────────────────────────────
    print("\n[4/4] XGBoost Classifier (scale_pos_weight + tuning) ...")
    t_xgb = time.time()
    xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
    print(f"  Trained in {time.time()-t_xgb:.1f}s")
    y_pred = xgb_model.predict(X_test)
    y_prob = xgb_model.predict_proba(X_test)[:, 1]
    m = compute_metrics(y_test, y_pred, y_prob, "XGBoost")
    print_metrics(m)
    all_metrics.append(m)
    all_results.append({"model_name": "XGBoost", "y_true": y_test, "y_prob": y_prob, "metrics": m})
    plot_confusion_matrix(y_test, y_pred, "XGBoost", FIGURES_DIR)

    # 6. Comparison table
    print_comparison_table(all_metrics)
    save_comparison_table(all_metrics, REPORTS_DIR / "model_comparison.csv")

    # 7. ROC and PR curves
    print("\nGenerating ROC and PR curves ...")
    plot_roc_curves(all_results, FIGURES_DIR)
    plot_pr_curves(all_results, FIGURES_DIR)

    # 8. Feature importance (XGBoost + SHAP)
    print("\nFeature importance ...")
    plot_xgb_feature_importance(xgb_model, all_feature_names, FIGURES_DIR)
    plot_shap_importance(xgb_model, X_val, all_feature_names, FIGURES_DIR)

    # 9. Save best model artifacts
    print("\nSaving model artifacts ...")
    save_artifacts(xgb_model, preprocessor, all_feature_names, avail_num, avail_cat)

    elapsed = (time.time() - t0) / 60
    print(f"\nTotal training time: {elapsed:.1f} min")
    print("Done.")


if __name__ == "__main__":
    main()
