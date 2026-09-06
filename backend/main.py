import pandas as pd
from datetime import datetime

from rule_engine import analyze_weather_data
from m4_processor import process_row

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import joblib
import numpy as np
import requests

from fastapi.middleware.cors import CORSMiddleware


# =====================================
# CONFIGURATION
# =====================================

MAX_HISTORY = 100
MAX_PREDICTION_HISTORY = 100


# =====================================
# STORE DATA SEPARATELY FOR EACH STATION
# =====================================

station_states = {}


def get_station_state(station_id):

    if station_id not in station_states:

        station_states[station_id] = {

            "weather_history": [],

            "prediction_history": [],

            "overall_health": 100,

            "feature_health": {
                "temperature": 100,
                "humidity": 100,
                "pressure": 100,
                "wind_speed": 100,
                "rainfall": 100
            }
        }

    return station_states[station_id]


# =====================================
# WEATHER STATIONS
# =====================================

STATIONS = [

    {
        "id": "AWS_001",
        "city": "Pune",
        "region": "Maharashtra",
        "latitude": 18.52,
        "longitude": 73.86
    },

    {
        "id": "AWS_002",
        "city": "Mumbai",
        "region": "Maharashtra",
        "latitude": 19.07,
        "longitude": 72.87
    },

    {
        "id": "AWS_003",
        "city": "Nashik",
        "region": "Maharashtra",
        "latitude": 20.01,
        "longitude": 73.78
    },

    {
        "id": "AWS_004",
        "city": "Delhi",
        "region": "NCT Delhi",
        "latitude": 28.61,
        "longitude": 77.21
    },

    {
        "id": "AWS_005",
        "city": "Bengaluru",
        "region": "Karnataka",
        "latitude": 12.97,
        "longitude": 77.59
    },

    {
        "id": "AWS_006",
        "city": "Kolkata",
        "region": "West Bengal",
        "latitude": 22.57,
        "longitude": 88.36
    },

    {
        "id": "AWS_007",
        "city": "Jaipur",
        "region": "Rajasthan",
        "latitude": 26.91,
        "longitude": 75.78
    }
]


# =====================================
# FASTAPI APP
# =====================================

app = FastAPI(
    title="AWS Anomaly Detection API",
    description="Real-time anomaly detection using Open-Meteo + M2 + M3 + M4",
    version="1.0.0"
)


# =====================================
# CORS CONFIGURATION
# =====================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =====================================
# LOAD M2 MODEL
# =====================================
model = joblib.load(
    "models/isolation_forest_model.pkl"
)

scaler = joblib.load(
    "models/scaler.pkl"
)


# =====================================
# INPUT DATA MODEL
# =====================================

class WeatherData(BaseModel):

    pressure: float
    temperature: float
    humidity: float
    wind_speed: float
    rainfall: float


# =====================================
# HOME API
# =====================================

@app.get("/")
def home():

    return {
        "message": "AWS Anomaly Detection API is running",
        "status": "online"
    }


# =====================================
# HEALTH CHECK API
# =====================================

@app.get("/health")
def health_check():

    return {

        "status": "healthy",

        "service": "AWS Anomaly Detection API",

        "model_loaded": True,

        "total_stations": len(STATIONS),

        "active_station_states": len(station_states),

        "timestamp": str(datetime.now())
    }


# =====================================
# MAIN ANOMALY DETECTION PIPELINE
# M2 → M3 → M4
# =====================================

