import streamlit as st
import pandas as pd
import psycopg2
import pydeck as pdk
import plotly.express as px
import os
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Central Java Air Quality & Health Risk Monitor",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    h1 { color: #0e76a8; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    h2, h3 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #0e76a8; }
    .css-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            database=os.getenv("DB_NAME", "air_quality_monitoring"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "adminpassword"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# --- DATA PROCESSING ---
def get_epa_color(index):
    # US EPA Index: 1-6
    colors = {
        1: [0, 228, 0, 160],   # Green (Good)
        2: [255, 255, 0, 160], # Yellow (Moderate)
        3: [255, 126, 0, 160], # Orange (Unhealthy for Sensitive)
        4: [255, 0, 0, 160],   # Red (Unhealthy)
        5: [143, 63, 151, 160],# Purple (Very Unhealthy)
        6: [126, 0, 35, 160]   # Maroon (Hazardous)
    }
    return colors.get(index, [128, 128, 128, 160]) # Default Grey

def get_epa_status(index):
    status = {
        1: "Good",
        2: "Moderate",
        3: "Unhealthy for Sensitive Groups",
        4: "Unhealthy",
        5: "Very Unhealthy",
        6: "Hazardous"
    }
    return status.get(index, "Unknown")

def load_data():
    conn = get_db_connection()
    if not conn: return None, None, None

    # 1. Cities & ISPA (Yearly)
    query_ispa = """
        SELECT c.name, c.latitude, c.longitude, i.report_year, i.pneumonia_cases, i.ispa_cases
        FROM cities c JOIN ispa_cases i ON c.id = i.city_id WHERE i.report_year = 2023
    """
    df_ispa = pd.read_sql(query_ispa, conn)

    # 2. Latest Weather (Snapshot)
    # Fetching new columns
    query_latest = """
        SELECT DISTINCT ON (c.name) 
            c.name, w.timestamp, w.temperature_c, w.humidity_percent, 
            w.pm2_5, w.pm10, w.us_epa_index, w.co, w.no2, w.o3,
            w.weather_condition, w.uv_index, w.wind_speed_kmh, w.wind_dir, w.pressure_mb
        FROM weather_log w JOIN cities c ON w.city_id = c.id
        ORDER BY c.name, w.timestamp DESC
    """
    df_latest = pd.read_sql(query_latest, conn)

    # 3. Time Series (24h)
    query_history = """
        SELECT c.name, w.timestamp, w.pm2_5, w.us_epa_index
        FROM weather_log w JOIN cities c ON w.city_id = c.id
        WHERE w.timestamp >= NOW() - INTERVAL '24 HOURS'
        ORDER BY w.timestamp ASC
    """
    df_history = pd.read_sql(query_history, conn)
    
    # Merge for Map
    if not df_ispa.empty and not df_latest.empty:
        df_map = pd.merge(df_ispa, df_latest, on='name', how='left')
        
        # Use US EPA Index for coloring if available, else fallback
        df_map['us_epa_index'] = df_map['us_epa_index'].fillna(0).astype(int)
        df_map['color'] = df_map['us_epa_index'].apply(get_epa_color)
        df_map['aqi_status'] = df_map['us_epa_index'].apply(get_epa_status)
        
        # Risk Status Logic (Updated)
        # High Risk if EPA Index > 2 (Unhealthy+) AND ISPA cases > median
        median_ispa = df_map['ispa_cases'].median()
        df_map['risk_status'] = df_map.apply(
            lambda x: "High Risk Area" if x['us_epa_index'] > 2 and x['ispa_cases'] > median_ispa else "Low/Medium Risk", 
            axis=1
        )
        
        return df_map, df_history, df_latest
    
    return None, None, None

df_map, df_history, df_latest = load_data()

# --- SIDEBAR ---
st.sidebar.title("Configuration")
st.sidebar.info("Dashboard updated with WeatherAPI data.")

# City Filter
if df_map is not None:
    all_cities = sorted(df_map['name'].unique())
    selected_cities = st.sidebar.multiselect("Filter City", all_cities, default=all_cities)
    
    if selected_cities:
        df_map = df_map[df_map['name'].isin(selected_cities)]
        df_latest = df_latest[df_latest['name'].isin(selected_cities)]
        df_history = df_history[df_history['name'].isin(selected_cities)]
    else:
        st.warning("Please select at least one city.")
        st.stop()

# --- MAIN LAYOUT ---
st.title("Central Java Air Quality & Health Risk Monitor")

if df_map is not None:
    
    # --- PART 1: REAL-TIME ENVIRONMENT MONITOR ---
    st.header("1. Real-Time Environment Monitor (Operasional)")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    avg_pm25 = df_latest['pm2_5'].mean()
    avg_temp = df_latest['temperature_c'].mean()
    avg_hum = df_latest['humidity_percent'].mean()
    
    # Find max pollution city based on PM2.5
    max_poll_city = df_latest.loc[df_latest['pm2_5'].idxmax()]
    
    # Count cities with EPA Index > 2 (Unhealthy for sensitive groups or worse)
    danger_count = df_latest[df_latest['us_epa_index'] > 2].shape[0]
    
    col1.metric("Rata-rata PM2.5", f"{avg_pm25:.1f} µg/m³", delta="High" if avg_pm25 > 15 else "Normal", delta_color="inverse")
    col2.metric("Suhu | Kelembaban", f"{avg_temp:.1f}°C | {avg_hum:.0f}%")
    col3.metric("Polusi Tertinggi (PM2.5)", f"{max_poll_city['name']}", f"{max_poll_city['pm2_5']:.1f}")
    col4.metric("Peringatan Dini (>Moderate)", f"{danger_count} Kota", delta_color="inverse")
    
    # Charts: Time Series & Weather Dist
    col_ts, col_gauge = st.columns([2, 1])
    
    with col_ts:
        st.subheader("Tren PM2.5 (24 Jam Terakhir)")
        # Filter for top 5 most polluted
        top_cities = df_latest.sort_values('pm2_5', ascending=False).head(5)['name'].tolist()
        df_history_filtered = df_history[df_history['name'].isin(top_cities)]
        
        fig_ts = px.line(df_history_filtered, x='timestamp', y='pm2_5', color='name', 
                         title="Tren PM2.5 (Top 5 Kota Tertinggi)", markers=True)
        st.plotly_chart(fig_ts, use_container_width=True)
        
    with col_gauge:
        st.subheader("Distribusi Kondisi Cuaca")
        weather_counts = df_latest['weather_condition'].value_counts().reset_index()
        weather_counts.columns = ['Condition', 'Count']
        fig_pie = px.pie(weather_counts, values='Count', names='Condition', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- PART 2: GEOSPATIAL ANALYSIS ---
    st.header("2. Geospatial Analysis (Peta Sebaran)")
    
    # PyDeck Map
    layer = pdk.Layer(
        "ScatterplotLayer",
        df_map,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=100,
        radius_min_pixels=5,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_position=["longitude", "latitude"],
        get_radius="ispa_cases", # Size based on ISPA
        get_fill_color="color",  # Color based on EPA Index
        get_line_color=[0, 0, 0],
    )

    view_state = pdk.ViewState(
        latitude=-7.150975,
        longitude=110.1402594,
        zoom=7.5,
        pitch=0,
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{name}</b><br/>"
                    "🌡️ Suhu: {temperature_c}°C<br/>"
                    "💨 Angin: {wind_speed_kmh} km/h ({wind_dir})<br/>"
                    "🌫️ PM2.5: {pm2_5} µg/m³<br/>"
                    "📊 EPA Index: {us_epa_index} ({aqi_status})<br/>"
                    "🏥 ISPA (2023): {ispa_cases}<br/>"
                    "⚠️ Status: {risk_status}",
            "style": {"backgroundColor": "white", "color": "black"}
        }
    ))
    st.caption("Lingkaran Besar = ISPA Tinggi | Warna = Indeks Kualitas Udara (EPA)")

    # --- PART 3: HEALTH RISK CORRELATION ---
    st.header("3. Health Risk Correlation (Analisis ISPA vs Kualitas Udara)")
    
    col_bar, col_scatter = st.columns(2)
    
    with col_bar:
        st.subheader("Top 10 Kota Kasus ISPA Tertinggi")
        top_ispa = df_map.sort_values('ispa_cases', ascending=False).head(10)
        fig_bar = px.bar(top_ispa, x='ispa_cases', y='name', orientation='h', color='ispa_cases', 
                         color_continuous_scale='Reds', title="ISPA Cases by City")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_scatter:
        st.subheader("Korelasi PM2.5 vs Kasus ISPA")
        fig_scatter = px.scatter(
            df_map, 
            x="pm2_5", 
            y="ispa_cases", 
            size="ispa_cases", 
            color="aqi_status",
            hover_name="name",
            title="PM2.5 Levels vs ISPA Cases",
            labels={"pm2_5": "PM2.5 (µg/m³)", "ispa_cases": "Total ISPA Cases"}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    # Additional Air Quality Details Table
    st.subheader("Detail Kualitas Udara Terkini")
    st.dataframe(df_latest[['name', 'timestamp', 'pm2_5', 'pm10', 'co', 'no2', 'o3', 'us_epa_index', 'weather_condition']].sort_values('pm2_5', ascending=False))

else:
    st.error("Data could not be loaded. Please ensure the database is running.")
