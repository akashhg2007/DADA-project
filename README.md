# 🌆 UrbanPulse: Real-Time Bangalore Traffic & Air Quality Intelligence

[![GitHub License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Flutter](https://img.shields.io/badge/Flutter-%E2%89%A5%203.22-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-Regressor-F57C00?logo=scikit-learn&logoColor=white)](https://xgboost.readthedocs.io)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)

UrbanPulse is a cutting-edge, end-to-end telemetry and predictive analytics suite designed for **Bangalore, India**. It integrates **spatial BBMP ward boundaries**, **TomTom traffic telemetry**, **CPCB air quality indexes (AQI)**, and **OpenWeatherMap logs** into a unified, AI-powered city-vitals monitoring platform.

The system features:
1. A **High-Performance FastAPI Backend** serving real-time telemetry and recursive machine learning predictions.
2. An **Interactive Streamlit Data Science Dashboard** for spatial Voronoi analysis, OLS regression explorer, and EDA data stories.
3. A **Stunning Glassmorphic Flutter Mobile & Web Client** offering real-time ward choropleth maps, animated KPI trackers, pull-to-refresh metrics, and debounced "What-If" environmental policy simulators.

---

## 🗺️ Monorepo Architecture Overview

This repository is structured as a clean, unified workspace containing three major system layers:

```text
dadv-project/ (Root)
├── backend/                   # ⚡ Core FastAPI Prediction & Telemetry Server
│   └── main.py                # Main REST API, XGBoost loader & CORS router
│
├── urbanpulse/                # 📊 Data Science, EDA & Streamlit Analytics
│   ├── src/                   # Streamlit screens (Correlation Explorer, Forecaster, App)
│   ├── notebooks/             # Jupyter notebooks for data cleaning & model training
│   ├── data/                  # Segmented 'raw' and 'processed' historical datasets
│   ├── models/                # Serialized XGBoost model (aqi_forecast_xgb.joblib)
│   └── docs/                  # Project reports and academic Viva Q&A sheets
│
└── urbanpulse_app/            # 📱 Glassmorphic Flutter App (Mobile & Web)
    ├── lib/                   # Feature-first Riverpod controllers, widgets, and themes
    ├── assets/                # Lottie assets & ward GeoJSON geometries
    └── README.md              # Detailed Flutter installation & build guidelines
```

---

## 🚀 Quick Start Guide

Get the entire stack running locally on your machine in three simple steps.

### 📋 Prerequisites
- **Python**: $\ge 3.9$
- **Flutter**: $\ge 3.22$
- **Dart**: $\ge 3.4$
- **Android Studio / Emulator** (for running the mobile app locally)

---

### 1. Start the FastAPI Backend
The backend handles real-time ward telemetry, XGBoost inferences, and debounced recursive forecast loops.

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r ../urbanpulse/requirements.txt uvicorn fastapi

# Run the server on port 8000
python -m uvicorn main:app --reload --port 8000
```
*The API is now active at **`http://localhost:8000`**. Check the interactive documentation at `http://localhost:8000/docs`.*

---

### 2. Start the Streamlit Analytics Dashboard
Run the EDA portal to explore spatial Voronoi calculations and scatter regression trends.

```bash
# Navigate to Streamlit folder
cd urbanpulse

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the Streamlit application
streamlit run src/App.py
```
*The dashboard will automatically launch in your browser at **`http://localhost:8501`**.*

---

### 3. Launch the Flutter Glassmorphic App
Deploy the premium dark-mode interface to the web or an Android device.

```bash
# Navigate to the Flutter project
cd urbanpulse_app

# Fetch packages
flutter pub get

# Generate JSON serialization models
dart run build_runner build --delete-conflicting-outputs

# Run the Flutter App
flutter run -d chrome        # Runs the Web version
flutter run -d emulator-5554 # Runs on your active Android emulator
```

---

## 📡 API Contract (At a Glance)

| Method | Endpoint | Description | Payload / Query |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/api/live/aqi` | Returns real-time CPCB AQI and TomTom congestion metrics per ward | None |
| **`GET`** | `/api/history/aqi` | Fetches historical AQI readings for line chart / correlation matrix | `?ward=All&days=7` |
| **`GET`** | `/api/forecast/aqi` | Generates a 24-hour baseline autoregressive prediction | None |
| **`POST`** | `/api/forecast/whatif` | Simulates traffic and rain adjustments on next-day AQI targets | `{"trafficAdjust": -20.0, "rainMm": 3.5}` |
| **`GET`** | `/api/traffic/junctions` | Returns coordinates & traffic speeds of active intersections | None |

---

## 🎯 System Components & Documentation

Dive deeper into individual project compartments:

*   **📱 [Flutter Mobile & Web Application (urbanpulse_app)](file:///d:/dadv%20project/urbanpulse_app/README.md)**: Explore the glassmorphism layout rules, state management details, Riverpod provider structures, and full cross-platform compile guides.
*   **📊 [Data Science & Analytics Workspace (urbanpulse)](file:///d:/dadv%20project/urbanpulse/README.md)**: Details the scrapers, scheduling daemons, datasets, correlation notebooks, and Streamlit layouts.
*   **📝 [Academic Project Report](file:///d:/dadv%20project/urbanpulse/docs/project_report.md)**: Read the formal submission report outlining the problem statement, data sources, ML methodology, and municipal policy recommendations.
*   **🎓 [Viva Q&A Preparation Guide](file:///d:/dadv%20project/urbanpulse/docs/viva_qna.md)**: A targeted 10-question academic cheat sheet explaining XGBoost, `pd.merge_asof`, Voronoi interpolation, autoregressive loops, and spatial limits.

---

## 🎨 Premium Visual Elements
- **Glassmorphism Theme**: Uses highly responsive backdrop blurs (`BackdropFilter`) configured via standard themes inside `lib/core/theme/`.
- **Lottie Animations**: Provides reactive, micro-animated feedback for loading states and rain simulations (changes dynamically based on weather predictions).
- **Responsive Charts**: Employs `fl_chart` to render dual-line real-time comparisons with custom tooltips.

---

## ⚖️ License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

*Developed for the Final Year Data Analytics & Visualization Project (BIT, 2026 Batch)*
