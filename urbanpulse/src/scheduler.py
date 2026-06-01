import os
import sys
import time
import schedule
from datetime import datetime

# Add the directory containing this script to sys.path to ensure clean local imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the pipeline tasks
try:
    from data_download import fetch_cpcb_aqi, fetch_traffic_snapshot, fetch_weather
except ImportError as e:
    print(f"Error importing pipeline tasks from data_download: {e}")
    sys.exit(1)

def log_last_run():
    """Logs the last execution timestamp to data/raw/last_run.txt"""
    project_root = os.path.dirname(script_dir)
    raw_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    last_run_file = os.path.join(raw_dir, "last_run.txt")
    timestamp_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_local = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    log_content = (
        f"Last successful execution:\n"
        f"UTC: {timestamp_utc}\n"
        f"Local (system time): {timestamp_local}\n"
    )
    
    try:
        with open(last_run_file, "w") as f:
            f.write(log_content)
        print(f"[Scheduler] Timestamp logged to: {last_run_file}")
    except Exception as e:
        print(f"[Scheduler] Failed to write run log: {e}")

def run_pipeline():
    """Wrapper function to execute the full data capture sequence"""
    print("\n" + "="*60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Scheduled Data Collection...")
    print("="*60)
    
    try:
        # Run CPCB AQI
        print("[Scheduler] 1/3 Running fetch_cpcb_aqi()...")
        fetch_cpcb_aqi()
        
        # Run TomTom Traffic flow
        print("[Scheduler] 2/3 Running fetch_traffic_snapshot()...")
        fetch_traffic_snapshot()
        
        # Run OpenWeatherMap weather
        print("[Scheduler] 3/3 Running fetch_weather()...")
        fetch_weather()
        
        # Log time
        log_last_run()
        print("\n[Scheduler] Data collection sequence completed successfully.")
        
    except Exception as e:
        print(f"[Scheduler] CRITICAL error in scheduled pipeline execution: {e}")
        
    print("="*60)
    print("Data collection running. Press Ctrl+C to stop.\n")

def main():
    print("="*60)
    print("        UrbanPulse Automated Data Scraper Daemon        ")
    print("="*60)
    
    # Run the pipeline immediately on startup to verify all components work
    print("\nRunning initial pipeline execution on startup to verify setup...")
    run_pipeline()
    
    # Schedule the pipeline tasks to run every 1 hour
    print("[Scheduler] Registering job: Run full pipeline every 1 hour...")
    schedule.every(1).hours.do(run_pipeline)
    
    print("\nData collection running. Press Ctrl+C to stop.")
    print("Monitoring and sleeping...\n")
    
    # Run loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Scheduler] Daemon terminated by user (Ctrl+C). Exiting gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
