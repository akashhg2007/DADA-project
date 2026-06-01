import os
import random
import requests
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def download_geojson():
    """Downloads Bangalore ward boundary GeoJSON and saves it to data/raw/bangalore_wards.geojson with multiple robust URL fallbacks."""
    urls = [
        "https://github.com/openbangalore/bangalore/raw/master/bangalore-wards.geojson",
        "https://raw.githubusercontent.com/spatialthoughts/qgis-tutorials/master/downloads/bangalore_wards.json",
        "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP.geojson"
    ]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = os.path.join(project_root, "data", "raw")
    output_path = os.path.join(output_dir, "bangalore_wards.geojson")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n[Step 1] Downloading Bangalore ward boundary GeoJSON...")
    
    success = False
    for i, url in enumerate(urls, 1):
        print(f"Attempt {i}: Fetching from {url} ...")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"-> Success! Saved GeoJSON to: {output_path}")
                success = True
                break
            else:
                print(f"-> HTTP Error {response.status_code} for {url}")
        except Exception as e:
            print(f"-> Connection failed for {url}: {e}")
            
    if not success:
        print("ERROR: All boundary download attempts failed.")
        return None
        
    return output_path

def load_and_inspect_geojson(file_path):
    """Loads the downloaded GeoJSON with geopandas and prints stats"""
    if not file_path or not os.path.exists(file_path):
        print("Cannot load GeoJSON: File path is invalid or file does not exist.")
        return
        
    print("\nLoading GeoJSON with GeoPandas to inspect...")
    try:
        gdf = gpd.read_file(file_path)
        total_wards = len(gdf)
        print(f"--- GeoJSON Verification ---")
        print(f"Total wards found in Bangalore: {total_wards}")
        
        name_cols = [col for col in gdf.columns if 'name' in col.lower() or 'ward_no' in col.lower() or 'display_na' in col.lower()]
        if name_cols:
            name_col = name_cols[0]
            sample_wards = gdf[name_col].dropna().unique()
            print(f"Using column '{name_col}' for ward identification.")
            print("Sample ward names:")
            for i, name in enumerate(sample_wards[:3], 1):
                print(f"  {i}. {name}")
        else:
            print("Columns available:")
            print(gdf.columns.tolist())
            print("Sample rows:")
            print(gdf.head(3))
            
    except Exception as e:
        print(f"Error loading or reading GeoJSON: {e}")

def generate_mock_aqi_data(stations, num_rows=100):
    """Generates realistic mock AQI data spanning the last 24h"""
    print(f"Generating {num_rows} rows of realistic mock AQI data for stations: {stations}...")
    
    data = []
    now = datetime.utcnow()
    
    hours_per_station = (num_rows + len(stations) - 1) // len(stations)
    
    for station in stations:
        if station == "Silk Board":
            pm25_base, pm10_base, aqi_base = 80, 140, 160
        elif station == "Peenya":
            pm25_base, pm10_base, aqi_base = 75, 130, 150
        elif station == "BTM Layout":
            pm25_base, pm10_base, aqi_base = 50, 90, 105
        elif station == "Hebbal":
            pm25_base, pm10_base, aqi_base = 55, 100, 110
        else: # Whitefield
            pm25_base, pm10_base, aqi_base = 65, 110, 130
            
        for h in range(hours_per_station):
            time_offset = now - timedelta(hours=h)
            timestamp = time_offset.strftime("%Y-%m-%dT%H:00:00Z")
            
            hour_of_day = time_offset.hour
            if 8 <= hour_of_day <= 11 or 18 <= hour_of_day <= 22:
                diurnal_factor = 1.3
            elif 2 <= hour_of_day <= 5:
                diurnal_factor = 0.75
            else:
                diurnal_factor = 1.0
                
            pm25 = max(10, pm25_base * diurnal_factor + random.uniform(-15, 15))
            pm10 = max(pm25 + 10, pm10_base * diurnal_factor + random.uniform(-25, 25))
            no2 = max(5, 30 * diurnal_factor + random.uniform(-10, 10))
            so2 = max(2, 10 + random.uniform(-4, 4))
            co = max(0.1, 1.0 * diurnal_factor + random.uniform(-0.3, 0.3))
            
            aqi = int(max(pm25 * 1.7, pm10 * 0.95, aqi_base * diurnal_factor + random.uniform(-15, 15)))
            
            data.append({
                "timestamp": timestamp,
                "station": station,
                "PM2.5": round(pm25, 2),
                "PM10": round(pm10, 2),
                "NO2": round(no2, 2),
                "SO2": round(so2, 2),
                "CO": round(co, 2),
                "AQI": aqi
            })
            
    df = pd.DataFrame(data[:num_rows])
    df = df.sort_values(by=["timestamp", "station"]).reset_index(drop=True)
    return df

