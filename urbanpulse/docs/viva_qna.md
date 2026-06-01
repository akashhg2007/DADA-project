# Academic Viva Q&A - UrbanPulse Bangalore Analytics

This document contains 10 rigorous, high-quality questions and answers prepared for academic viva evaluations, detailing architectural design, data processing pipelines, modeling choices, and scalability recommendations.

---

## 1. Why did you choose XGBoost over a classical Linear Regression model for AQI forecasting?
**Answer**: 
XGBoost (Extreme Gradient Boosting) was selected over Linear Regression for three primary reasons:
1.  **Non-Linear Interactions**: The relationship between environmental factors (such as wind speed, temperature, and humidity), traffic congestion, and Air Quality (AQI) is highly non-linear. For example, wind speed has a non-linear dispersion effect (low wind traps air, but high wind disperses it). Linear Regression struggles to capture these threshold-based and joint-feature interactions without extensive manual polynomial feature engineering.
2.  **Multicollinearity Handling**: Environmental features (like temperature and humidity) and traffic features (like congestion and speed) exhibit high multicollinearity. Linear models are highly sensitive to multicollinearity, leading to unstable coefficient estimations. Decision-tree based ensembles like XGBoost are robust to multicollinearity, as they split on features sequentially based on information gain.
3.  **Outlier & Lag Robustness**: XGBoost handles missing lag offsets and localized outliers robustly through its default tree-routing splits and regularization parameters ($L1$/$L2$), resulting in superior predictive accuracy on unseen test partitions.

---

## 2. How did you handle missing CAAQMS (Continuous Ambient Air Quality Monitoring Systems) data?
**Answer**: 
Environmental telemetry data commonly suffers from missing values due to sensor maintenance or transmission drops. We engineered a robust, two-tiered cleaning pipeline:
1.  **Station-Specific Forward Fill**: We grouped the dataset by the specific monitoring station (`station`) and applied a forward fill (`ffill`) limited to a **maximum window of 2 hours**. This preserves the chronological sequence of the time-series without leaking data across distant hours or separate geographic stations.
2.  **Deletion threshold**: If a sensor was offline for more than 2 consecutive hours, the gaps were deemed too large to interpolate safely, and those rows were dropped (`dropna`) to avoid introducing synthetic bias.
3.  **Outlier Filtering**: Verified that any malfunctioning sensor readings recording an `AQI > 500` (which is the absolute upper bound of the Indian AQI scale) were purged to prevent model distortion.

---

## 3. What is the biggest limitation of this project in its current state?
**Answer**: 
The primary limitation is **Spatial Resolution (Sensor Density)**. 
Bangalore covers over $700 \text{ km}^2$ and has 198 BBMP administrative wards, but CPCB only operates a limited number of active CAAQMS monitoring stations (5 targeted in our pipeline). 
Because we map the entire city's choropleth using a nearest-monitor centromeric Voronoi distance calculation, we assume uniform air quality across wide spatial boundaries. In reality, air quality is a highly localized micro-climate shaped by street canyons, specific construction zones, and localized tree covers, which our 5-node macro-telemetry cannot fully capture.

---

## 4. How would you scale this architecture to monitor all of India?
**Answer**: 
To scale the system to a national level, we would transition to a cloud-native, serverless stream-processing architecture:
1.  **Serverless Scrapers**: Deploy the scraper routines (`data_download.py`) as serverless microservices (e.g., AWS Lambda or Google Cloud Functions) triggered by cron events (AWS EventBridge). This allows thousands of parallel scrapers to fetch data for every Indian city concurrently without server bottlenecks.
2.  **Streaming Ingestion**: Route scraped telemetry from TomTom and CPCB into a real-time ingestion pipeline using Apache Kafka or AWS Kinesis to handle millions of incoming data packets.
3.  **Cloud Data Warehouse**: Store historical logs in a scalable cloud data warehouse like Snowflake or Google BigQuery to allow fast analytical queries on terabytes of spatial data.
4.  **Spatial GIS Databases**: Integrate PostgreSQL with PostGIS extensions to run complex spatial indexing instead of in-memory centromeric calculations.

---

## 5. Show me the exact code where you merge the independent datasets.
**Answer**: 
We utilize `pandas.merge_asof` to perform a chronological left join on the nearest hour. The merge is structured in two steps inside `notebooks/01_EDA_Cleaning.ipynb`:

