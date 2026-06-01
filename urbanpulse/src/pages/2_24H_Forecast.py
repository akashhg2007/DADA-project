import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import joblib
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assets.theme import apply_urbanpulse_theme, COLORS

# Page configuration
st.set_page_config(
    page_title="UrbanPulse - 24H AI Forecast",
    page_icon="🔮",
    layout="wide"
)

# Premium Dark Mode CSS Injection from assets/style.css
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = script_dir
src_dir = os.path.dirname(pages_dir)
project_root = os.path.dirname(src_dir)
processed_dir = os.path.join(project_root, "data", "processed")
models_dir = os.path.join(project_root, "models")

# Load Cacheable Datasets
@st.cache_data(show_spinner="Synthesizing city vitals...")
def load_forecast_data():
    master_path = os.path.join(processed_dir, "master_df.csv")
    if not os.path.exists(master_path):
        return None
    df = pd.read_csv(master_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

master_df = load_forecast_data()

# Load Forecasting Model
@st.cache_resource
def load_xgboost_model():
    model_path = os.path.join(models_dir, "aqi_forecast_xgb.joblib")
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)

model = load_xgboost_model()

if master_df is None:
    st.error("Error: Scraped historical master dataset was not found. Please run the scraping and cleaning pipelines first.")
    st.stop()

if model is None:
    st.warning("🔮 AI Forecasting Engine is currently offline. Please run the model training script to compile the XGBoost pipeline:")
    st.code("python src/train_model.py")
    st.stop()

# Title Panel
st.markdown("<h1 class='forecast-title'>Bangalore 24-Hour AI Forecaster</h1>", unsafe_allow_html=True)
st.markdown("<p class='forecast-subtitle'>Iterative next-day autoregressive predictions with real-time \"What-If\" environmental simulations.</p>", unsafe_allow_html=True)

# 1. Location Selection & Parameters
unique_locations = sorted(master_df['location'].unique())

# Sidebar controls for what-if scenarios
st.sidebar.markdown("<h2 style='font-weight: 800; color: #8e44ad;'>🔮 What-If Simulator</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Simulate green policies or weather changes to observe next-day AQI fluctuations in real-time.")
st.sidebar.markdown("---")

# Sliders
traffic_adjust = st.sidebar.slider(
    "Simulated Traffic Congestion",
    min_value=-50,
    max_value=50,
    value=0,
    step=5,
    format="%+d%%"
)

rain_adjust = st.sidebar.slider(
    "Simulated Hourly Rain (mm)",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.5
)

# Toast notification when sliders move (detect value changes)
if "prev_traffic" not in st.session_state:
    st.session_state["prev_traffic"] = traffic_adjust
if "prev_rain" not in st.session_state:
    st.session_state["prev_rain"] = rain_adjust

if st.session_state["prev_traffic"] != traffic_adjust or st.session_state["prev_rain"] != rain_adjust:
    st.toast("Recalculating AQI...", icon="⚡")
    st.session_state["prev_traffic"] = traffic_adjust
    st.session_state["prev_rain"] = rain_adjust

st.sidebar.markdown("---")
st.sidebar.markdown("### How the Model Predicts")
st.sidebar.caption("The XGBoost model predicts AQI at step `t` using weather, hour, and traffic congestion. The prediction is then scaled and fed recursively back as the lagged fine dust value (`PM2.5_lag1`) for step `t+1`.")

# Main area controls
main_col1, main_col2 = st.columns([1, 2])

with main_col1:
    selected_location = st.selectbox(
        "Select Localized Ward/Junction for Forecast",
        options=unique_locations
    )

