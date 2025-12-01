import time
import schedule
from ingest_weather import ingest_data
from datetime import datetime

def job():
    print(f"Starting scheduled job at {datetime.now()}")
    try:
        ingest_data()
    except Exception as e:
        print(f"Job failed: {e}")

def main():
    print("Weather scraper service started.")
    # Run immediately on startup
    job()
    
    # Schedule every 5 minutes
    schedule.every(5).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
