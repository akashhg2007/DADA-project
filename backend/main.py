import os
import math
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import numpy as np
import joblib
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="UrbanPulse Backend API",
    description="Real-time Traffic and AQI forecast API for Bangalore",
    version="1.0.0"
)

# Enable CORS for Flutter web, emulator, and mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve paths dynamically to support running from workspace root or backend dir
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(BACKEND_DIR)

# Possible search paths for master_df.csv and aqi_forecast_xgb.joblib
DATA_PATHS = [
    os.path.join(BACKEND_DIR, "data", "processed", "master_df.csv"),
    os.path.join(WORKSPACE_ROOT, "data", "processed", "master_df.csv"),
    os.path.join(WORKSPACE_ROOT, "urbanpulse", "data", "processed", "master_df.csv"),
]

MODEL_PATHS = [
    os.path.join(BACKEND_DIR, "models", "aqi_forecast_xgb.joblib"),
    os.path.join(WORKSPACE_ROOT, "models", "aqi_forecast_xgb.joblib"),
    os.path.join(WORKSPACE_ROOT, "urbanpulse", "models", "aqi_forecast_xgb.joblib"),
]

# Global data containers
df_master = None
xgb_model = None

def find_file(paths: List[str]) -> str:
    for path in paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not locate required file in search paths: {paths}")

def load_resources():
    global df_master, xgb_model
    data_path = find_file(DATA_PATHS)
    df_master = pd.read_csv(data_path)
    df_master['timestamp'] = pd.to_datetime(df_master['timestamp'])
    
    model_path = find_file(MODEL_PATHS)
    xgb_model = joblib.load(model_path)

# Load data and model on startup
@app.on_event("startup")
def startup_event():
    try:
        load_resources()
        print("Successfully loaded master dataset and forecasting model.")
    except Exception as e:
        print(f"Error loading resources: {e}")

# Re-load helper if dataset changes or for safety
def get_data_and_model():
    global df_master, xgb_model
    if df_master is None or xgb_model is None:
        try:
            load_resources()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Resources not loaded: {str(e)}")
    return df_master, xgb_model

# Response Pydantic models
class AQIReadingResponse(BaseModel):
    timestamp: str
    ward: str
    aqi: float
    pm25: float
    congestion: float

class JunctionTrafficResponse(BaseModel):
    junction_name: str
    ward: str
    latitude: float
    longitude: float
    congestion_level: float
    avg_speed_kmph: float
    timestamp: str

# What-If scenario request model
class WhatIfRequest(BaseModel):
    trafficAdjust: float # -50 to +50
    rainMm: float        # 0 to 10

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "UrbanPulse Backend API",
        "endpoints": [
            "/api/live/aqi",
            "/api/history/aqi",
            "/api/forecast/aqi",
            "/api/forecast/whatif",
            "/api/traffic/junctions"
        ]
    }

@app.get("/api/live/aqi", response_model=List[AQIReadingResponse])
def get_live_aqi():
    df, _ = get_data_and_model()
    
    latest_readings = []
    unique_locations = df['location'].unique()
    
    for loc in unique_locations:
        loc_df = df[df['location'] == loc].sort_values("timestamp")
        if not loc_df.empty:
            latest_row = loc_df.iloc[-1]
            latest_readings.append(AQIReadingResponse(
                timestamp=latest_row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                ward=latest_row['location'],
                aqi=float(latest_row['AQI']),
                pm25=float(latest_row['PM2.5']),
                congestion=float(latest_row['congestion_level'])
            ))
            
    return latest_readings

@app.get("/api/history/aqi", response_model=List[AQIReadingResponse])
def get_history_aqi(
    ward: str = Query("All", description="Filter by ward name or return 'All'"),
    days: int = Query(7, description="Number of days of history to retrieve")
):
    df, _ = get_data_and_model()
    
    max_time = df['timestamp'].max()
    cutoff_time = max_time - timedelta(days=days)
    
    filtered_df = df[df['timestamp'] >= cutoff_time]
    
    if ward != "All":
        filtered_df = filtered_df[filtered_df['location'].str.lower() == ward.lower()]
        
    filtered_df = filtered_df.sort_values("timestamp")
    
    history_readings = []
    for _, row in filtered_df.iterrows():
        history_readings.append(AQIReadingResponse(
            timestamp=row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            ward=row['location'],
            aqi=float(row['AQI']),
            pm25=float(row['PM2.5']),
            congestion=float(row['congestion_level'])
        ))
        
    return history_readings