def fetch_cpcb_aqi():
    """Fetches AQI data from CPCB API or generates realistic mock data if API key is missing"""
    stations = ["BTM Layout", "Silk Board", "Peenya", "Hebbal", "Whitefield"]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    raw_dir = os.path.join(project_root, "data", "raw")
    processed_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    raw_csv_path = os.path.join(raw_dir, f"aqi_{today_str}.csv")
    history_csv_path = os.path.join(processed_dir, "aqi_history.csv")
    
    cpcb_key = os.getenv("CPCB_API_KEY")
    df_new = None
    
    print(f"\n[Step 2] Fetching CPCB AQI data for Bangalore (City ID = 289)...")
    if cpcb_key and cpcb_key.strip() != "":
        print("CPCB API Key found! Attempting to query live air quality data...")
        url = "https://api.data.gov.in/resource/3b01bcb8-0b15-492b-b6f4-c2c3d558a74e"
        params = {
            "api-key": cpcb_key.strip(),
            "format": "json",
            "limit": 1000,
            "filters[city]": "Bengaluru"
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            res_json = response.json()
            
            records = res_json.get("records", [])
            if records:
                print(f"Retrieved {len(records)} records from CPCB API. Filtering and structuring data...")
                raw_api_df = pd.DataFrame(records)
                parsed_rows = []
                
                station_col = [c for c in raw_api_df.columns if 'station' in c.lower()][0]
                update_col = [c for c in raw_api_df.columns if 'update' in c.lower() or 'time' in c.lower()][0]
                pollutant_col = [c for c in raw_api_df.columns if 'pollutant_id' in c.lower() or 'pollutant' in c.lower()][0]
                value_col = [c for c in raw_api_df.columns if 'pollutant_avg' in c.lower() or 'avg' in c.lower() or 'value' in c.lower()][0]
                
                station_groups = raw_api_df.groupby([station_col, update_col])
                for (stat_name, timestamp), group in station_groups:
                    matched_station = None
                    for target in stations:
                        if target.lower() in stat_name.lower():
                            matched_station = target
                            break
                    if not matched_station:
                        continue
                        
                    metrics = {"timestamp": timestamp, "station": matched_station}
                    for _, row in group.iterrows():
                        pol = str(row[pollutant_col]).upper()
                        val = pd.to_numeric(row[value_col], errors='coerce')
                        
                        if "PM2.5" in pol or "PM25" in pol:
                            metrics["PM2.5"] = val
                        elif "PM10" in pol:
                            metrics["PM10"] = val
                        elif "NO2" in pol:
                            metrics["NO2"] = val
                        elif "SO2" in pol:
                            metrics["SO2"] = val
                        elif "CO" in pol:
                            metrics["CO"] = val
                        elif "AQI" in pol or "INDEX" in pol:
                            metrics["AQI"] = val
                            
                    for key in ["PM2.5", "PM10", "NO2", "SO2", "CO", "AQI"]:
                        if key not in metrics:
                            metrics[key] = None
                            
                    if metrics["AQI"] is None and metrics["PM2.5"] is not None:
                        metrics["AQI"] = int(metrics["PM2.5"] * 1.5)
                        
                    parsed_rows.append(metrics)
                
                if parsed_rows:
                    df_new = pd.DataFrame(parsed_rows)
                    print(f"Successfully processed {len(df_new)} rows of live AQI data.")
                else:
                    print("No records matched the selected target stations. Falling back to mock data.")
            else:
                print("CPCB API returned empty records. Falling back to mock data.")
                
        except Exception as e:
            print(f"Failed to fetch live CPCB AQI data due to: {e}. Falling back to mock data.")
            
    if df_new is None:
        if not cpcb_key or cpcb_key.strip() == "":
            print("CPCB API Key is missing or empty in environment variables.")
        df_new = generate_mock_aqi_data(stations, num_rows=100)
        
    df_new.to_csv(raw_csv_path, index=False)
    print(f"Saved raw batch to: {raw_csv_path}")
    
    if os.path.exists(history_csv_path):
        print(f"Loading existing history from: {history_csv_path} ...")
        df_existing = pd.read_csv(history_csv_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        before_count = len(df_combined)
        df_combined = df_combined.drop_duplicates(subset=["timestamp", "station"], keep="last")
        after_count = len(df_combined)
        duplicates_removed = before_count - after_count
        print(f"Appended records. Removed {duplicates_removed} duplicate row(s).")
    else:
        print(f"Creating new historical file: {history_csv_path} ...")
        df_combined = df_new
        
    df_combined = df_combined.sort_values(by=["timestamp", "station"]).reset_index(drop=True)
    df_combined.to_csv(history_csv_path, index=False)
    print(f"Successfully updated AQI history at: {history_csv_path}")
    
    print("\n--- AQI Verification ---")
    print(f"Total rows in new batch: {len(df_new)}")
    print(f"Total rows in accumulated history: {len(df_combined)}")
    print("Sample AQI records (first 3 rows):")
    print(df_combined.head(3).to_string(index=False))

def generate_mock_traffic_data(junctions, num_hours=24):
    """Generates realistic mock traffic data with weekday rush hour spikes (8-11 AM, 5-8 PM)"""
    print(f"Generating realistic mock traffic data for {num_hours} hours across junctions...")
    
    data = []
    now = datetime.utcnow()
    
    for name, coords in junctions.items():
        if name == "Silk Board":
            base_congestion, base_speed = 40, 22
        elif name == "Marathahalli":
            base_congestion, base_speed = 32, 26
        elif name == "Hebbal":
            base_congestion, base_speed = 28, 32
        elif name == "Whitefield":
            base_congestion, base_speed = 34, 28
        else: # Koramangala
            base_congestion, base_speed = 26, 28
            
        for h in range(num_hours):
            time_offset = now - timedelta(hours=h)
            timestamp = time_offset.strftime("%Y-%m-%dT%H:00:00Z")
            
            is_weekday = time_offset.weekday() < 5
            hour = time_offset.hour
            
            if is_weekday:
                if 8 <= hour <= 11 or 17 <= hour <= 20:
                    rush_multiplier = random.uniform(1.8, 2.4)
                elif 23 <= hour or hour <= 5:
                    rush_multiplier = random.uniform(0.15, 0.3)
                else:
                    rush_multiplier = random.uniform(0.8, 1.2)
            else:
                if 12 <= hour <= 15 or 18 <= hour <= 21:
                    rush_multiplier = random.uniform(1.2, 1.6)
                elif 23 <= hour or hour <= 6:
                    rush_multiplier = random.uniform(0.1, 0.25)
                else:
                    rush_multiplier = random.uniform(0.6, 0.9)
            
            congestion = base_congestion * rush_multiplier + random.uniform(-5, 5)
            congestion = max(0, min(100, int(congestion)))
            
            free_flow = 55.0
            avg_speed = free_flow / (1.0 + (congestion / 100.0) * 1.5) + random.uniform(-2, 2)
            avg_speed = max(3.0, min(free_flow, round(avg_speed, 2)))
            
            data.append({
                "timestamp": timestamp,
                "junction_name": name,
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "congestion_level": congestion,
                "avg_speed_kmph": avg_speed
            })
            
    df = pd.DataFrame(data)
    df = df.sort_values(by=["timestamp", "junction_name"]).reset_index(drop=True)
    return df

def fetch_traffic_snapshot():
    """Fetches traffic snapshot data from TomTom API or generates mock data if key is missing"""
    junctions = {
        "Silk Board": {"lat": 12.917, "lon": 77.623},
        "Marathahalli": {"lat": 12.959, "lon": 77.697},
        "Hebbal": {"lat": 13.035, "lon": 77.597},
        "Whitefield": {"lat": 12.969, "lon": 77.750},
        "Koramangala": {"lat": 12.935, "lon": 77.624}
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    raw_dir = os.path.join(project_root, "data", "raw")
    processed_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    raw_csv_path = os.path.join(raw_dir, f"traffic_{today_str}.csv")
    history_csv_path = os.path.join(processed_dir, "traffic_history.csv")
    
    tomtom_key = os.getenv("TOMTOM_API_KEY")
    df_new = None
    
    print(f"\n[Step 3] Fetching traffic snapshots for Bangalore junctions...")
    if tomtom_key and tomtom_key.strip() != "":
        print("TomTom API Key found! Fetching current flow segment details from live API...")
        parsed_rows = []
        now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:00:00Z")
        
        success_count = 0
        for name, coords in junctions.items():
            lat, lon = coords["lat"], coords["lon"]
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative-compact/10/json"
            params = {
                "key": tomtom_key.strip(),
                "point": f"{lat},{lon}"
            }
            
            try:
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                flow_data = response.json().get("flowSegmentData", {})
                
                if flow_data:
                    current_speed = flow_data.get("currentSpeed", 0.0)
                    free_flow_speed = flow_data.get("freeFlowSpeed", 45.0)
                    
                    if free_flow_speed > 0:
                        congestion = max(0, min(100, int((1.0 - (current_speed / free_flow_speed)) * 100)))
                    else:
                        congestion = 0
                        
                    parsed_rows.append({
                        "timestamp": now_str,
                        "junction_name": name,
                        "latitude": lat,
                        "longitude": lon,
                        "congestion_level": congestion,
                        "avg_speed_kmph": float(current_speed)
                    })
                    success_count += 1
                    
            except Exception as e:
                print(f"Warning: Failed to fetch traffic for {name}: {e}")
                
        if success_count == len(junctions):
            df_new = pd.DataFrame(parsed_rows)
            print("Successfully retrieved live traffic for all junctions.")
        else:
            print(f"Retrieved traffic for {success_count}/{len(junctions)} junctions. Falling back to complete mock batch to maintain historical alignment.")
            
    if df_new is None:
        if not tomtom_key or tomtom_key.strip() == "":
            print("TomTom API Key is missing or empty in environment variables.")
        df_new = generate_mock_traffic_data(junctions, num_hours=24)
        
    df_new.to_csv(raw_csv_path, index=False)
    print(f"Saved raw traffic snapshot to: {raw_csv_path}")
    
    if os.path.exists(history_csv_path):
        print(f"Loading existing history from: {history_csv_path} ...")
        df_existing = pd.read_csv(history_csv_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        before_count = len(df_combined)
        df_combined = df_combined.drop_duplicates(subset=["timestamp", "junction_name"], keep="last")
        after_count = len(df_combined)
        duplicates_removed = before_count - after_count
        print(f"Appended records. Removed {duplicates_removed} duplicate row(s).")
    else:
        print(f"Creating new historical file: {history_csv_path} ...")
        df_combined = df_new
        
    df_combined = df_combined.sort_values(by=["timestamp", "junction_name"]).reset_index(drop=True)
    df_combined.to_csv(history_csv_path, index=False)
    print(f"Successfully updated traffic history at: {history_csv_path}")
    
    print("\n--- Traffic Verification ---")
    print(f"Total rows in new batch: {len(df_new)}")
    print(f"Total rows in accumulated history: {len(df_combined)}")
    print("Sample Traffic records (first 3 rows):")
    print(df_combined.head(3).to_string(index=False))

def generate_mock_weather_data(num_hours=24):
    """Generates realistic mock weather data with diurnal temperatures (22-32C) and occasional rain"""
    print(f"Generating realistic mock weather data for {num_hours} hours...")
    
    data = []
    now = datetime.utcnow()
    
    for h in range(num_hours):
        time_offset = now - timedelta(hours=h)
        timestamp = time_offset.strftime("%Y-%m-%dT%H:00:00Z")
        
        # Diurnal temperature cycle: peaks around 2-3 PM (14:00-15:00 UTC corresponds to late evening in IST, but let's use UTC hour directly for smooth sine wave)
        # UTC + 5:30 is IST, so 2 PM IST is 8:30 AM UTC.
        # Sine wave peak around 8:30 AM UTC
        hour_utc = time_offset.hour
        # Diurnal wave centered around 27C, fluctuation of 5C (so 22C to 32C range)
        # Peak temperature at 14:00 local time (8:30 UTC), low at 04:00 local time (22:30 UTC)
        temp = 27.0 + 5.0 * random.uniform(0.8, 1.2) * (random.uniform(0.9, 1.1) * (
            0.5 * (1.0 + (datetime.strptime(timestamp, "%Y-%m-%dT%H:00:00Z").hour - 8.5) / 12.0)
        ))
        
        # Simpler sine based temperature:
        import math
        # peak temp at 14:00 local, which is 8.5 UTC.
        # math.cos((hour_utc - 8.5) * (2 * math.pi / 24.0)) gives 1 at 8.5, -1 at 20.5
        temp_val = 27.0 + 5.0 * math.cos((hour_utc - 8.5) * (2 * math.pi / 24.0)) + random.uniform(-0.5, 0.5)
        temp_val = max(22.0, min(32.0, round(temp_val, 2)))
        
        # Humidity is inversely proportional to temp
        humidity_val = 85.0 - (temp_val - 22.0) * 4.0 + random.uniform(-5, 5)
        humidity_val = max(40.0, min(100.0, int(humidity_val)))
        
        wind_speed_val = max(2.0, round(12.0 + 6.0 * math.sin((hour_utc - 10.0) * (2 * math.pi / 24.0)) + random.uniform(-3, 3), 2))
        
        # 10% chance of rain
        has_rain = random.random() < 0.10
        if has_rain:
            weather_main = "Rain"
            rain_1h = max(0.1, round(random.uniform(0.2, 6.0), 2))
            # rain increases humidity and drops temp slightly
            humidity_val = min(100, humidity_val + 10)
            temp_val = max(22.0, temp_val - 2.0)
        else:
            weather_main = random.choice(["Clear", "Clouds", "Haze", "Clouds"])
            rain_1h = 0.0
            
        data.append({
            "timestamp": timestamp,
            "temp": temp_val,
            "humidity": humidity_val,
            "wind_speed": wind_speed_val,
            "weather_main": weather_main,
            "rain_1h": rain_1h
        })
        
    df = pd.DataFrame(data)
    df = df.sort_values(by=["timestamp"]).reset_index(drop=True)
    return df

def fetch_weather():
    """Fetches weather data for Bangalore from OpenWeatherMap API or generates mock data if key is missing"""
    lat, lon = 12.9716, 77.5946
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    raw_dir = os.path.join(project_root, "data", "raw")
    processed_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    raw_csv_path = os.path.join(raw_dir, f"weather_{today_str}.csv")
    history_csv_path = os.path.join(processed_dir, "weather_history.csv")
    
    owm_key = os.getenv("OPENWEATHER_API_KEY")
    df_new = None
    
    print(f"\n[Step 4] Fetching weather data for Bangalore (lat={lat}, lon={lon})...")
    if owm_key and owm_key.strip() != "":
        print("OpenWeatherMap API Key found! Fetching current weather from API...")
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": owm_key.strip(),
            "units": "metric"
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            w_data = response.json()
            
            if w_data:
                # Convert dt to UTC string hourly
                dt = w_data.get("dt")
                timestamp_str = datetime.utcfromtimestamp(dt).strftime("%Y-%m-%dT%H:00:00Z")
                
                temp = w_data.get("main", {}).get("temp")
                humidity = w_data.get("main", {}).get("humidity")
                wind_speed = w_data.get("wind", {}).get("speed")
                weather_main = w_data.get("weather", [{}])[0].get("main", "Clear")
                
                # rain_1h might be nested in rain.1h
                rain_data = w_data.get("rain", {})
                rain_1h = rain_data.get("1h", 0.0) if isinstance(rain_data, dict) else 0.0
                
                df_new = pd.DataFrame([{
                    "timestamp": timestamp_str,
                    "temp": float(temp) if temp is not None else 25.0,
                    "humidity": int(humidity) if humidity is not None else 60,
                    "wind_speed": float(wind_speed) if wind_speed is not None else 10.0,
                    "weather_main": str(weather_main),
                    "rain_1h": float(rain_1h)
                }])
                print("Successfully retrieved live current weather from OpenWeatherMap.")
                
        except Exception as e:
            print(f"Warning: Failed to fetch live weather: {e}. Falling back to mock data.")
            
    if df_new is None:
        if not owm_key or owm_key.strip() == "":
            print("OpenWeatherMap API Key is missing or empty in environment variables.")
        df_new = generate_mock_weather_data(num_hours=24)
        
    df_new.to_csv(raw_csv_path, index=False)
    print(f"Saved raw weather snapshot to: {raw_csv_path}")
    
    if os.path.exists(history_csv_path):
        print(f"Loading existing history from: {history_csv_path} ...")
        df_existing = pd.read_csv(history_csv_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        before_count = len(df_combined)
        df_combined = df_combined.drop_duplicates(subset=["timestamp"], keep="last")
        after_count = len(df_combined)
        duplicates_removed = before_count - after_count
        print(f"Appended records. Removed {duplicates_removed} duplicate row(s).")
    else:
        print(f"Creating new historical file: {history_csv_path} ...")
        df_combined = df_new
        
    df_combined = df_combined.sort_values(by=["timestamp"]).reset_index(drop=True)
    df_combined.to_csv(history_csv_path, index=False)
    print(f"Successfully updated weather history at: {history_csv_path}")
    
    print("\n--- Weather Verification ---")
    print(f"Total rows in new batch: {len(df_new)}")
    print(f"Total rows in accumulated history: {len(df_combined)}")
    print("Sample Weather records (first 3 rows):")
    print(df_combined.head(3).to_string(index=False))

def main():
    print("==================================================")
    print("         UrbanPulse Data Downloader Script        ")
    print("==================================================")
    
    saved_path = download_geojson()
    load_and_inspect_geojson(saved_path)
    
    fetch_cpcb_aqi()
    
    fetch_traffic_snapshot()
    
    fetch_weather()
    
    print("\n==================================================")
    print("        Data Download Execution Completed!       ")
    print("==================================================")

if __name__ == "__main__":
    main()
