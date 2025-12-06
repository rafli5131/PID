import asyncio
import aiohttp
import psycopg2
from datetime import datetime
import os

# Database connection parameters
DB_PARAMS = {
    "host": "postgres",
    "database": "air_quality_monitoring",
    "user": "admin",
    "password": "adminpassword",
    "port": "5432"
}

API_KEY = "4c0dbb9c648a4e669a641524251809"
BASE_URL = "http://api.weatherapi.com/v1/current.json"

def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn

async def fetch_weather(session, city_name):
    params = {
        "key": API_KEY,
        "q": f"{city_name},Jawa Tengah, Indonesia",
        "lang": "id",
        "aqi": "yes"
    }
    try:
        async with session.get(BASE_URL, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch data for {city_name}: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching data for {city_name}: {e}")
        return None

async def ingest_data_async():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Starting ingestion at {datetime.now()}")
    
    # Fetch all cities from DB
    cursor.execute("SELECT id, name FROM cities")
    cities = cursor.fetchall()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities:
            city_id, city_name = city
            tasks.append(process_city(session, cursor, city_id, city_name))
        
        await asyncio.gather(*tasks)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Weather ingestion complete.")

async def process_city(session, cursor, city_id, city_name):
    data = await fetch_weather(session, city_name)
    if data:
        try:
            current = data['current']
            location = data['location']
            air_quality = current.get('air_quality', {})
            
            # Extract fields
            temp_c = current['temp_c']
            humidity = current['humidity']
            wind_kph = current['wind_kph']
            wind_degree = current['wind_degree']
            wind_dir = current['wind_dir']
            pressure_mb = current['pressure_mb']
            precip_mm = current['precip_mm']
            cloud = current['cloud']
            feelslike_c = current['feelslike_c']
            vis_km = current['vis_km']
            uv_index = current['uv']
            gust_kph = current['gust_kph']
            condition_text = current['condition']['text']
            
            # Air Quality
            co = air_quality.get('co', 0)
            no2 = air_quality.get('no2', 0)
            o3 = air_quality.get('o3', 0)
            so2 = air_quality.get('so2', 0)
            pm2_5 = air_quality.get('pm2_5', 0)
            pm10 = air_quality.get('pm10', 0)
            us_epa_index = air_quality.get('us-epa-index', 0)
            gb_defra_index = air_quality.get('gb-defra-index', 0)
            
            # Use PM2.5 as the main pollution index for backward compatibility or display
            pollution_index = int(pm2_5)

            sql = """
                INSERT INTO weather_log 
                (city_id, timestamp, temperature_c, humidity_percent, wind_speed_kmh, 
                weather_condition, wind_degree, wind_dir, pressure_mb, precip_mm, 
                cloud, feelslike_c, vis_km, uv_index, gust_kph, 
                co, no2, o3, so2, pm2_5, pm10, us_epa_index, gb_defra_index, pollution_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Timestamp from API is epoch, convert to datetime
            timestamp = datetime.fromtimestamp(current['last_updated_epoch'])

            cursor.execute(sql, (
                city_id, timestamp, temp_c, humidity, wind_kph,
                condition_text, wind_degree, wind_dir, pressure_mb, precip_mm,
                cloud, feelslike_c, vis_km, uv_index, gust_kph,
                co, no2, o3, so2, pm2_5, pm10, us_epa_index, gb_defra_index, pollution_index
            ))
            print(f"Ingested data for {city_name}")
            
        except Exception as e:
            print(f"Error processing data for {city_name}: {e}")

def ingest_data():
    """Synchronous wrapper for the async ingestion function."""
    asyncio.run(ingest_data_async())

if __name__ == "__main__":
    ingest_data()