@app.get("/api/forecast/aqi", response_model=List[AQIReadingResponse])
def get_forecast_aqi(
    ward: str = Query("All", description="Forecast for specific ward or 'All'")
):
    df, model = get_data_and_model()
    
    unique_locations = df['location'].unique()
    if ward != "All":
        if ward not in unique_locations:
            raise HTTPException(
                status_code=404, 
                detail=f"Ward '{ward}' not found. Available wards: {list(unique_locations)}"
            )
        wards_to_forecast = [ward]
    else:
        wards_to_forecast = unique_locations
        
    forecast_results = []
    num_hours = 24
    
    for loc in wards_to_forecast:
        loc_history = df[df['location'] == loc].sort_values("timestamp")
        if loc_history.empty:
            continue
        latest_row = loc_history.iloc[-1]
        
        current_pm25_lag = float(latest_row['PM2.5'])
        latest_time = latest_row['timestamp']
        base_temp = float(latest_row['temp'])
        base_humidity = float(latest_row['humidity'])
        base_wind = float(latest_row['wind_speed'])
        
        for h in range(1, num_hours + 1):
            future_time = latest_time + timedelta(hours=h)
            future_hour = future_time.hour
            is_weekend = 1 if future_time.weekday() >= 5 else 0
            
            # Diurnal traffic variation template
            if is_weekend == 0:
                if 8 <= future_hour <= 11 or 17 <= future_hour <= 20:
                    hourly_traffic = latest_row['congestion_level'] * 1.3
                elif 23 <= future_hour or future_hour <= 5:
                    hourly_traffic = latest_row['congestion_level'] * 0.3
                else:
                    hourly_traffic = latest_row['congestion_level'] * 0.95
            else:
                if 12 <= future_hour <= 15 or 18 <= future_hour <= 21:
                    hourly_traffic = latest_row['congestion_level'] * 0.8
                else:
                    hourly_traffic = latest_row['congestion_level'] * 0.4
                    
            simulated_traffic = max(0.0, min(100.0, hourly_traffic))
            
            # Diurnal weather oscillation model
            temp_t = base_temp + 3.0 * math.cos((future_hour - 14) * (2 * math.pi / 24.0))
            temp_t = max(18.0, min(35.0, round(temp_t, 2)))
            
            humidity_t = base_humidity - 2.5 * math.cos((future_hour - 14) * (2 * math.pi / 24.0))
            humidity_t = max(35.0, min(100.0, int(humidity_t)))
            
            # Feature array: hour, is_weekend, temp, humidity, wind_speed, congestion_level, PM2.5_lag1, rain_1h
            feat_array = np.array([[
                float(future_hour),
                float(is_weekend),
                float(temp_t),
                float(humidity_t),
                float(base_wind),
                float(simulated_traffic),
                float(current_pm25_lag),
                0.0 # rain_val
            ]])
            
            pred_aqi = int(model.predict(feat_array)[0])
            pred_aqi = max(10, pred_aqi)
            
            forecast_results.append(AQIReadingResponse(
                timestamp=future_time.strftime("%Y-%m-%d %H:%M:%S"),
                ward=loc,
                aqi=float(pred_aqi),
                pm25=float(pred_aqi / 2.0),
                congestion=float(simulated_traffic)
            ))
            
            current_pm25_lag = pred_aqi / 2.0
            
    return forecast_results