```python
# Step A: Sort both datasets by the merge key ('timestamp')
traffic = traffic.sort_values('timestamp')
aqi = aqi.sort_values('timestamp')

# Merge Traffic and AQI on nearest timestamp matching locations
merged_df = pd.merge_asof(
    traffic,
    aqi,
    on='timestamp',
    by='location',
    direction='nearest'
)

# Step B: Sort weather data and merge globally on nearest timestamp
weather = weather.sort_values('timestamp')

master_df = pd.merge_asof(
    merged_df.sort_values('timestamp'),
    weather,
    on='timestamp',
    direction='nearest'
)
```

---

## 6. Why did you choose `pd.merge_asof` instead of a standard `pd.merge` inner join?
**Answer**: 
A standard inner join requires exact matching on the join key (`timestamp`). In real-world data collection, independent scrapers, APIs, and cron scrapers execute asynchronously. CPCB might publish its hourly metrics at `10:02:15`, TomTom might capture congestion indexes at `10:00:00`, and weather logs might register at `09:58:30`. 
An exact inner join on these timestamps would result in zero matches, wiping out the entire database. `pd.merge_asof` solves this by matching records on the **nearest chronological hour**, ensuring robust data integration across asynchronous data feeds.

---

## 7. What are the key features utilized in your machine learning forecaster?
**Answer**: 
The `XGBoostRegressor` model utilizes 8 features to predict next-hour AQI:
1.  `hour` (0-23): Captures diurnal cycles (e.g., traffic rush hours, weather patterns).
2.  `is_weekend` (0/1): Represents differences in commercial commute patterns.
3.  `temp` & `humidity`: Capture thermodynamic air expansion and moisture levels.
4.  `wind_speed`: Models atmospheric dispersion of particulates.
5.  `rain_1h`: Captures wet deposition (rain washing particles out of the air).
6.  `congestion_level` (0-100%): Serves as a direct proxy for active vehicle emissions.
7.  `PM2.5_lag1`: The PM2.5 concentration from 1 hour prior, providing temporal autoregressive continuity.

---

## 8. Explain how your recursive 24-hour forecasting loop works.
**Answer**: 
Because we predict next-hour AQI using lagged inputs, we cannot perform standard one-shot multi-step predictions for a 24-hour horizon. We implemented a **recursive autoregressive loop**:
1.  For step $t=1$, we feed the actual observed `PM2.5` from the latest scraper row as the `PM2.5_lag1` feature.
2.  The model predicts the AQI for step $t=1$.
3.  We convert this predicted AQI into an estimated PM2.5 value using our historical scaling factor (`predicted_pm25 = predicted_aqi / 2.0`).
4.  For step $t=2$, we feed this *predicted* PM2.5 value back into the model as the `PM2.5_lag1` input feature.
5.  This process repeats recursively up to $t=24$, allowing the model to project an entire next-day timeline dynamically.

---

## 9. How does the spatial Voronoi interpolation map work in the Streamlit dashboard?
**Answer**: 
To color the 198 BBMP wards in the choropleth map dynamically:
1.  We load the ward boundaries from the GeoJSON file.
2.  In-memory, we compute the centroid coordinate (center of gravity) of each ward polygon using `shapely.geometry.shape`.
3.  We calculate the Euclidean distance from each ward centroid to each of our 5 active monitoring station coordinates.
4.  We assign the ward's AQI property to be the AQI of the **nearest monitoring station**.
5.  This dynamically populates the GeoJSON features properties with `assigned_aqi` values in real-time, allowing Folium to render a complete, colored choropleth across the entire city canvas.

---

## 10. How did you design the "What-If" policy simulation scenario engine?
**Answer**: 
The simulation engine inside `2_24H_Forecast.py` integrates sidebar sliders directly into our recursive forecast loop:
1.  **Traffic Congestion Slider**: Takes adjustments from `-50%` to `+50%`. Inside the 24-step loop, it applies this scaling multiplier to the baseline traffic congestion template (`simulated_traffic = base_traffic * (1.0 + adjustment)`).
2.  **Rainfall Simulator**: Takes values from `0` to `10 mm`. It overrides the `rain_1h` input feature, cools temperatures, and raises humidity scales in the feature array.
3.  The recursive forecaster re-runs predictions instantly when sliders change, comparing the adjusted 6-hour average against the baseline forecast to report immediate environmental percentage impacts (e.g., `"-12.5% AQI Reduction"`).
