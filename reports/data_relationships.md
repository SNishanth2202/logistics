# Data Relationships — Freight Logistics Dataset

## Entity-Relationship Overview

```
Drivers (1,300 rows)
   │  vehicle_no = truck_id  (1:1 static assignment)
   │
   ▼
Trucks (1,300 rows)
   │  truck_id
   │
   ▼
TruckSchedule (12,308 rows)   ◄──── route_id ──── Routes (2,352 rows)
   │                                                     │
   │  route_id + departure_date                          │ route_id + date
   ▼                                                     ▼
RoutesWeather (425,712 rows, 6-hourly)     Traffic (2,597,913 rows, hourly)
```

---

## Join Details

### 1. TruckSchedule → Trucks
| Attribute | Value |
|-----------|-------|
| Left table | `truck_schedule_table` |
| Right table | `trucks_table` |
| Join key | `truck_id` (integer) |
| Join type | **inner** (truck must exist) |
| Left rows | 12,308 |
| Right unique keys | 1,300 |
| Expected cardinality | many-to-one (many trips per truck) |
| Duplicate key check | No duplicates in trucks.truck_id ✓ |

### 2. Trucks → Drivers
| Attribute | Value |
|-----------|-------|
| Left table | `trucks_table` |
| Right table | `drivers_table` |
| Join key | `trucks.truck_id = drivers.vehicle_no` |
| Join type | **left** (some trucks may have no driver record) |
| Cardinality | one-to-one (one driver per truck) |
| Duplicate key check | `vehicle_no` is unique in drivers ✓ |

> **NOTE**: There is no `driver_id` in the schedule table. Drivers are linked
> to trucks via `vehicle_no`, which corresponds to `truck_id`. This makes the
> driver-truck relationship static (one driver permanently assigned per truck).

### 3. TruckSchedule → Routes
| Attribute | Value |
|-----------|-------|
| Left table | `truck_schedule_table` |
| Right table | `routes_table` |
| Join key | `route_id` |
| Join type | **inner** (route must exist) |
| Left unique route_ids | 2,352 |
| Right unique route_ids | 2,352 |
| Cardinality | many-to-one |
| Duplicate key check | No duplicates in routes.route_id ✓ |

### 4. TruckSchedule → RoutesWeather
| Attribute | Value |
|-----------|-------|
| Left table | `truck_schedule_table` |
| Right table | `routes_weather` |
| Join key | `route_id` + `date` (departure date, normalized to day) |
| Join type | **left** (some departure dates may have no weather) |
| Aggregation | 6-hourly weather averaged to daily per route |
| Cardinality | many-to-one (after daily aggregation) |
| Coverage | 2019-01-01 → 2019-02-15 (matches schedule dates) ✓ |

### 5. TruckSchedule → Traffic
| Attribute | Value |
|-----------|-------|
| Left table | `truck_schedule_table` |
| Right table | `traffic_table` |
| Join key | `route_id` + `date` + `hour` (departure hour) |
| Join type | **left** (not all departure hours have traffic data) |
| Fallback | Daily route average if exact hour unavailable |
| Hour encoding | Traffic uses 0/100/200/2300 format → divided by 100 |
| Coverage | 2019-01-01 → 2019-02-15 ✓ |

---

## Keys Confirmed Present in Each Table

| Table | Primary Key | Foreign Keys |
|-------|-------------|-------------|
| `truck_schedule_table` | (`truck_id`, `departure_date`) | `truck_id` → trucks, `route_id` → routes |
| `trucks_table` | `truck_id` | — |
| `drivers_table` | `driver_id` | `vehicle_no` → trucks.truck_id |
| `routes_table` | `route_id` | `origin_id`, `destination_id` → city_weather.city_id |
| `routes_weather` | (`route_id`, `Date`) | `route_id` → routes |
| `traffic_table` | (`route_id`, `date`, `hour`) | `route_id` → routes |
| `city_weather` | (`city_id`, `date`, `hour`) | `city_id` → routes.origin_id/destination_id |

---

## Missing Link: city_weather ↔ routes
`routes_table` has `origin_id` and `destination_id` matching `city_weather.city_id`.
This link is not used in the primary model because `routes_weather` already provides
route-level weather. `city_weather` is available as a fallback if needed.