# Autoregressive iterative prediction function
def run_iterative_forecast(base_row, num_hours=24, traffic_mult=1.0, rain_val=0.0):
    predictions = []
    
    # Initialize recursive lag value (PM2.5_lag1) from the active latest row
    current_pm25_lag = base_row['PM2.5']
    latest_time = base_row['timestamp']
    
    # Base meteorological cycle averages to interpolate daily weather oscillations safely
    # If simulated rain is added, humidity is raised and temperature cools slightly
    base_temp = base_row['temp']
    base_humidity = base_row['humidity']
    base_wind = base_row['wind_speed']
    
    if rain_val > 0:
        base_humidity = min(100.0, base_humidity + 12.0)
        base_temp = max(18.0, base_temp - 2.5)
        
    for h in range(1, num_hours + 1):
        future_time = latest_time + timedelta(hours=h)
        future_hour = future_time.hour
        is_weekend = 1 if future_time.weekday() >= 5 else 0
        
        # Diurnal traffic variation template based on commute profile
        # Peak mornings 8-11 AM and evenings 5-8 PM
        if is_weekend == 0:
            if 8 <= future_hour <= 11 or 17 <= future_hour <= 20:
                hourly_traffic = base_row['congestion_level'] * 1.3
            elif 23 <= future_hour or future_hour <= 5:
                hourly_traffic = base_row['congestion_level'] * 0.3
            else:
                hourly_traffic = base_row['congestion_level'] * 0.95
        else:
            if 12 <= future_hour <= 15 or 18 <= future_hour <= 21:
                hourly_traffic = base_row['congestion_level'] * 0.8
            else:
                hourly_traffic = base_row['congestion_level'] * 0.4
                
        # Apply simulated what-if traffic multiplier
        simulated_traffic = max(0, min(100, int(hourly_traffic * traffic_mult)))
        
        # Diurnal weather oscillation model
        import math
        temp_t = base_temp + 3.0 * math.cos((future_hour - 14) * (2 * math.pi / 24.0))
        temp_t = max(18.0, min(35.0, round(temp_t, 2)))
        
        humidity_t = base_humidity - 2.5 * math.cos((future_hour - 14) * (2 * math.pi / 24.0))
        humidity_t = max(35.0, min(100.0, int(humidity_t)))
        
        # Structure features array: hour, is_weekend, temp, humidity, wind_speed, congestion_level, PM2.5_lag1, rain_1h
        feat_array = np.array([[
            float(future_hour),
            float(is_weekend),
            float(temp_t),
            float(humidity_t),
            float(base_wind),
            float(simulated_traffic),
            float(current_pm25_lag),
            float(rain_val)
        ]])
        
        # Predict AQI
        pred_aqi = int(model.predict(feat_array)[0])
        pred_aqi = max(10, pred_aqi) # clamp to logical limits
        
        predictions.append({
            "timestamp": future_time,
            "hour_str": future_time.strftime("%I:00 %p"),
            "predicted_aqi": pred_aqi,
            "simulated_congestion": simulated_traffic,
            "simulated_rain": rain_val
        })
        
        # Recursive feed back: convert predicted AQI to PM2.5 using scaling factor
        current_pm25_lag = pred_aqi / 2.0
        
    return pd.DataFrame(predictions)

# Get historical 24 hours and the latest row for selected location
loc_history = master_df[master_df['location'] == selected_location].sort_values("timestamp")
latest_row = loc_history.iloc[-1]

# past 24 hours of history
past_24h = loc_history.tail(24).copy()

# Run both predictions: Baseline (no adjustments) and What-If (with adjustments)
base_forecast = run_iterative_forecast(latest_row, num_hours=24, traffic_mult=1.0, rain_val=0.0)
whatif_forecast = run_iterative_forecast(
    latest_row, 
    num_hours=24, 
    traffic_mult=(1.0 + traffic_adjust / 100.0), 
    rain_val=rain_adjust
)

# 2. Re-run prediction when sliders change and show % change in next 6h AQI
base_avg_6h = base_forecast.head(6)['predicted_aqi'].mean()
whatif_avg_6h = whatif_forecast.head(6)['predicted_aqi'].mean()
pct_change_6h = ((whatif_avg_6h - base_avg_6h) / base_avg_6h) * 100.0

st.markdown("---")

# Layout: Simulation Metric Cards & Plotly Trend Chart
metric_col, chart_col = st.columns([1, 3])

