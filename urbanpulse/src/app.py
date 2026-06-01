import os
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import folium
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import shape
import sys
import requests
from streamlit_lottie import st_lottie

# Add the project root to sys.path to enable clean imports from assets
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assets.theme import get_metric_card_html, apply_urbanpulse_theme, COLORS
import geopandas as gpd
from src.components.map_viz import render_aqi_map

# 1. Page Config
st.set_page_config(
    page_title="UrbanPulse - Bangalore Traffic & AQI",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Premium Dark Mode CSS Injection from assets/style.css
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Define project paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
processed_dir = os.path.join(project_root, "data", "processed")
raw_dir = os.path.join(project_root, "data", "raw")

# 2. Cacheable Data Loaders
@st.cache_data(show_spinner="Synthesizing city vitals...")
def load_historical_data():
    master_path = os.path.join(processed_dir, "master_df.csv")
    if not os.path.exists(master_path):
        return None
    df = pd.read_csv(master_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@st.cache_data(show_spinner="Synthesizing city vitals...")
def load_geojson():
    geojson_path = os.path.join(raw_dir, "bangalore_wards.geojson")
    if not os.path.exists(geojson_path):
        return None
    with open(geojson_path, "r") as f:
        return json.load(f)

# Helper Lottie fetcher
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# Render loading pulse animation in sidebar
lottie_pulse = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_t9gkkhqy.json")
with st.sidebar:
    if lottie_pulse:
        st_lottie(lottie_pulse, height=100, key="sidebar_loader")
    else:
        st.caption("🔄 Synthesizing city vitals...")

# Load datasets
master_df = load_historical_data()
geojson_data = load_geojson()

if master_df is None or geojson_data is None:
    st.error("Error: Scraped historical datasets or boundaries were not found. Please run 'python src/data_download.py' first to scaffold datasets.")
    st.stop()

# Helper data extraction
unique_dates = sorted(master_df['timestamp'].dt.date.unique())
unique_locations = sorted(master_df['location'].unique())

# 3. Hero Section & Custom Command Bar at the Top
st.markdown("""
<div class="glass" style="margin-bottom:1.5rem">
  <h1 style="margin:0; font-weight:700; font-size:2.5rem">UrbanPulse <span style="color:#4F46E5">Bangalore</span></h1>
  <p style="color:#94A3B8; margin:0.5rem 0 0 0">Real-time traffic & air quality intelligence</p>
</div>
""", unsafe_allow_html=True)

# Blinking green dot CSS + Live Caption
st.markdown("""
<style>
@keyframes blink {
    0% { opacity: 0.15; }
    50% { opacity: 1.0; }
    100% { opacity: 0.15; }
}
.blink-dot {
    color: #10B981;
    font-weight: bold;
    animation: blink 1.5s infinite;
    display: inline-block;
    margin-right: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p style="font-size: 0.85rem; color: #94A3B8; margin-top: -0.5rem; margin-bottom: 1rem;"><span class="blink-dot">●</span> Live • Updated 2 min ago</p>', unsafe_allow_html=True)

# 4. Top Command Bar (Filters Panel inside glass container with padding 1rem)
st.markdown('<div class="glass" style="padding:1rem !important; margin-bottom:1.5rem;">', unsafe_allow_html=True)
cmd_col0, cmd_col1, cmd_col2, cmd_col3, cmd_col4 = st.columns([0.5, 3, 1, 1, 1])

with cmd_col0:
    components.html("""
    <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: transparent; display: flex; align-items: flex-end; padding-bottom: 2px; }
    button {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        color: #94A3B8;
        font-size: 1.2rem;
        width: 42px;
        height: 38px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        font-family: sans-serif;
    }
    button:hover {
        background: rgba(79,70,229,0.3);
        border-color: rgba(79,70,229,0.6);
        color: #F1F5F9;
        transform: scale(1.05);
    }
    </style>
    <button onclick="
        var doc = window.parent.document;
        var btn = doc.querySelector('[data-testid=\'stSidebarCollapseButton\'] button');
        if (!btn) btn = doc.querySelector('[data-testid=\'collapsedControl\'] button');
        if (!btn) btn = doc.querySelector('button[kind=\'header\']');
        if (btn) { var s = btn.style.visibility; btn.style.visibility = 'visible'; btn.click(); btn.style.visibility = s; }
    ">☰</button>
    """, height=50)

with cmd_col1:
    selected_ward = st.selectbox(
        "Select Ward",
        options=["All Bangalore"] + unique_locations,
        index=0
    )
    if selected_ward == "All Bangalore":
        selected_locations = unique_locations
    else:
        selected_locations = [selected_ward]

with cmd_col2:
    st.markdown("<div style='height: 1.55rem;'></div>", unsafe_allow_html=True)
    selected_date = st.date_input(
        "Date",
        value=unique_dates[-1],
        min_value=unique_dates[0],
        max_value=unique_dates[-1],
        label_visibility="collapsed"
    )

with cmd_col3:
    st.markdown("<div style='height: 1.85rem;'></div>", unsafe_allow_html=True)
    live_mode = st.toggle("Live Mode", value=True)

with cmd_col4:
    st.markdown("<div style='height: 1.55rem;'></div>", unsafe_allow_html=True)
    refresh_btn = st.button("⟳ Refresh", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Set map canvas style default
map_style = "Cartodb Dark_Matter"

# Filter dataset to selected date and location
day_df = master_df[(master_df['timestamp'].dt.date == selected_date) & (master_df['location'].isin(selected_locations))]

if day_df.empty:
    st.markdown("""
    <div class="glass" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; text-align: center; margin: 2rem 0;">
        <div style="font-size: 4rem; margin-bottom: 1rem; filter: drop-shadow(0 0 10px rgba(79, 70, 229, 0.4));">📡</div>
        <h2 style="font-weight: 700; color: #F1F5F9; margin: 0 0 0.5rem 0; font-family: 'Inter', sans-serif;">No readings yet</h2>
        <p style="color: #94A3B8; margin: 0; font-size: 1rem; font-family: 'Inter', sans-serif;">Data collection in progress</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Get latest snapshot metrics for current hour in selected day
latest_timestamp = day_df['timestamp'].max()
latest_df = day_df[day_df['timestamp'] == latest_timestamp]


# 4. KPI Metrics Area (4 Columns using Centralized HTML Cards)
is_mobile = st.session_state.get('is_mobile', False)
if is_mobile:
    col_a, col_b = st.columns([1, 1])
    col1, col2, col3, col4 = col_a, col_b, col_a, col_b
else:
    col1, col2, col3, col4 = st.columns(4)

# Calculate temporal delta relative to prior hour on selected day
prior_hours = day_df[(day_df['timestamp'] < latest_timestamp)].sort_values("timestamp")
if not prior_hours.empty:
    prior_timestamp = prior_hours['timestamp'].max()
    prior_df = prior_hours[prior_hours['timestamp'] == prior_timestamp]
else:
    prior_df = pd.DataFrame()

# KPI 1: City AQI Card
avg_aqi = int(latest_df['AQI'].mean())
if not prior_df.empty:
    prior_aqi = int(prior_df['AQI'].mean())
    delta_aqi = avg_aqi - prior_aqi
else:
    delta_aqi = -3

delta_sign = "▲" if delta_aqi > 0 else "▼"
delta_color = "badge-red" if delta_aqi > 0 else "badge-green"
badge1_html = f"<span class='badge {delta_color}'>{delta_sign} {abs(delta_aqi)}</span>"
card1_html = get_metric_card_html("🌫️ City AQI", f"{avg_aqi}", "Citywide Index Score", badge1_html)
col1.markdown(card1_html, unsafe_allow_html=True)

# KPI 2: Worst Ward Card
max_aqi_row = latest_df.loc[latest_df['AQI'].idxmax()]
polluted_station = max_aqi_row['location']
polluted_val = int(max_aqi_row['AQI'])
badge2_html = f"<span class='badge badge-red'>AQI: {polluted_val}</span>"
card2_html = get_metric_card_html("⚠️ Worst Ward", f"{polluted_station}", "Highest local emissions", badge2_html)
col2.markdown(card2_html, unsafe_allow_html=True)

# KPI 3: Avg Speed Card
avg_speed = round(latest_df['avg_speed_kmph'].mean(), 1)
avg_congestion = int(latest_df['congestion_level'].mean())
if not prior_df.empty:
    prior_speed = round(prior_df['avg_speed_kmph'].mean(), 1)
    delta_speed = round(avg_speed - prior_speed, 1)
else:
    delta_speed = 1.2

delta_sign_spd = "▲" if delta_speed > 0 else "▼"
delta_color_spd = "badge-green" if delta_speed > 0 else "badge-red"
badge3_html = f"<span class='badge {delta_color_spd}'>{delta_sign_spd} {abs(delta_speed):.1f} km/h</span>"
card3_html = get_metric_card_html("🚗 Avg Speed", f"{avg_speed} km/h", f"Congestion: {avg_congestion}%", badge3_html)
col3.markdown(card3_html, unsafe_allow_html=True)

# KPI 4: Active Alerts Card
active_alerts = []
for idx, row in latest_df.iterrows():
    if row['AQI'] > 150:
        active_alerts.append(f"⚠️ High AQI ({int(row['AQI'])}) at {row['location']}")
    if row['congestion_level'] > 75:
        active_alerts.append(f"🔴 Gridlock ({int(row['congestion_level'])}%) at {row['junction_name']}")

alert_count = len(active_alerts)
alert_badge = "<span class='badge badge-red'>Critical</span>" if alert_count > 0 else "<span class='badge badge-green'>Stable</span>"
card4_html = get_metric_card_html("🔔 Active Alert", f"{alert_count}", "Active scraper triggers", alert_badge)
col4.markdown(card4_html, unsafe_allow_html=True)

# Show alert items inside expansion panel if they exist
if active_alerts:
    with st.expander("🔍 Click to inspect active traffic & environmental alerts"):
        for alert in active_alerts:
            st.warning(alert)

# 5. Core Layout Split: Map & Trends
map_col, chart_col = st.columns([3, 2])

with map_col:
    st.markdown("<h3 style='font-weight: 600; margin-bottom: 0.5rem;'>🗺️ Spatial AQI Choropleth & Traffic Congestion Map</h3>", unsafe_allow_html=True)
    
    # Process GeoJSON and calculate spatially closest monitoring station for all 198 wards (Voronoi Interpolation)
    processed_geojson = {"type": "FeatureCollection", "features": []}
    
    for feature in geojson_data['features']:
        feat_copy = feature.copy()
        geom = shape(feat_copy['geometry'])
        centroid = geom.centroid
        c_lon, c_lat = centroid.x, centroid.y
        
        # Calculate closest station
        min_dist = float('inf')
        closest_aqi = 100
        closest_location = "BTM Layout"
        
        for idx, row in latest_df.iterrows():
            s_lat, s_lon = row['latitude'], row['longitude']
            dist = (c_lat - s_lat)**2 + (c_lon - s_lon)**2
            if dist < min_dist:
                min_dist = dist
                closest_aqi = row['AQI']
                closest_location = row['location']
                
        feat_copy['properties']['assigned_aqi'] = closest_aqi
        feat_copy['properties']['assigned_station'] = closest_location
        feat_copy['properties']['WARD_NO'] = feature['properties'].get('WARD_NO', '')
        feat_copy['properties']['WARD_NAME'] = feature['properties'].get('WARD_NAME', '')
        processed_geojson['features'].append(feat_copy)
        
    # Convert processed GeoJSON to GeoDataFrame for the GIS visualizer
    ward_gdf = gpd.GeoDataFrame.from_features(processed_geojson["features"])
    ward_gdf.set_crs(epsg=4326, inplace=True)
    
    # Render using the modular custom GIS component (auto-detects mobile height!)
    render_aqi_map(ward_gdf, latest_df)

with chart_col:
    st.markdown("<h3 style='font-weight: 600; margin-bottom: 0.5rem;'>📈 Daily Scraper Trend Metrics</h3>", unsafe_allow_html=True)
    
    # Render Trend charts
    day_df_sorted = day_df.sort_values(by="timestamp")
    
    # Generate interactive Plotly Line chart
    fig = go.Figure()
    
    # Add traces per location
    for loc in selected_locations:
        loc_day_df = day_df_sorted[day_df_sorted['location'] == loc]
        if not loc_day_df.empty:
            fig.add_trace(go.Scatter(
                x=loc_day_df['timestamp'].dt.strftime('%H:%M'),
                y=loc_day_df['AQI'],
                mode='lines+markers',
                name=f"{loc} (AQI)",
                line=dict(width=3, shape='spline'),
                marker=dict(size=6),
                hovertemplate="Time: %{x}<br>AQI: %{y}<extra></extra>"
            ))
            
    fig = apply_urbanpulse_theme(fig)
    fig.update_layout(
        title="<b>Hourly Air Quality Index (AQI) Trends</b>",
        title_x=0,
        xaxis_title="Hour (UTC)",
        yaxis_title="AQI Value",
        legend_title="Locations",
        height=260,
        margin=dict(l=20,r=20,t=40,b=20), 
        hovermode='x unified', 
        hoverlabel=dict(bgcolor="#1E293B")
    )
    with st.container():
        st.markdown('<div class="glass" style="margin-bottom:1rem; padding:1rem !important;">', unsafe_allow_html=True)
        st.plotly_chart(fig, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Traffic Congestion chart
    fig2 = go.Figure()
    for loc in selected_locations:
        loc_day_df = day_df_sorted[day_df_sorted['location'] == loc]
        if not loc_day_df.empty:
            fig2.add_trace(go.Scatter(
                x=loc_day_df['timestamp'].dt.strftime('%H:%M'),
                y=loc_day_df['congestion_level'],
                mode='lines+markers',
                name=f"{loc} (Traffic)",
                line=dict(width=3, shape='spline'),
                marker=dict(size=6),
                hovertemplate="Time: %{x}<br>Congestion: %{y}%<extra></extra>"
            ))
            
    fig2 = apply_urbanpulse_theme(fig2)
    fig2.update_layout(
        title="<b>Hourly Traffic Congestion Levels (%)</b>",
        title_x=0,
        xaxis_title="Hour (UTC)",
        yaxis_title="Congestion (%)",
        legend_title="Locations",
        height=260,
        margin=dict(l=20,r=20,t=40,b=20), 
        hovermode='x unified', 
        hoverlabel=dict(bgcolor="#1E293B")
    )
    with st.container():
        st.markdown('<div class="glass" style="margin-bottom:1rem; padding:1rem !important;">', unsafe_allow_html=True)
        st.plotly_chart(fig2, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)

# 6. Environmental Status banner & Forecast Section
st.markdown("---")
weather_col, forecast_col = st.columns(2)

with weather_col:
    st.markdown("### 🌤️ Regional Weather Conditions")
    # Fetch current weather details for the latest hourly point
    latest_w = latest_df.iloc[0]
    w_temp = latest_w.get('temp', 27.0)
    w_hum = latest_w.get('humidity', 60)
    w_wind = latest_w.get('wind_speed', 10.0)
    w_main = latest_w.get('weather_main', "Clear")
    w_rain = latest_w.get('rain_1h', 0.0)
    
    st.write(f"The localized meteorological conditions observed in **Bangalore** at `{latest_timestamp.strftime('%H:%M UTC')}`:")
    
    w_c1, w_c2, w_c3, w_c4 = st.columns(4)
    w_c1.metric("Temperature", f"{w_temp}°C", delta=f"{round(w_temp - 27.0, 1)}C vs base")
    w_c2.metric("Humidity", f"{int(w_hum)}%", delta=f"{int(w_hum - 60)}% vs base")
    w_c3.metric("Wind Speed", f"{w_wind} km/h")
    w_c4.metric("Condition", str(w_main))
    
    if w_rain > 0:
        st.info(f"🌧️ Active precipitation detected: `{w_rain} mm` accumulated in the last hour.")

with forecast_col:
    st.markdown("### 🔮 Next-Hour AI AQI Forecasting")
    # Let's read the machine learning model if it is saved to predict next-hour values!
    model_path = os.path.join(project_root, "models", "aqi_forecast_xgb.joblib")
    
    if os.path.exists(model_path):
        import joblib
        try:
            model = joblib.load(model_path)
            st.write("XGBoost AI forecasting engine active! Local predictions for the upcoming hour:")
            
            # Predict for the 5 locations
            forecast_rows = []
            for loc in selected_locations:
                loc_latest = latest_df[latest_df['location'] == loc]
                if not loc_latest.empty:
                    row_data = loc_latest.iloc[0]
                    
                    # Features: hour, is_weekend, temp, humidity, wind_speed, congestion_level, PM2.5_lag1, rain_1h
                    # Calculate PM2.5_lag1 (which is PM2.5 in latest row since it is the prior hour value for the forecast!)
                    pm25_lag1 = row_data['PM2.5']
                    
                    feat_array = np.array([[
                        float(row_data['hour']),
                        float(row_data['is_weekend']),
                        float(row_data['temp']),
                        float(row_data['humidity']),
                        float(row_data['wind_speed']),
                        float(row_data['congestion_level']),
                        float(pm25_lag1),
                        float(row_data['rain_1h'])
                    ]])
                    
                    pred_val = int(model.predict(feat_array)[0])
                    current_val = int(row_data['AQI'])
                    delta_val = pred_val - current_val
                    
                    forecast_rows.append({
                        "Location": loc,
                        "Current AQI": current_val,
                        "Predicted AQI (Next Hour)": pred_val,
                        "Trend": "📈 Surge" if delta_val > 5 else ("📉 Dissipating" if delta_val < -5 else "➡️ Stable")
                    })
            
            f_df = pd.DataFrame(forecast_rows)
            st.dataframe(f_df, hide_index=True, use_container_width=True)
            
        except Exception as e:
            st.caption(f"Forecasting engine dormant: {e}")
    else:
        st.write("🔮 *AI Forecasting engine is currently sleeping. To activate live next-hour forecasting, please execute the model trainer script:*")
        st.code("python src/train_model.py")

# 7. Last Updated caption footer
st.markdown("---")
local_update_time = latest_timestamp.strftime("%Y-%m-%d %I:%M %p UTC")
st.caption(f"Last updated: {local_update_time} | UrbanPulse System Scraper Daemon Active | Bruhat Bengaluru Mahanagara Palike spatial GIS dataset (198 Wards)")
