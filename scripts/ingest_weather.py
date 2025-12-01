import requests
import psycopg2
from datetime import datetime
import time

# Database connection parameters
DB_PARAMS = {
    "host": "postgres",
    "database": "air_quality_monitoring",
    "user": "admin",
    "password": "adminpassword",
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn

def fetch_weather_data(lat, lon):
    api_key = "5cd2d782c008f3b7edd5ceef7d2ed1e9"
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
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
        time.sleep(0.2)
        
        data = fetch_weather_data(lat, lon)
        if data and 'main' in data:
            # Extract data
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed'] * 3.6 # Convert m/s to km/h
            wind_deg = data['wind'].get('deg', 0)
            weather_condition = data['weather'][0]['main'] if data['weather'] else 'Unknown'
            
            # Simulate pollution index (0-300) based on real weather data
            import random
            base_pollution = random.randint(50, 150)
            if wind_speed < 5:
                base_pollution += 50
            if 'Rain' in weather_condition:
                base_pollution -= 30
            
            # UV Index is not available in standard current weather API, simulating for now as requested
            # In a real scenario, we would use the One Call API 3.0
            uv_index = random.uniform(0, 11) 
            if 10 <= datetime.now().hour <= 14:
                 uv_index += 2

            sql = """
                INSERT INTO weather_log 
                (city_id, timestamp, temperature_c, humidity_percent, wind_speed_kmh, weather_condition, wind_direction, uv_index, pollution_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                city_id, 
                datetime.fromtimestamp(data['dt']), 
                temp, 
                humidity,
                wind_speed,
                weather_condition,
                wind_deg,
                uv_index,
                base_pollution
            ))
            conn.commit() # Commit immediately
            print(f"Ingested weather data for {city_name}")
            
    # conn.commit() # Already committed
    cursor.close()
    conn.close()
    print("Weather ingestion complete.")

if __name__ == "__main__":
    ingest_data()
