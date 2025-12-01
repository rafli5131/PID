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
def get_aqi_color(aqi):
    if aqi <= 50: return [0, 128, 0, 160] # Green
    elif aqi <= 100: return [255, 255, 0, 160] # Yellow
    elif aqi <= 150: return [255, 165, 0, 160] # Orange
    else: return [255, 0, 0, 160] # Red

def get_aqi_status(aqi):
    if aqi <= 50: return "Sehat"
    elif aqi <= 100: return "Sedang"
    elif aqi <= 150: return "Tidak Sehat bagi Sensitif"
    else: return "Berbahaya"

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
    query_latest = """
        SELECT DISTINCT ON (c.name) 
            c.name, w.timestamp, w.temperature_c, w.humidity_percent, 
            w.pollution_index, w.weather_condition, w.uv_index
        FROM weather_log w JOIN cities c ON w.city_id = c.id
        ORDER BY c.name, w.timestamp DESC
    """
    df_latest = pd.read_sql(query_latest, conn)

    # 3. Time Series (24h)
    query_history = """
        SELECT c.name, w.timestamp, w.pollution_index
        FROM weather_log w JOIN cities c ON w.city_id = c.id
        WHERE w.timestamp >= NOW() - INTERVAL '24 HOURS'
        ORDER BY w.timestamp ASC
    """
    df_history = pd.read_sql(query_history, conn)
    
    # Merge for Map
    if not df_ispa.empty and not df_latest.empty:
        df_map = pd.merge(df_ispa, df_latest, on='name', how='left')
        df_map['color'] = df_map['pollution_index'].apply(get_aqi_color)
        df_map['aqi_status'] = df_map['pollution_index'].apply(get_aqi_status)
        
        # Risk Status for Tooltip (Simple Logic for now)
        df_map['risk_status'] = df_map.apply(lambda x: "High Risk Area" if x['pollution_index'] > 100 and x['ispa_cases'] > df_map['ispa_cases'].median() else "Low/Medium Risk", axis=1)
        
        return df_map, df_history, df_latest
    
    return None, None, None

df_map, df_history, df_latest = load_data()

# --- SIDEBAR ---
st.sidebar.title("Configuration")
st.sidebar.info("Dashboard updated with specific visual requirements.")

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
    
    avg_aqi = df_latest['pollution_index'].mean()
    avg_temp = df_latest['temperature_c'].mean()
    avg_hum = df_latest['humidity_percent'].mean()
    max_poll_city = df_latest.loc[df_latest['pollution_index'].idxmax()]
    danger_count = df_latest[df_latest['pollution_index'] > 150].shape[0]
    
    col1.metric("Rata-rata AQI", f"{avg_aqi:.0f}", delta="Unhealthy" if avg_aqi > 100 else "Healthy", delta_color="inverse")
    col2.metric("Suhu | Kelembaban", f"{avg_temp:.1f}°C | {avg_hum:.0f}%")
    col3.metric("Polusi Tertinggi", f"{max_poll_city['name']}", f"{max_poll_city['pollution_index']:.0f}")
    col4.metric("Peringatan Dini (Bahaya)", f"{danger_count} Kota", delta_color="inverse")
    
    # Charts: Time Series & Weather Dist
    col_ts, col_gauge = st.columns([2, 1])
    
    with col_ts:
        st.subheader("Tren Kualitas Udara 24 Jam Terakhir")
        # Filter for major cities or top 5 most polluted to avoid clutter
        top_cities = df_latest.sort_values('pollution_index', ascending=False).head(5)['name'].tolist()
        df_history_filtered = df_history[df_history['name'].isin(top_cities)]
        
        fig_ts = px.line(df_history_filtered, x='timestamp', y='pollution_index', color='name', 
                         title="Tren Polusi (Top 5 Kota Tertinggi)", markers=True)
        st.plotly_chart(fig_ts, use_container_width=True)
        
    with col_gauge:
        st.subheader("Distribusi Cuaca Saat Ini")
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
        radius_scale=100, # Adjust scale for visibility
        radius_min_pixels=5,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_position=["longitude", "latitude"],
        get_radius="ispa_cases", # Size based on ISPA
        get_fill_color="color",  # Color based on AQI
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
                    "😷 AQI Saat Ini: {pollution_index} ({aqi_status})<br/>"
                    "🏥 Total Kasus ISPA (2023): {ispa_cases}<br/>"
                    "⚠️ Status: {risk_status}",
            "style": {"backgroundColor": "white", "color": "black"}
        }
    ))
    st.caption("Lingkaran Besar = ISPA Tinggi | Warna Merah = Polusi Tinggi")

    # --- PART 3: HEALTH RISK CORRELATION ---
    st.header("3. Health Risk Correlation (Strategis/Analisis)")
    
    col_bar, col_scatter = st.columns(2)
    
    with col_bar:
        st.subheader("Top 10 Kota Kasus ISPA Tertinggi")
        top_ispa = df_map.sort_values('ispa_cases', ascending=False).head(10)
        fig_bar = px.bar(top_ispa, x='ispa_cases', y='name', orientation='h', color='ispa_cases', 
                         color_continuous_scale='Reds', title="ISPA Cases by City")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_scatter:
        st.subheader("Korelasi Polusi vs Kesehatan")
        fig_scatter = px.scatter(
            df_map, 
            x="pollution_index", 
            y="ispa_cases", 
            size="ispa_cases", 
            color="aqi_status",
            hover_name="name",
            title="Pollution Index vs ISPA Cases",
            labels={"pollution_index": "Rata-rata Pollution Index", "ispa_cases": "Total ISPA Cases"}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.error("Data could not be loaded. Please ensure the database is running.")
