# Air Quality & ISPA Monitoring Pipeline (Central Java)

This project monitors air quality and ISPA (Acute Respiratory Infection) cases in Central Java, Indonesia.

## Features
- **Data Ingestion**: Fetches real-time weather data from Open-Meteo and loads ISPA case statistics from CSV.
- **Storage**: PostgreSQL database for structured data storage.
- **Visualization**: Grafana dashboard for monitoring pollution levels and health risks.

## Prerequisites
- Docker & Docker Compose
- Python 3.x
- Virtual Environment (recommended)

## Setup

1.  **Start Services**:
    ```bash
    docker compose up -d
    ```

2.  **Install Dependencies**:
    ```bash
    source /home/rafli/jupyter_env/bin/activate
    pip install requests psycopg2-binary
    ```

3.  **Run Ingestion**:
    ```bash
    python3 scripts/ingest_weather.py
    python3 scripts/ingest_ispa.py
    ```

4.  **View Dashboard**:
    Open [http://localhost:3000](http://localhost:3000) (User: `admin`, Pass: `admin`).
