"""
scripts/verify_and_summarize.py
================================
Post-training verification:
  - Check model artifacts exist
  - Run a test prediction
  - Print model comparison table
  - Print top 10 feature importances
  - Print final summary
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import joblib


def main():
    print("=" * 60)
    print("POST-TRAINING VERIFICATION")
    print("=" * 60)

    # 1. Check artifacts
    artifacts = [
        ROOT / "models" / "delivery_time_xgboost.pkl",
        ROOT / "models" / "nan_fill_values.json",
        ROOT / "models" / "feature_names.json",
        ROOT / "reports" / "model_comparison.csv",
        ROOT / "data" / "processed" / "cleaned_delivery_sh.csv",
        ROOT / "reports" / "figures" / "feature_importance_xgboost.png",
    ]
    print("\n[1] Checking artifacts:")
    all_ok = True
    for path in artifacts:
        exists = path.exists()
        status = "OK" if exists else "MISSING"
        print(f"  [{status}] {path.relative_to(ROOT)}")
        if not exists:
            all_ok = False

    if not all_ok:
        print("\nSome artifacts are missing. Run src/train.py first.")
        return

    # 2. Model comparison
    print("\n[2] Model Comparison (Test Set):")
    comp = pd.read_csv(ROOT / "reports" / "model_comparison.csv")
    print(comp.to_string(index=False))

    # 3. Best model
    best = comp.loc[comp["MAE"].idxmin()]
    print(f"\n[3] Best model by MAE: {best['Model']}")
    print(f"    MAE  = {best['MAE']:.3f} min")
    print(f"    RMSE = {best['RMSE']:.3f} min")
    print(f"    R²   = {best['R2']:.4f}")
    print(f"    MAPE = {best['MAPE']:.2f}%")

    # 4. Feature importance
    model = joblib.load(ROOT / "models" / "delivery_time_xgboost.pkl")
    with open(ROOT / "models" / "feature_names.json") as f:
        feature_names = json.load(f)

    importance = model.get_booster().get_score(importance_type="gain")
    imp_named = {}
    for key, val in importance.items():
        if key.startswith("f") and key[1:].isdigit():
            idx = int(key[1:])
            name = feature_names[idx] if idx < len(feature_names) else key
        else:
            name = key
        imp_named[name] = val

    imp_df = (
        pd.DataFrame({"feature": list(imp_named.keys()), "importance": list(imp_named.values())})
        .sort_values("importance", ascending=False)
    )
    print("\n[4] Top 10 Feature Importances (XGBoost Gain):")
    for _, row in imp_df.head(10).iterrows():
        print(f"  {row['feature']:<45} {row['importance']:>10.2f}")

    # 5. Test prediction
    print("\n[5] Test prediction:")
    from predict import DeliveryTimePredictor
    predictor = DeliveryTimePredictor()
    test_record = {
        "accept_time": "06-04 10:30:00",
        "accept_gps_lng": 121.5228,
        "accept_gps_lat": 31.1060,
        "lng": 121.5241,
        "lat": 31.0661,
        "aoi_type": 1,
        "region_id": 1,
    }
    pred = predictor.predict(test_record)
    print(f"  Input: Jun-4 10:30, courier @ (121.5228, 31.1060), dest @ (121.5241, 31.0661)")
    print(f"  Predicted duration: {pred:.2f} minutes ({pred/60:.1f} hours)")
    print(f"  (Using training-set medians for historical features — cold-start scenario)")

    print("\nVerification complete.")


if __name__ == "__main__":
    main()