with metric_col:
    st.markdown("#### 🔮 Scenario Impact Panel")
    st.caption("Average changes modeled for the **upcoming 6 hours**:")
    
    # 6H AQI Prediction Metric
    trend_color = "normal"
    if pct_change_6h > 5:
        delta_label = f"+{pct_change_6h:.1f}% Increase"
        st.markdown(f"""
        <div class='scenario-card' style='border-color: #e74c3c;'>
            <h5 style='margin:0; color:#e74c3c; font-weight:800;'>⚠️ AQI SURGE WARNING</h5>
            <p style='font-size: 0.85rem; margin: 4px 0 0 0; color:#7f8c8d;'>Pollution increases inside the 6h horizon.</p>
        </div>
        """, unsafe_allow_html=True)
    elif pct_change_6h < -5:
        delta_label = f"{pct_change_6h:.1f}% Reduction"
        st.markdown(f"""
        <div class='scenario-card' style='border-color: #2ecc71;'>
            <h5 style='margin:0; color:#2ecc71; font-weight:800;'>🌱 ENVIRONMENTAL GAIN</h5>
            <p style='font-size: 0.85rem; margin: 4px 0 0 0; color:#7f8c8d;'>Green policies show immediate cleaner air indexes!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        delta_label = "No significant change"
        st.markdown(f"""
        <div class='scenario-card' style='border-color: #95a5a6;'>
            <h5 style='margin:0; color:#7f8c8d; font-weight:800;'>➡️ STABLE CONDITION</h5>
            <p style='font-size: 0.85rem; margin: 4px 0 0 0; color:#95a5a6;'>Minor localized fluctuations.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.metric(
        label="Simulated Next 6H Mean AQI",
        value=f"{int(whatif_avg_6h)} Index",
        delta=delta_label,
        delta_color="inverse"  # drops are good, increases are bad
    )
    
    st.markdown("##### Scenario Settings Applied:")
    st.write(f"🚗 **Congestion level**: `{traffic_adjust:+.0f}%` of base")
    st.write(f"🌧️ **Precipitation override**: `{rain_adjust:.1f} mm` hourly")

with chart_col:
    st.markdown("#### 📈 Continuous 48-Hour Historical & Forecasting Path")
    st.caption("Consolidates the past 24 hours of observed metrics alongside the upcoming 24 hours of AI scenarios.")
    
    # Continuous timeline preparation
    fig = go.Figure()
    
    # 1. Historical 24h path
    fig.add_trace(go.Scatter(
        x=past_24h['timestamp'],
        y=past_24h['AQI'],
        mode='lines',
        name='Observed History (Past 24h)',
        line=dict(color='#4F46E5', width=3, shape='spline'),
        marker=dict(size=6),
        hovertemplate="Time: %{x}<br>Actual AQI: %{y}<extra></extra>"
    ))
    
    # 2. Baseline Forecast 24h path (dashed)
    # We prep and connect them by adding the latest historical row as the start of the forecast!
    forecast_times = [latest_row['timestamp']] + list(base_forecast['timestamp'])
    base_aqis = [latest_row['AQI']] + list(base_forecast['predicted_aqi'])
    whatif_aqis = [latest_row['AQI']] + list(whatif_forecast['predicted_aqi'])
    
    fig.add_trace(go.Scatter(
        x=forecast_times,
        y=base_aqis,
        mode='lines+markers',
        name='AI Baseline Forecast (No Policy change)',
        line=dict(color='#95a5a6', width=3, shape='spline', dash='dash'),
        marker=dict(size=6),
        hovertemplate="Time: %{x}<br>Baseline Forecast: %{y}<extra></extra>"
    ))
    
    # 3. What-if Forecast 24h path (colored dashed)
    fig.add_trace(go.Scatter(
        x=forecast_times,
        y=whatif_aqis,
        mode='lines+markers',
        name='AI Simulated Scenario (Active Policy)',
        line=dict(color='#8e44ad', width=3, shape='spline', dash='dot'),
        marker=dict(size=6),
        hovertemplate="Time: %{x}<br>Simulated Scenario: %{y}<extra></extra>"
    ))
    
    # Visual boundary line at active current hour (t=0)
    fig.add_vline(
        x=latest_row['timestamp'], 
        line_width=1.5, 
        line_dash="solid", 
        line_color="#e74c3c"
    )
    
    fig.add_annotation(
        x=latest_row['timestamp'],
        y=max(max(past_24h['AQI']), max(whatif_aqis)) * 0.95,
        text="📍 ACTIVE NOW",
        showarrow=False,
        font=dict(color="#e74c3c", size=10, family="Outfit"),
        bgcolor="white",
        bordercolor="#e74c3c",
        borderwidth=1,
        borderpad=4
    )
    
    fig = apply_urbanpulse_theme(fig)
    fig.update_layout(
        xaxis_title="Timeline (Chronological GMT)",
        yaxis_title="Air Quality Index (AQI)",
        margin=dict(l=20,r=20,t=40,b=20), 
        hovermode='x unified', 
        hoverlabel=dict(bgcolor="#1E293B"),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    with st.container():
        st.markdown('<div class="glass" style="margin-bottom:1rem; padding:1rem !important;">', unsafe_allow_html=True)
        st.plotly_chart(fig, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)

# 3. Comparison Breakdown Table
st.markdown("---")
st.markdown("#### 📊 Chronological Hourly Comparison Matrix (Baseline vs. What-If)")

# Build comparative table
table_data = []
for idx in range(24):
    row_base = base_forecast.iloc[idx]
    row_wi = whatif_forecast.iloc[idx]
    
    aqi_base = int(row_base['predicted_aqi'])
    aqi_wi = int(row_wi['predicted_aqi'])
    diff = aqi_wi - aqi_base
    
    table_data.append({
        "Hour Interval": f"+{idx+1} Hour ({row_base['hour_str']})",
        "Baseline Congestion": f"{latest_row['congestion_level']}% (Mean)",
        "Baseline Predicted AQI": aqi_base,
        "Simulated Congestion": f"{row_wi['simulated_congestion']}%",
        "Simulated Predicted AQI": aqi_wi,
        "Net Difference (AQI)": f"{diff:+d}" if diff != 0 else "0"
    })

comparison_df = pd.DataFrame(table_data)

# Custom color-coding formatting for net difference
def highlight_diff(val):
    if '-' in str(val):
        return 'color: #2ecc71; font-weight: bold;'
    elif '+' in str(val):
        return 'color: #e74c3c; font-weight: bold;'
    return 'color: #7f8c8d;'

styled_table = comparison_df.style.map(highlight_diff, subset=["Net Difference (AQI)"])
st.dataframe(styled_table, hide_index=True, use_container_width=True)
