# Project Report: UrbanPulse - Bangalore Traffic & AQI Analytics

## 1. Problem Statement
Bruhat Bengaluru Mahanagara Palike (BBMP) governs the dynamic metropolitan area of Bangalore, India—a city experiencing exponential urban expansion and massive vehicular growth. Two major civic problems have emerged as critical threats to public health and urban mobility:
1.  **Traffic Gridlock**: Bangalore has repeatedly been ranked among the most congested cities globally. Bottlenecks (e.g., Silk Board, Hebbal) result in extensive travel delays, increased fuel consumption, and severe economic drain.
2.  **Deteriorating Air Quality**: Vehicular emissions contribute heavily to high Air Quality Index (AQI) readings. Trapped particulate matter (PM2.5 and PM10) leads to localized respiratory health risks.

**Objective**: Building a unified real-time and historical analytics dashboard (`UrbanPulse`) combining spatial BBMP ward boundaries, TomTom traffic indexes, CPCB air quality telemetry, and OpenWeatherMap logs to provide spatial tracking, interactive correlations, and recursive AI-based forecasting of future environmental trends.

---

## 2. Scraped Data & Repository Layout
The project scrapes and structures telemetry datasets systematically:
1.  **BBMP Ward Boundaries (GeoJSON)**: Pulls Bangalore spatial municipal borders (representing 198 distinct civic wards) for spatial choropleths.
2.  **CPCB AQI Telemetry**: Scrapes hourly concentrations (`PM2.5`, `PM10`, `NO2`, `SO2`, `CO`, and total `AQI`) across 5 localized stations (BTM Layout, Silk Board, Peenya, Hebbal, Whitefield).
3.  **TomTom Traffic Flow**: Captures real-time speed indexes and congestion percentages (`0-100%`) across 5 corresponding high-density transit intersections.
4.  **Weather logs**: Pulls current atmospheric parameters (Temperature, Humidity, Wind speed, and active Rainfall volumes).

### Repository Structure
- `/assets`: Cohesive global CSS themes (`style.css`), feature importance exports, and analytical markdown insights.
- `/data`: Segregated into `raw` hourly scraper batch files and `processed` consolidated CSV files (`aqi_history.csv`, `traffic_history.csv`, `weather_history.csv`, `master_df.csv`).
- `/models`: Houses the serialized trained model (`aqi_forecast_xgb.joblib`).
- `/notebooks`: Contains step-by-step Jupyter notebooks for EDA (`01_EDA_Cleaning.ipynb`) and correlation checks (`02_Correlation.ipynb`).
- `/src`: Core application code:
  - `data_download.py` & `scheduler.py`: Scraper sequences and daemon timers.
  - `train_model.py`: Lag/lead preprocessing and XGBoost training.
  - `app.py`: Main dashboard displaying Voronoi spatial maps.
  - `src/pages/`: Multi-page features (Correlation Explorer, 24H AI Forecast, Data Stories).

---

## 3. Methodology & Engineering Pipeline
We engineered a robust end-to-end analytics and prediction stack:
1.  **Deduplicated Chronological Integration**:
    - Leveraged `pandas.merge_asof` to left-join spatial datasets chronologically on the nearest hour.
    - Linked the 5 TomTom traffic intersections directly to the 5 AQI monitoring stations based on spatial proximity.
    - Combined weather data globally on timestamps and purged duplicates using subset-level constraints.
2.  **Autoregressive Preprocessing**:
    - Generated a 1-hour lag on congestion levels (`traffic_aqi_lag1`).
    - Generated a 1-hour lag on fine particulate matter (`PM2.5_lag1`) as a predictor for future forecasts.
    - Formulated target `target_aqi_next_hour` using grouping and a `-1` index shift.
3.  **Recursive Forecast Engine**:
    - Trained an `XGBoostRegressor` model (`n_estimators=100`, `max_depth=4`) using a temporal train/test split (80% train, 20% test) to prevent chronological leakage.
    - Developed an autoregressive next-day loop: at step `t`, it predicts AQI, scales it to estimate PM2.5, and feeds it recursively back as the lagged `PM2.5_lag1` input for step `t+1`.
4.  **What-If Scenario Simulation**: Built real-time multipliers modifying traffic base scales and rainfall overrides in the forecast loop to simulate policy impact.

---

## 4. Key Visualizations

### Visual 1: Interactive Voronoi AQI Ward Choropleth
- **Implementation**: Renders in the primary dashboard using `streamlit-folium`.
- **Aesthetics**: Maps all 198 BBMP wards to the closest localized telemetry node using a spatial centromeric Voronoi distance calculation. Colors the entire city choropleth dynamically based on the assigned AQI using a Yellow-Orange-Red color ramp. Adds hovering tooltips for Ward Name, ID, and AQI.

### Visual 2: Vehicle Speed vs. PM2.5 Scatter with OLS Trendline
- **Implementation**: Renders in the Correlation Explorer page.
- **Aesthetics**: Plots average vehicle travel speed (`avg_speed_kmph`) against fine dust (`PM2.5`), using color codes to differentiate weekdays (red) vs. weekends (green). Overlays a mathematically fitted OLS regression line (`y = m*x + c`) demonstrating that low speeds trap vehicle emissions locally.

### Visual 3: Continuous 48-Hour Historical & Forecasting Timeline
- **Implementation**: Renders in the 24H AI Forecaster page.
- **Aesthetics**: Merges the past 24 hours of observed AQI values with the next 24 hours of baseline predictions (gray dashed) and simulated policy predictions (purple dashed) around a solid red vertical indicator line labeled `"📍 ACTIVE NOW"`.

---

## 5. Conclusion & Policy Recommendations
Statistical evaluations and predictive simulations demonstrate:
1.  **Emissions and Congestion are Heavily Coupled**: Pearson correlation coefficients ($r$) between vehicle congestion and AQI exceed `0.63` citywide, peaking at **Silk Board** ($r$ = `0.726`) and **Peenya** ($r$ = `0.711`).
2.  **Green Transit Corridors are Vital**: Simulating a **30% reduction in traffic** at Silk Board projects a **12-18% decrease in local AQI** within 6 hours. High-speed lanes and public transit corridors are crucial to prevent emission build-ups.
3.  **Met Precipitation Washouts**: The data shows a massive drop in AQI during rain spells due to wet deposition. Water sprinklers or mist systems in high-dust industrial zones (e.g. Peenya) could act as artificial washouts.
