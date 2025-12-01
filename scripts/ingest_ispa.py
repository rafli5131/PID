import csv
import psycopg2
import os

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

def parse_number(value_str):
    # Handle "1.955.764" -> 1955764.0
    # Handle "83.865" -> 83865.0 (assuming these are thousands separators based on context of population/cases)
    # However, "4.643" could be 4 thousand or 4 point 6. 
    # Looking at the file: "Pneumonia = 83.865", "ISPA = 1.955.764". These are likely totals.
    # "KEBUMEN;4.643;24.955". 24 thousand ISPA cases makes sense for a regency.
    # So "." is likely a thousands separator.
    if not value_str:
        return 0
    clean_str = value_str.replace('.', '')
    return float(clean_str)

def ingest_csv():
    file_path = '../data/jumlah-kasus-pneumonia-dan-ispa-pada-balita-menurut-kabupaten-kota-tahun-2023.csv'
    if not os.path.exists(file_path):
        print(f"{file_path} not found.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Starting ISPA CSV ingestion...")
    
    with open(file_path, 'r') as csvfile:
        # The file uses semicolon delimiter
        reader = csv.reader(csvfile, delimiter=';')
        
        # Skip header
        next(reader) 
        
        for row in reader:
            if len(row) < 3:
                continue
                
            city_name = row[0].strip()
            pneumonia_str = row[1].strip()
            ispa_str = row[2].strip()
            
            # Skip empty lines or totals if they exist and don't match a city
            if not city_name:
                continue

            # Get city_id
            cursor.execute("SELECT id FROM cities WHERE name = %s", (city_name,))
            res = cursor.fetchone()
            
            if not res:
                print(f"City not found in DB: {city_name}")
                # Optional: Insert if not exists? For now, we rely on init.sql seeding.
                continue
                
            city_id = res[0]
            
            pneumonia_cases = parse_number(pneumonia_str)
            ispa_cases = parse_number(ispa_str)
            
            sql = """
                INSERT INTO ispa_cases (city_id, report_year, pneumonia_cases, ispa_cases)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (city_id, report_year) DO UPDATE 
                SET pneumonia_cases = EXCLUDED.pneumonia_cases, ispa_cases = EXCLUDED.ispa_cases
            """
            cursor.execute(sql, (city_id, 2023, pneumonia_cases, ispa_cases))
            print(f"Ingested ISPA data for {city_name}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("ISPA data ingestion complete.")

if __name__ == "__main__":
    ingest_csv()
