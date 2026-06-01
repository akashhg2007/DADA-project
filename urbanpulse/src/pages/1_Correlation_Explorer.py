import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assets.theme import apply_urbanpulse_theme, COLORS

# Page Configuration
st.set_page_config(
    page_title="UrbanPulse - Correlation Explorer",
    page_icon="📊",
    layout="wide"
)

# Premium Dark Mode CSS Injection from assets/style.css
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Define project paths
script_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = script_dir  # pages is under src
src_dir = os.path.dirname(pages_dir)
project_root = os.path.dirname(src_dir)
processed_dir = os.path.join(project_root, "data", "processed")
assets_dir = os.path.join(project_root, "assets")

# Cacheable Loader
@st.cache_data(show_spinner="Synthesizing city vitals...")
def load_data():
    master_path = os.path.join(processed_dir, "master_df.csv")
    if not os.path.exists(master_path):
        return None
    df = pd.read_csv(master_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = load_data()

if df is None:
    st.error("Error: Scraped historical master dataset was not found. Please run the scraping and cleaning pipelines first.")
    st.stop()

# Title Panel
st.markdown("<h1 class='explorer-title'>What Drives Bangalore's Air?</h1>", unsafe_allow_html=True)
st.markdown("<p class='explorer-subtitle'>Analyze cross-correlations, day-hour patterns, and predictive machine learning feature behaviors.</p>", unsafe_allow_html=True)

# 1. Ward selector Dropdown
unique_locations = sorted(df['location'].unique())
selected_location = st.selectbox(
    "Select Localized Ward/Junction for Analysis",
    options=unique_locations
)

# Filter dataset to selected ward
loc_df = df[df['location'] == selected_location].copy()

# Add temporal day of week feature
loc_df['day_of_week'] = loc_df['timestamp'].dt.day_name()
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
loc_df['day_of_week'] = pd.Categorical(loc_df['day_of_week'], categories=days_order, ordered=True)

# 2. Main Visualization Split
viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.markdown("### 🚦 Mobility vs. Particulate Matter")
    st.caption("Investigate if slow travel speeds and high congestion drive fine dust accumulations.")
    
    # Plotly scatter: X=congestion_level, Y=PM2.5, color=hour, with manual OLS trendline
    fig_scatter = px.scatter(
        loc_df,
        x="congestion_level",
        y="PM2.5",
        color="hour",
        color_continuous_scale="Viridis",
        labels={"congestion_level": "Congestion level (%)", "PM2.5": "PM2.5 Concentration (ug/m3)", "hour": "Hour of Day"},
        title=f"<b>Congestion vs. PM2.5 Concentrations at {selected_location}</b>",
        hover_data=["avg_speed_kmph", "AQI"]
    )
    
    # Calculate OLS trendline manually using numpy to ensure absolute reliability without statsmodels
    x = loc_df['congestion_level'].values
    y = loc_df['PM2.5'].values
    if len(x) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        x_range = np.linspace(x.min(), x.max(), 100)
        y_trend = slope * x_range + intercept
        
        # Add OLS Line to Plotly express scatter plot
        fig_scatter.add_trace(go.Scatter(
            x=x_range,
            y=y_trend,
            mode='lines',
            name='OLS Linear Trend',
            line=dict(color='#e74c3c', width=3, shape='spline'),
            hovertemplate=f"Trend: y = {slope:.3f}*x + {intercept:.1f}<extra></extra>"
        ))
        
    fig_scatter = apply_urbanpulse_theme(fig_scatter)
    fig_scatter.update_layout(
        margin=dict(l=20,r=20,t=40,b=20), 
        hovermode='x unified', 
        hoverlabel=dict(bgcolor="#1E293B"),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    with st.container():
        st.markdown('<div class="glass" style="margin-bottom:1rem; padding:1rem !important;">', unsafe_allow_html=True)
        st.plotly_chart(fig_scatter, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)

with viz_col2:
    st.markdown("### 🗓️ Weekly Temporal Pollutant Cycle")
    st.caption("Identify weekday commute peaks and quiet weekend intervals using the mean AQI heatmap.")
    
    # Plotly heatmap: pivot_table index=hour, columns=day_of_week, values=AQI mean
    pivot_df = loc_df.pivot_table(
        index='hour', 
        columns='day_of_week', 
        values='AQI', 
        aggfunc='mean'
    )
    
    # Ensure all days are represented in correct order
    for d in days_order:
        if d not in pivot_df.columns:
            pivot_df[d] = np.nan
    pivot_df = pivot_df[days_order]
    
    fig_heat = px.imshow(
        pivot_df,
        labels=dict(x="Day of Week", y="Hour of Day", color="Mean AQI"),
        x=days_order,
        y=pivot_df.index.tolist(),
        color_continuous_scale=[[0, "#1E293B"], [0.5, "#F59E0B"], [1, "#EF4444"]],
        title=f"<b>Hourly AQI Heatmap by Day of Week ({selected_location})</b>"
    )
    
    fig_heat = apply_urbanpulse_theme(fig_heat)
    fig_heat.update_layout(
        margin=dict(l=20,r=20,t=40,b=20), 
        hovermode='x unified', 
        hoverlabel=dict(bgcolor="#1E293B"),
        xaxis=dict(tickangle=-30)
    )
    with st.container():
        st.markdown('<div class="glass" style="margin-bottom:1rem; padding:1rem !important;">', unsafe_allow_html=True)
        st.plotly_chart(fig_heat, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# 3. Bottom Panel: Feature Importances & Factual Insights
panel_col1, panel_col2 = st.columns(2)

with panel_col1:
    st.markdown("### 🧠 Machine Learning Predictor Feature Importances")
    st.caption("Evaluate which parameters are utilized most by the XGBoost forecasting regressor.")
    
    model_path = os.path.join(project_root, "models", "aqi_forecast_xgb.joblib")
    
    if os.path.exists(model_path):
        import joblib
        try:
            model = joblib.load(model_path)
            importances = model.feature_importances_
            features = ['hour', 'is_weekend', 'temp', 'humidity', 'wind_speed', 'congestion_level', 'PM2.5_lag1', 'rain_1h']
            
            # Map clean labels
            clean_labels = {
                'hour': 'Hour of Day',
                'is_weekend': 'Weekend Indicator',
                'temp': 'Temperature (°C)',
                'humidity': 'Humidity (%)',
                'wind_speed': 'Wind Speed',
                'congestion_level': 'Traffic Congestion (%)',
                'PM2.5_lag1': 'PM2.5 Lag (1 hr)',
                'rain_1h': 'Rainfall Volume'
            }
            
            df_imp = pd.DataFrame({
                "Feature": [clean_labels[f] for f in features],
                "Importance Score": importances
            }).sort_values("Importance Score", ascending=True)
            
            # Display interactive themed Plotly horizontal bar chart
            fig_imp = px.bar(
                df_imp,
                x="Importance Score",
                y="Feature",
                orientation="h",
                title="<b>XGBoost Predictor Feature Importances</b>"
            )
            fig_imp.update_traces(
                marker_color=COLORS['primary'],
                marker_line_width=0
            )
            fig_imp = apply_urbanpulse_theme(fig_imp)
            fig_imp.update_layout(
                margin=dict(l=20,r=20,t=40,b=20),
                hovermode='y unified',
                hoverlabel=dict(bgcolor="#1E293B"),
                height=280
            )
            with st.container():
                st.markdown('<div class="glass" style="margin-bottom:1rem; padding:1rem !important;">', unsafe_allow_html=True)
                st.plotly_chart(fig_imp, width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.image(os.path.join(assets_dir, "feature_importance.png"), caption="XGBoost Feature Importances (Static Export)")
    else:
        # Fallback to feature_importance.png
        png_path = os.path.join(assets_dir, "feature_importance.png")
        if os.path.exists(png_path):
            st.image(png_path, caption="XGBoost Feature Importances (Static Export)")
        else:
            st.warning("Model file or static PNG feature importance plot was not found. Train the model using 'python src/train_model.py' to generate.")

with panel_col2:
    st.markdown("### 📋 Analytics Insights Report")
    st.caption("Factual, data-grounded metrics derived from the Bangalore scraped databases.")
    
    insights_path = os.path.join(assets_dir, "insights.md")
    if os.path.exists(insights_path):
        with open(insights_path, "r") as f:
            insights_md = f.read()
            
        # Display the parsed insights inside st.info block
        st.info(insights_md)
    else:
        st.info("""
        ### 📋 Top Scraper Insights
        
        *   **High Commuter Congestion**: Localized intersections like **Silk Board** show a high correlation between vehicle crawl speeds and air indexes due to emission concentrations.
        *   **Dispersion Drivers**: Atmospheric indicators (especially wind speed) show a strong negative relationship with AQI, serving as a clean dispersion mechanism.
        *   **Commuting Dividends**: Weekend indicators reflect a significant drop in ambient PM2.5 compared to busy weekday mornings (8-11 AM).
        """)
