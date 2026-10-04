# Target Variable Analysis: `delay`

## Source Table
`truck_schedule_table.csv`

## Raw Inspection Results

| Property | Value |
|----------|-------|
| Column name | `delay` |
| Data type | `int64` |
| Unique values | `[0, 1]` |
| Minimum | `0` |
| Maximum | `1` |
| Null values | `0` |

### Value Counts
| delay | Count | Percentage |
|-------|-------|------------|
| 0 (on-time) | 8,014 | **65.1%** |
| 1 (delayed) | 4,294 | **34.9%** |

### Distribution Note
The target is moderately imbalanced (~35% positive class).
This is not extreme enough to require resampling techniques,
and their use would be inappropriate for chronological data anyway.
Class weights are the correct remedy.

---

## Interpretation

`delay` is a **binary integer (0 or 1)** indicating whether a delivery was late.

- `delay = 0`: The truck arrived on time (or before estimated arrival)
- `delay = 1`: The truck was delayed (arrived after estimated arrival)

The column appears to be a pre-computed binary flag derived from comparing
actual arrival time to estimated arrival time. **The actual arrival timestamp
is NOT present** in any of the 7 dataset files.

---

## Can We Build a Regression Target?

To support regression (e.g., "predict delay in minutes"), we would need:
- **Actual arrival datetime** (not in any file)
- OR **delay duration in minutes** (not present)

The only time-related columns in the schedule are:
- `departure_date`: actual departure timestamp ✓
- `estimated_arrival`: estimated (not actual) arrival ✓
- `delay`: binary flag ✓

There is **no actual arrival time** in the dataset. The difference
`estimated_arrival - departure_date` is the *planned* trip duration, not
the *actual* delay. This cannot be used as a regression target without
fabricating data.

---

## Conclusion

> **Primary ML problem: BINARY DELAY CLASSIFICATION**
>
> Target: `delay ∈ {0, 1}`
>
> Output: `delay_probability ∈ [0, 1]`
>
> Regression is NOT defensible from this dataset.
> No delay_minutes column exists or can be honestly constructed.

---

## Handling Class Imbalance

| Method | Approach |
|--------|---------|
| Logistic Regression | `class_weight='balanced'` |
| Random Forest | `class_weight='balanced'` |
| XGBoost | `scale_pos_weight = n_negative / n_positive ≈ 1.87` |
| Threshold tuning | Applied post-training if recall needs boosting |
| SMOTE | **NOT used** — temporal data; would cause cross-time leakage |
