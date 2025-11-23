import psycopg2

DB_PARAMS = {
    "host": "localhost",
    "database": "air_quality_monitoring",
    "user": "admin",
    "password": "adminpassword",
    "port": "5432"
}

def verify():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cities")
        cities_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weather_log")
        weather_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ispa_cases")
        ispa_count = cursor.fetchone()[0]
        
        print(f"Cities: {cities_count}")
        print(f"Weather Logs: {weather_count}")
        print(f"ISPA Cases: {ispa_count}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
