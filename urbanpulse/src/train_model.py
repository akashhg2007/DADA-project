import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def train_forecasting_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    processed_dir = os.path.join(project_root, "data", "processed")
    models_dir = os.path.join(project_root, "models")
    assets_dir = os.path.join(project_root, "assets")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)
    
    master_path = os.path.join(processed_dir, "master_df.csv")
    model_save_path = os.path.join(models_dir, "aqi_forecast_xgb.joblib")
    plot_save_path = os.path.join(assets_dir, "feature_importance.png")
    
    print("--- [Step 1] Loading Master Dataset ---")
    df = pd.read_csv(master_path)
    print(f"Loaded master dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    
    print("\n--- [Step 2] Processing Lagged and Future Target Features ---")
    # Guarantee chronological order per location before lagging
    df = df.sort_values(by=['location', 'timestamp'])
    
    # Calculate PM2.5 lagged by 1 hour (PM2.5_lag1)
    df['PM2.5_lag1'] = df.groupby('location')['PM2.5'].shift(1)
    
    # Calculate Target: AQI in the next hour (shift -1)
    df['target_aqi_next_hour'] = df.groupby('location')['AQI'].shift(-1)
    
    # Define features and target
    features = [
        'hour', 
        'is_weekend', 
        'temp', 
        'humidity', 
        'wind_speed', 
        'congestion_level', 
        'PM2.5_lag1', 
        'rain_1h'
    ]
    target = 'target_aqi_next_hour'
    
    # Drop rows with NaNs in features or target
    clean_df = df.dropna(subset=features + [target])
    print(f"Cleaned dataset shape after removing lag/lead NaNs: {clean_df.shape[0]} rows")
    
    print("\n--- [Step 3] Performing Temporal Train/Test Split ---")
    # Temporal split: last 20% of unique days/hours for test set
    unique_timestamps = sorted(clean_df['timestamp'].unique())
    split_index = int(len(unique_timestamps) * 0.8)
    split_timestamp = unique_timestamps[split_index]
    
    train_df = clean_df[clean_df['timestamp'] < split_timestamp]
    test_df = clean_df[clean_df['timestamp'] >= split_timestamp]
    
    print(f"Split Timestamp: {split_timestamp}")
    print(f"Train set: {train_df.shape[0]} rows (chronological first 80%)")
    print(f"Test set: {test_df.shape[0]} rows (chronological last 20%)")
    
    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]
    
    print("\n--- [Step 4] Training XGBoost Regressor ---")
    print("Model Parameters: n_estimators=100, max_depth=4")
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=4,
        random_state=42,
        learning_rate=0.1
    )
    model.fit(X_train, y_train)
    print("XGBoost model training completed successfully.")
    
    print("\n--- [Step 5] Evaluating Model on Test Set ---")
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Test Set Evaluation Metrics:")
    print(f"  Mean Absolute Error (MAE)  = {mae:.4f}")
    print(f"  Root Mean Squared Error (RMSE) = {rmse:.4f}")
    print(f"  Coefficient of Determination (R^2) = {r2:.4f}")
    
    print("\n--- [Step 6] Saving Model ---")
    joblib.dump(model, model_save_path)
    print(f"Model successfully saved to: {model_save_path}")
    
    print("\n--- [Step 7] Generating Feature Importances Plot ---")
    importances = model.feature_importances_
    feat_imp = pd.Series(importances, index=features).sort_values(ascending=True)
    
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    # Plot using a cohesive harmonious palette
    colors = sns.color_palette("viridis", len(features))
    feat_imp.plot(kind='barh', color=colors, edgecolor='w')
    
    plt.title("XGBoost AQI Predictor - Feature Importances", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Relative Importance Score", fontsize=12)
    plt.ylabel("Features", fontsize=12)
    plt.tight_layout()
    
    plt.savefig(plot_save_path, dpi=300)
    plt.close()
    print(f"Feature importance bar chart saved to: {plot_save_path}")
    
    print("\n==================================================")
    print("          Model Training Completed!               ")
    print("==================================================")

if __name__ == "__main__":
    train_forecasting_model()
