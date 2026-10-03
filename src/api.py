from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from predict import predict


# ============================================================
# CREATE FASTAPI APP
# ============================================================


app = FastAPI(
    title="Logistics Delivery Delay Prediction API",
    description="API for predicting whether a freight delivery will be delayed.",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Logistics Delivery Prediction API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# INPUT SCHEMA
# ============================================================

class DeliveryInput(BaseModel):

    departure_date: str

    truck_age: float
    load_capacity_pounds: float
    mileage_mpg: float

    fuel_type: str

    driver_age: float
    experience: float
    driver_ratings: float

    average_speed_mph: float
    driving_style: str

    distance: float
    average_hours: float

    weather_wind_speed: float
    weather_precip: float
    weather_humidity: float
    weather_visibility: float

    weather_chanceofrain: float
    weather_chanceoffog: float
    weather_chanceofsnow: float
    weather_chanceofthunder: float

    route_delay_rate_hist: float

    truck_age_category: str


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Freight Delay Prediction API",
        "status": "running"
    }


# ============================================================
# PREDICTION ENDPOINT
# ============================================================

@app.post("/predict")
def make_prediction(data: DeliveryInput):

    record = data.model_dump()

    result = predict(record)

    return result