@app.post("/api/forecast/whatif", response_model=List[AQIReadingResponse])
def post_forecast_whatif(
    request: WhatIfRequest,
    ward: str = Query("All", description="Forecast for specific ward or 'All'")
):
    df, model = get_data_and_model()
    
    unique_locations = df['location'].unique()
    if ward != "All":
        if ward not in unique_locations:
            raise HTTPException(
                status_code=404, 
                detail=f"Ward '{ward}' not found. Available wards: {list(unique_locations)}"
            )
        wards_to_forecast = [ward]
    else:
        wards_to_forecast = unique_locations
        
    forecast_results = []
    num_hours = 24
    
    for loc in wards_to_forecast:
        loc_history = df[df['location'] == loc].sort_values("timestamp")
        if loc_history.empty:
            continue
        latest_row = loc_history.iloc[-1]
        
        current_pm25_lag = float(latest_row['PM2.5'])
        latest_time = latest_row['timestamp']
        base_temp = float(latest_row['temp'])
        base_humidity = float(latest_row['humidity'])
        base_wind = float(latest_row['wind_speed'])
        
        for h in range(1, num_hours + 1):
            future_time = latest_time + timedelta(hours=h)
            future_hour = future_time.hour
            is_weekend = 1 if future_time.weekday() >= 5 else 0
            
            # Diurnal traffic variation template
            if is_weekend == 0:
                if 8 <= future_hour <= 11 or 17 <= future_hour <= 20:
                    hourly_traffic = latest_row['congestion_level'] * 1.3
                elif 23 <= future_hour or future_hour <= 5:
                    hourly_traffic = latest_row['congestion_level'] * 0.3
                else:
                    hourly_traffic = latest_row['congestion_level'] * 0.95
            else:
                if 12 <= future_hour <= 15 or 18 <= future_hour <= 21:
                    hourly_traffic = latest_row['congestion_level'] * 0.8
                else:
                    hourly_traffic = latest_row['congestion_level'] * 0.4
                    
            # Apply traffic adjustment percentage (-50% to +50%)
            simulated_traffic = hourly_traffic * (1.0 + request.trafficAdjust / 100.0)
            simulated_traffic = max(0.0, min(100.0, simulated_traffic))
            
            # Diurnal weather oscillation model
            temp_t = base_temp + 3.0 * math.cos((future_hour - 14) * (2 * math.pi / 24.0))
            temp_t = max(18.0, min(35.0, round(temp_t, 2)))
            
            humidity_t = base_humidity - 2.5 * math.cos((future_hour - 14) * (2 * math.pi / 24.0))
            humidity_t = max(35.0, min(100.0, int(humidity_t)))
            
            # Feature array: hour, is_weekend, temp, humidity, wind_speed, congestion_level, PM2.5_lag1, rain_1h
            feat_array = np.array([[
                float(future_hour),
                float(is_weekend),
                float(temp_t),
                float(humidity_t),
                float(base_wind),
                float(simulated_traffic),
                float(current_pm25_lag),
                float(request.rainMm) # Apply what-if rain value
            ]])
            
            pred_aqi = int(model.predict(feat_array)[0])
            pred_aqi = max(10, pred_aqi)
            
            forecast_results.append(AQIReadingResponse(
                timestamp=future_time.strftime("%Y-%m-%d %H:%M:%S"),
                ward=loc,
                aqi=float(pred_aqi),
                pm25=float(pred_aqi / 2.0),
                congestion=float(simulated_traffic)
            ))
            
            current_pm25_lag = pred_aqi / 2.0
            
    return forecast_results

@app.get("/api/traffic/junctions", response_model=List[JunctionTrafficResponse])
def get_traffic_junctions():
    df, _ = get_data_and_model()
    
    unique_junctions = df['junction_name'].unique()
    latest_junction_data = []
    
    for junc in unique_junctions:
        junc_df = df[df['junction_name'] == junc].sort_values("timestamp")
        if not junc_df.empty:
            latest_row = junc_df.iloc[-1]
            latest_junction_data.append(JunctionTrafficResponse(
                junction_name=latest_row['junction_name'],
                ward=latest_row['location'],
                latitude=float(latest_row['latitude']),
                longitude=float(latest_row['longitude']),
                congestion_level=float(latest_row['congestion_level']),
                avg_speed_kmph=float(latest_row['avg_speed_kmph']),
                timestamp=latest_row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            ))
            
    return latest_junction_data