def run_anomaly_pipeline(
    data: WeatherData,
    station_id: str
):

    # =====================================
    # GET THIS STATION'S STATE
    # =====================================

    state = get_station_state(station_id)

    weather_history = state["weather_history"]

    prediction_history = state["prediction_history"]

    overall_health = state["overall_health"]

    feature_health = state["feature_health"]


    # =====================================
    # M2: ISOLATION FOREST
    # =====================================

    input_data = np.array([[
    data.temperature,
    data.humidity,
    data.pressure,
    data.wind_speed,
    data.rainfall
]])

    scaled_data = scaler.transform(input_data)

    prediction = model.predict(scaled_data)[0]

    anomaly_score = model.decision_function(
        scaled_data
    )[0]

    ml_prediction = 1 if prediction == -1 else 0

    ml_status = (
        "Anomaly"
        if prediction == -1
        else "Normal"
    )


    # =====================================
    # CURRENT WEATHER READING
    # =====================================

    current_timestamp = datetime.now()

    current_reading = {

        "timestamp": current_timestamp,

        "temperature": data.temperature,

        "humidity": data.humidity,

        "pressure": data.pressure,

        "wind_speed": data.wind_speed,

        "rainfall": data.rainfall
    }


    # =====================================
    # STORE WEATHER HISTORY
    # =====================================

    weather_history.append(current_reading)

    if len(weather_history) > MAX_HISTORY:
        weather_history.pop(0)


    # =====================================
    # M3: RULE ENGINE
    # =====================================

    history_df = pd.DataFrame(weather_history)

    m3_results = analyze_weather_data(history_df)


    # =====================================
    # GET CURRENT M3 RESULTS
    # =====================================

    current_m3_results = []

    rule_anomaly = False

    rule_anomaly_types = []

    rule_features = []

    rule_reasons = []


    for result in m3_results:

        if result.timestamp == current_timestamp:

            current_m3_results.append({

                "anomaly": result.anomaly,

                "anomaly_type": result.anomaly_type,

                "feature": result.feature,

                "value": result.value,

                "timestamp": str(result.timestamp),

                "reason": result.reason
            })


            if result.anomaly:

                rule_anomaly = True

                rule_anomaly_types.append(
                    result.anomaly_type
                )


                if result.feature is not None:

                    rule_features.append(
                        result.feature
                    )


                if result.reason:

                    rule_reasons.append(
                        result.reason
                    )


    # =====================================
    # PREPARE M2 + M3 DATA FOR M4
    # =====================================

    m4_input = {

        "timestamp": current_timestamp,

        "temperature": data.temperature,

        "humidity": data.humidity,

        "pressure": data.pressure,

        "wind_speed": data.wind_speed,

        "rainfall": data.rainfall,


        # M2 OUTPUT

        "ml_prediction": ml_prediction,

        "ml_status": ml_status,

        "anomaly_score": float(anomaly_score),


        # M3 OUTPUT

        "rule_anomaly": rule_anomaly,


        "rule_anomaly_type": (

            ", ".join(
                dict.fromkeys(rule_anomaly_types)
            )

            if rule_anomaly_types

            else "NORMAL"
        ),


        "rule_feature": (

            ", ".join(
                dict.fromkeys(
                    str(feature)
                    for feature in rule_features
                )
            )

            if rule_features

            else None
        ),


        "rule_reason": (

            " | ".join(
                dict.fromkeys(rule_reasons)
            )

            if rule_reasons

            else ""
        )
    }


    # =====================================
    # M4: RISK + EXPLANATION + HEALTH
    # =====================================

    m4_result = process_row(

        row=m4_input,

        previous_health=overall_health,

        feature_health=feature_health
    )


    # =====================================
    # UPDATE ONLY THIS STATION'S HEALTH
    # =====================================

    state["overall_health"] = (
        m4_result["sensor_health"]
    )

    state["feature_health"] = (
        m4_result["feature_health"]
    )


    # =====================================
    # FINAL RESULT
    # =====================================

    final_result = {

        "timestamp": str(current_timestamp),


        "weather_data": {

            "temperature": data.temperature,

            "humidity": data.humidity,

            "pressure": data.pressure,

            "wind_speed": data.wind_speed,

            "rainfall": data.rainfall
        },


        "m2": {

            "ml_prediction": ml_prediction,

            "ml_status": ml_status,

            "anomaly_score": float(anomaly_score)
        },


        "m3": current_m3_results,


        "m4": {

            "risk_score": m4_result["risk_score"],

            "confidence": m4_result["confidence"],

            "severity": m4_result["severity"],

            "explanation": m4_result["explanation"],

            "sensor_health": m4_result["sensor_health"],

            "feature_health": m4_result["feature_health"]
        },


        "history_size": len(weather_history)
    }


    # =====================================
    # STORE PREDICTION HISTORY
    # =====================================

    prediction_history.append(final_result)

    if len(prediction_history) > MAX_PREDICTION_HISTORY:
        prediction_history.pop(0)


    return final_result


# =====================================
# MANUAL PREDICTION API
# =====================================

@app.post("/predict/{station_id}")
def predict_anomaly(
    station_id: str,
    data: WeatherData
):

    return run_anomaly_pipeline(
        data=data,
        station_id=station_id
    )

# =====================================
# LIVE WEATHER + ANOMALY DETECTION API
# =====================================

@app.get("/predict/live")
def predict_live():

    results = []

    for station in STATIONS:

        try:

            latitude = station["latitude"]
            longitude = station["longitude"]

            # Open-Meteo API
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={latitude}"
                f"&longitude={longitude}"
                "&current="
                "temperature_2m,"
                "relative_humidity_2m,"
                "surface_pressure,"
                "wind_speed_10m,"
                "precipitation"
            )

            response = requests.get(url, timeout=10)

            response.raise_for_status()

            weather_response = response.json()

            current = weather_response.get("current", {})

            # Create WeatherData object
            weather_data = WeatherData(

                temperature=float(
                    current.get("temperature_2m", 0)
                ),

                humidity=float(
                    current.get("relative_humidity_2m", 0)
                ),

                pressure=float(
                    current.get("surface_pressure", 0)
                ),

                wind_speed=float(
                    current.get("wind_speed_10m", 0)
                ),

                rainfall=float(
                    current.get("precipitation", 0)
                )
            )


            # Run M2 → M3 → M4 pipeline
            prediction = run_anomaly_pipeline(

                data=weather_data,

                station_id=station["id"]

            )


            # Add station information
            results.append({

                "station": station,

                "weather_data":
                    prediction["weather_data"],

                "m2":
                    prediction["m2"],

                "m3":
                    prediction["m3"],

                "m4":
                    prediction["m4"],

                "timestamp":
                    prediction["timestamp"]

            })


        except Exception as e:

            print(
                f"Error processing "
                f"{station['id']}: {str(e)}"
            )

            results.append({

                "station": station,

                "error": str(e)

            })


    return {

        "status": "success",

        "total_stations": len(STATIONS),

        "stations": results,

        "timestamp": str(datetime.now())

    }
# =====================================
# GET HISTORY OF ONE STATION
# =====================================

@app.get("/history/{station_id}")
def get_history(station_id: str):

    state = get_station_state(
        station_id
    )

    return {

        "station_id": station_id,

        "count": len(
            state["prediction_history"]
        ),

        "data": state["prediction_history"]
    }


# =====================================
# GET SYSTEM STATUS
# =====================================

@app.get("/system/status")
def get_system_status():

    station_status = {}


    for station_id, state in station_states.items():

        latest_result = (

            state["prediction_history"][-1]

            if state["prediction_history"]

            else None
        )


        station_status[station_id] = {

            "weather_history_size":
                len(state["weather_history"]),

            "prediction_history_size":
                len(state["prediction_history"]),

            "sensor_health":
                state["overall_health"],

            "feature_health":
                state["feature_health"],

            "latest_result":
                latest_result
        }


    return {

        "backend_status": "online",

        "model_status": "loaded",

        "total_stations": len(STATIONS),

        "active_station_states": len(station_states),

        "stations": station_status
    }