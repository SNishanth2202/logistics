# AI-Driven Freight Delay Classification

**Phase 1 of: AI-Driven Dynamic Freight Matching and Multi-Objective Route Optimization for Sustainable Logistics**

---

## Overview

This module predicts the **probability of a freight delivery being delayed** using 7 historical logistics datasets covering trucks, drivers, routes, traffic, and weather conditions (Jan–Feb 2019).

**Output**: `delay_probability ∈ [0, 1]`  
**Problem type**: Binary classification (`delay = 0` on-time, `delay = 1` delayed)

---

## Dataset Structure

| File | Rows | Purpose |
|------|------|---------|
| `truck_schedule_table.csv` | 12,308 | **Spine** — one row per delivery trip |
| `drivers_table.csv` | 1,300 | Driver attributes |
| `trucks_table.csv` | 1,300 | Truck attributes |
| `routes_table.csv` | 2,352 | Route distance and avg hours |
| `routes_weather.csv` | 425,712 | 6-hourly weather per route |
| `traffic_table.csv` | 2,597,913 | Hourly traffic per route |
| `city_weather.csv` | 55,176 | Hourly weather per city (fallback) |

### Table Relationships
```
Drivers (vehicle_no = truck_id)
    │
    ▼
Trucks ──── truck_id ────► TruckSchedule (spine)
                                    │
                 route_id ──────────┼──────────► Routes
                                    │
                 route_id + date ───┼──────────► RoutesWeather (daily avg)
                                    │
              route_id+date+hour ───┴──────────► Traffic (hourly)
```

---

## Target Variable

`delay` is a binary integer (0 or 1):
- `delay = 0`: On-time delivery (65.1%)
- `delay = 1`: Delayed delivery (34.9%)

**No actual arrival timestamp exists in the data.** Therefore:
- ✅ Delay Classification is the primary ML problem
- ❌ Regression (delay minutes) is NOT supported — no actual arrival time exists

---

## Features Used

### Time (from departure_date)
`hour`, `day_of_week`, `day_of_month`, `month`, `is_weekend`, `is_peak_hour`

### Truck
`truck_age`, `load_capacity_pounds`, `mileage_mpg`, `fuel_type`, `truck_age_category`

### Driver (linked via vehicle_no = truck_id)
`driver_age`, `experience`, `driving_style`, `driver_ratings`, `average_speed_mph`

### Route
`distance`, `average_hours`

### Weather (daily avg per route from routes_weather.csv)
`weather_temp`, `weather_wind_speed`, `weather_precip`, `weather_humidity`, `weather_visibility`, `weather_chanceofrain`, `weather_chanceoffog`, `weather_chanceofsnow`, `weather_chanceofthunder`

### Traffic (at departure hour)
`traffic_vehicles`, `traffic_accident`

### Historical Features (temporal, leakage-free)
| Feature | Definition |
|---------|------------|
| `truck_trip_count_hist` | Number of prior trips by this truck |
| `truck_delay_rate_hist` | Fraction of prior trips delayed (this truck) |
| `route_trip_count_hist` | Number of prior trips on this route |
| `route_delay_rate_hist` | Fraction of prior trips delayed (this route) |

### Features Excluded
| Feature | Reason |
|---------|--------|
| `estimated_arrival` | Not available before delivery starts (leakage risk) |
| `driver_id` | Not in schedule table — driver linked statically via vehicle_no |
| `name`, `gender` | Non-predictive identifiers |
| `origin_id`, `destination_id` | Captured by `route_id` and `distance` |

---

## Leakage Prevention

All historical features are computed using **strictly prior observations**:

For a delivery at time **T**, the truck's historical delay rate includes only deliveries at time **< T** (using expanding cumulative sums with `shift(1)` to exclude the current record).

This is enforced in [`src/historical_features.py`](src/historical_features.py) and verified by a random-sample leakage test at build time.

---

## Train/Validation/Test Split

**Chronological split** — never random:

| Split | Rows | Date Range |
|-------|------|------------|
| Train | 8,615 | 2019-01-01 → 2019-01-31 |
| Validation | 1,846 | 2019-01-31 → 2019-02-06 |
| Test | 1,847 | 2019-02-06 → 2019-02-12 |

Preprocessing (imputation, scaling, encoding) is **fit on training data only**.

---

## Models & Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|-------|----------|-----------|--------|-----|---------|--------|
| Majority Baseline | 0.606 | 0.000 | 0.000 | 0.000 | 0.500 | 0.394 |
| Logistic Regression | 0.619 | 0.903 | 0.039 | 0.074 | 0.660 | 0.590 |
| Random Forest | 0.763 | 0.724 | 0.646 | 0.683 | 0.805 | 0.666 |
| **XGBoost** | 0.760 | 0.714 | **0.651** | 0.681 | **0.812** | 0.659 |

