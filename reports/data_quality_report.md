# Data Quality Report

Generated for: Freight Logistics Dataset
Tables inspected: 7

| Table | Problem | Affected Records | Treatment | Reason |
|-------|---------|-----------------|-----------|--------|
| drivers_table | ✓ Driver age outside [18,80] | 0 | Flag; keep but note | Age<18 illegal to drive; >80 unusual |
| drivers_table | ⚠ Negative experience | 12 | Flag; keep | Experience cannot be negative |
| drivers_table | ✓ Experience > (age-18) | 0 | Flag; keep | Cannot accumulate more experience than driving-eligible years |
| drivers_table | ✓ Average speed outside (0, 120] mph | 0 | Flag; keep | Speed 0 or >120 mph unrealistic for freight |
| drivers_table | ⚠ Missing gender | 23 | Impute as 'Unknown' | Non-informative for model |
| drivers_table | ⚠ Missing driving_style | 52 | Impute as 'Unknown' | Will be encoded as separate category |
| drivers_table | ✓ Duplicate vehicle_no (driver-truck link key) | 0 | Investigate; use first match | vehicle_no must be unique to link driver to truck |
| trucks_table | ✓ Truck age outside [0,30] | 0 | Flag; keep | Age<0 impossible; >30 very unusual |
| trucks_table | ✓ Load capacity <= 0 lbs | 0 | Flag; impute with median | Zero/negative capacity is physically impossible |
| trucks_table | ✓ Mileage MPG <= 0 | 0 | Flag; impute with median | Non-positive MPG is impossible |
| trucks_table | ⚠ Missing load_capacity_pounds | 57 | Impute with median (train only) | Moderate missingness; median is defensible |
| trucks_table | ⚠ Missing fuel_type | 40 | Impute as 'Unknown' | Categorical; Unknown category |
| trucks_table | ✓ Duplicate truck_id | 0 | Raise error if found | truck_id must be unique primary key |
| routes_table | ✓ Distance <= 0 | 0 | Flag; impute or drop | Non-positive distance is impossible |
| routes_table | ✓ average_hours <= 0 | 0 | Flag; impute with median | Non-positive travel time is impossible |
| routes_table | ✓ origin_id == destination_id (self-loop) | 0 | Flag; likely data error | A route from city to itself is nonsensical |
| routes_table | ✓ Duplicate route_id | 0 | Raise error if found | route_id must be unique |
| traffic_table | ✓ Negative no_of_vehicles | 0 | Set to NaN; impute with 0 | Negative vehicle count is impossible |
| traffic_table | ⚠ Missing no_of_vehicles | 1,152 | Impute with route-date median | 1,152 missing (0.04%); low impact |
| traffic_table | ✓ accident not in {0,1} | 0 | Coerce to 0/1 | Binary indicator; invalid values should be 0 |
| traffic_table | ✓ Non-standard hour encoding: hour column uses [np.int64(0), np.int64(100), np.int64(200), np.int64(300), np.int64(400)]... format (max=2300) | 0 | Divide by 100 to get 0-23 hour | Dataset encodes hour as 0,100,200,...,2300 |
| truck_schedule_table | ✓ Unparseable departure_date | 0 | Drop affected rows | Cannot use without valid timestamp |
| truck_schedule_table | ✓ Unparseable estimated_arrival | 0 | Flag | No actual arrival in dataset |
| truck_schedule_table | ✓ estimated_arrival < departure_date | 0 | Flag; investigate | Arrival before departure is physically impossible |
| truck_schedule_table | ✓ Duplicate (truck_id, departure_date) | 0 | Keep first occurrence | Same truck cannot depart twice at same time |
| truck_schedule_table | ✓ Class imbalance: delay=1 is 34.9% of records | 0 | Use class_weight='balanced' / scale_pos_weight | Moderate imbalance; class weights sufficient |
| routes_weather | ⚠ Temperature outside [-60, 60]°C | 212,697 | Flag; keep | Extreme temperatures — check units (may be Fahrenheit) |
| routes_weather | ✓ Negative precipitation | 0 | Set to 0 | Precipitation cannot be negative |
| routes_weather | ✓ Negative visibility | 0 | Set to 0 | Visibility cannot be negative |
| routes_weather | ✓ chanceofrain outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| routes_weather | ✓ chanceoffog outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| routes_weather | ✓ chanceofsnow outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| routes_weather | ✓ chanceofthunder outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| city_weather | ⚠ Temperature outside [-60, 60]°C | 9,132 | Flag; keep | Extreme temperatures — check units (may be Fahrenheit) |
| city_weather | ✓ Negative precipitation | 0 | Set to 0 | Precipitation cannot be negative |
| city_weather | ✓ Negative visibility | 0 | Set to 0 | Visibility cannot be negative |
| city_weather | ✓ chanceofrain outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| city_weather | ✓ chanceoffog outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| city_weather | ✓ chanceofsnow outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |
| city_weather | ✓ chanceofthunder outside [0,100] | 0 | Clip to [0,100] | Probability percentage must be in [0,100] |

## Summary

- **Critical issues**: None that invalidate the dataset
- **Missing data**: Moderate in trucks (load_capacity, fuel_type) and drivers (gender, driving_style)
- **Traffic**: hour column uses non-standard 0/100/200/2300 encoding — normalize by dividing by 100
- **Class imbalance**: delay=1 is ~35% — handled via class weights
- **No actual arrival time**: Regression target cannot be defensibly constructed — classification only
- **Driver-truck link**: `drivers.vehicle_no = trucks.truck_id` (integer FK)

## Treatment Decisions

| Feature | Treatment |
|---------|-----------|
| Missing gender | Impute → 'Unknown' |
| Missing driving_style | Impute → 'Unknown' |
| Missing load_capacity_pounds | Impute → median (fit on train) |
| Missing fuel_type | Impute → 'Unknown' |
| Missing no_of_vehicles | Impute → route-date median then 0 |
| Traffic hour encoding | Divide by 100 (0,100,200... → 0,1,2...) |
| Class imbalance | class_weight='balanced' (LR/RF); scale_pos_weight (XGBoost) |