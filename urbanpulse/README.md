# UrbanPulse - Bangalore Traffic & AQI Dashboard

UrbanPulse is a real-time and historical analytics dashboard designed to monitor, visualize, and predict traffic patterns and Air Quality Index (AQI) in Bangalore. By integrating spatial data, weather info, and CPCB AQI records, it provides actionable insights into the city's environmental and mobility landscape.

## Project Structure

```text
urbanpulse/
├── .env                  # Environment configurations and API keys
├── README.md             # Project documentation (this file)
├── requirements.txt      # Python dependencies list
├── assets/               # Branding assets, images, and static graphics
├── data/
│   ├── raw/              # Original, unmodified data dumps
│   └── processed/        # Cleaned and processed data ready for modeling/viz
├── models/               # Saved machine learning models (e.g. xgboost, joblib files)
├── notebooks/            # Jupyter notebooks for exploratory data analysis (EDA)
└── src/                  # Core application source code
    └── pages/            # Multi-page Streamlit views/dashboards
```

## Getting Started

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Setup Environment
1. Clone this repository or open the folder.
2. Duplicate the `.env` template and fill in your API keys:
   - `OPENWEATHER_API_KEY`: API key for weather data from OpenWeatherMap.
   - `CPCB_API_KEY`: API key for Central Pollution Control Board (CPCB) data.

### 3. Installation
Install all dependencies using pip:
```bash
pip install -r requirements.txt
```

### 4. Running the Dashboard
Run the Streamlit application:
```bash
streamlit run src/App.py
```
*(Create `App.py` inside `/src` to begin building your main application entrypoint)*