**Best model**: XGBoost (ROC-AUC = 0.812, Recall = 0.651)

### Class Imbalance Handling
- Logistic Regression / Random Forest: `class_weight='balanced'`
- XGBoost: `scale_pos_weight = 2.0` (n_neg / n_pos)
- SMOTE was NOT used (would cause temporal data leakage)

---

## Top 10 Features (XGBoost Gain)

| Rank | Feature | Gain |
|------|---------|------|
| 1 | `average_hours` (route avg travel time) | 191.3 |
| 2 | `distance` (route distance) | 140.7 |
| 3 | `route_trip_count_hist` | 74.5 |
| 4 | `day_of_month` | 71.5 |
| 5 | `truck_trip_count_hist` | 38.8 |
| 6 | `route_delay_rate_hist` | 30.5 |
| 7 | `day_of_week` | 20.4 |
| 8 | `traffic_vehicles` | 15.6 |
| 9 | `weather_precip` | 14.9 |
| 10 | `weather_temp` | 14.5 |

*Route features dominate — longer/more complex routes are harder to complete on time.*

---

## Data Quality Notes

| Issue | Records | Treatment |
|-------|---------|-----------|
| Missing `load_capacity_pounds` | 57 trucks | Median imputation (train only) |
| Missing `fuel_type` | 40 trucks | Imputed as 'Unknown' |
| Missing `gender` | 23 drivers | Imputed as 'Unknown' |
| Missing `driving_style` | 52 drivers | Imputed as 'Unknown' |
| Negative `experience` | 12 drivers | Set to NaN, median imputed |
| Missing `no_of_vehicles` (traffic) | 1,152 | Route-date median, then 0 |
| Weather temperature | All records | Fahrenheit, not Celsius (kept as-is — monotone transform) |
| Traffic hour encoding | All records | Was 0/100/200→2300, divided by 100 |

---

## Project Structure

```
logistics/
├── data/
│   ├── raw/                     ← 7 original CSV files
│   └── processed/
│       ├── master_modeling.csv  ← 12,308 rows, 38 cols
│       └── imputation_medians.json
├── src/
│   ├── inspect_data.py          ← Dataset inventory
│   ├── data_validation.py       ← Quality checks
│   ├── data_preprocessing.py    ← Load + clean all tables
│   ├── feature_engineering.py   ← Static joins + features
│   ├── historical_features.py   ← Temporal rolling features
│   ├── build_dataset.py         ← Orchestrate full build
│   ├── train.py                 ← Train 4 models
│   ├── evaluate.py              ← Classification metrics
│   └── predict.py               ← Inference on new records
├── notebooks/
│   └── 01_eda.ipynb             ← Full exploratory analysis
├── logistics-ai/
│   ├── models/
│   │   ├── delay_xgboost.pkl    ← Best model
│   │   ├── preprocessor.pkl     ← Fitted sklearn preprocessor
│   │   └── feature_columns.json ← Feature spec
│   └── reports/
│       ├── model_comparison.csv
│       └── figures/             ← All plots
└── reports/
    ├── dataset_inventory.csv / .txt
    ├── data_relationships.md
    ├── target_analysis.md
    └── data_quality_report.md
```

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Inspect datasets
python src/inspect_data.py

# 3. Data quality check
python src/data_validation.py

# 4. Build master dataset (~3 min due to large traffic table)
python src/build_dataset.py

# 5. Train models (~12 seconds)
python src/train.py

# 6. Run inference on example record
python src/predict.py --example
```

---

## Limitations

1. **Short time window**: Only 6.5 weeks of data (Jan–Feb 2019). Historical features are sparse for trucks/routes with few trips.
2. **No actual arrival time**: Cannot compute regression targets (delay in minutes) without fabricating data.
3. **Static driver-truck assignment**: One driver per truck. Driver features do not vary over time.
4. **No geographic coordinates**: Cannot compute shortest path or spatial features.
5. **Logistic Regression weakness**: The logistic model struggled due to mostly non-linear relationships; recall was near-zero despite balanced weights. XGBoost and Random Forest are far superior for this dataset.
6. **Temperature in Fahrenheit**: All weather temperatures are in °F (not labeled in source data).

---

## Next Phase (Phase 2+)

- FastAPI serving layer for real-time inference
- PostgreSQL integration for live data
- Freight matching using delay probability as a risk signal
- Multi-objective route optimization (OR-Tools / Genetic Algorithms)
- Live traffic and weather API integration
- Model retraining pipeline as new data arrives
