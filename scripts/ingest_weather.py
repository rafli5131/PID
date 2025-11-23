import requests
import psycopg2
from datetime import datetime
import time

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "air_quality_monitoring",
    "user": "admin",
    "password": "adminpassword",
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn

def fetch_weather_data(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def ingest_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Starting ingestion at {datetime.now()}")
    
    # Fetch all cities from DB
    cursor.execute("SELECT id, name, latitude, longitude FROM cities WHERE latitude IS NOT NULL")
    cities = cursor.fetchall()

    for city in cities:
        city_id, city_name, lat, lon = city
        
        # Add delay to be nice to the API
        time.sleep(0.5)
        
        data = fetch_weather_data(lat, lon)
        if data and 'current_weather' in data:
            cw = data['current_weather']
            
            # Simulate pollution index (0-300)
            import random
            base_pollution = random.randint(50, 150)
            if cw['windspeed'] < 5:
                base_pollution += 50
            
            sql = """
                INSERT INTO weather_log 
                (city_id, timestamp, temperature_c, humidity_percent, wind_speed_kmh, pollution_index)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                city_id, 
                cw['time'], 
                cw['temperature'], 
                random.randint(40, 90), # Humidity placeholder
                cw['windspeed'],
                base_pollution
            ))
            print(f"Ingested weather data for {city_name}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Weather ingestion complete.")

if __name__ == "__main__":
    ingest_data()
