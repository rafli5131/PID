import streamlit as st
import pandas as pd
import psycopg2
import pydeck as pdk
import plotly.express as px
import os

# Page Config
st.set_page_config(
    page_title="Central Java Air Quality & ISPA Monitor",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database Connection
@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "air_quality_monitoring"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "adminpassword"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Data Fetching
def load_data():
    conn = get_db_connection()
    if not conn:
        return None, None

    # Fetch Cities & ISPA Data
    query_ispa = """
        SELECT 
            c.name, c.latitude, c.longitude, 
            i.report_year, i.pneumonia_cases, i.ispa_cases
        FROM cities c
        JOIN ispa_cases i ON c.id = i.city_id
    """
    df_ispa = pd.read_sql(query_ispa, conn)

    # Fetch Recent Weather Data (Last 24 hours for all cities)
    query_weather = """
        SELECT 
            c.name, w.timestamp, w.temperature_c, w.humidity_percent, 
            w.wind_speed_kmh, w.pollution_index
        FROM weather_log w
        JOIN cities c ON w.city_id = c.id
        ORDER BY w.timestamp ASC
    """
    df_weather = pd.read_sql(query_weather, conn)
    
    return df_ispa, df_weather

# Load Data
df_ispa, df_weather = load_data()

# Sidebar
st.sidebar.title("Filters")
if df_ispa is not None:
    selected_cities = st.sidebar.multiselect(
        "Select Cities", 
        options=sorted(df_ispa['name'].unique()),
        default=sorted(df_ispa['name'].unique())
    )
else:
    selected_cities = []

# Main Content
st.title("🌬️ Central Java Air Quality & ISPA Monitoring Dashboard")

if df_ispa is not None and df_weather is not None:
    
    # Filter Data
    filtered_ispa = df_ispa[df_ispa['name'].isin(selected_cities)]
    filtered_weather = df_weather[df_weather['name'].isin(selected_cities)]

    # --- ROW 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_ispa = filtered_ispa['ispa_cases'].sum()
    avg_pollution = filtered_weather['pollution_index'].mean() if not filtered_weather.empty else 0
    avg_temp = filtered_weather['temperature_c'].mean() if not filtered_weather.empty else 0
    
    col1.metric("Total ISPA Cases (2023)", f"{total_ispa:,.0f}")
    col2.metric("Avg Pollution Index (24h)", f"{avg_pollution:.1f}")
    col3.metric("Avg Temperature (24h)", f"{avg_temp:.1f} °C")
    col4.metric("Monitored Cities", len(selected_cities))

    # --- ROW 2: MAP ---
    st.subheader("📍 Geographic Distribution")
    
    # PyDeck Layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        filtered_ispa,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=100,
        radius_min_pixels=5,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_position=["longitude", "latitude"],
        get_radius="ispa_cases",
        get_fill_color=[255, 140, 0],
        get_line_color=[0, 0, 0],
    )
    
    # Heatmap Layer
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        filtered_ispa,
        get_position=["longitude", "latitude"],
        get_weight="ispa_cases",
        radius_pixels=50,
    )

    view_state = pdk.ViewState(
        latitude=-7.150975,
        longitude=110.1402594, # Center of Central Java roughly
        zoom=7,
        pitch=0,
    )

    st.pydeck_chart(pdk.Deck(
        layers=[heatmap_layer, layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\nISPA Cases: {ispa_cases}\nPneumonia Cases: {pneumonia_cases}"}
    ))

    # --- ROW 3: CHARTS ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 ISPA Cases by City")
        fig_bar = px.bar(
            filtered_ispa.sort_values('ispa_cases', ascending=False).head(10), 
            x='ispa_cases', 
            y='name', 
            orientation='h',
            color='ispa_cases',
            title="Top 10 Cities with Highest ISPA Cases"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("📈 Pollution Trend (Last 24h)")
        if not filtered_weather.empty:
            # Aggregate by time to avoid too many lines if all cities selected
            weather_agg = filtered_weather.groupby('timestamp')['pollution_index'].mean().reset_index()
            fig_line = px.line(
                weather_agg, 
                x='timestamp', 
                y='pollution_index', 
                title="Average Pollution Index Over Time"
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No weather data available for the selected period.")

    # --- ROW 4: DATA TABLE ---
    st.subheader("📋 Detailed Data")
    tab1, tab2 = st.tabs(["ISPA Data", "Weather Logs"])
    
    with tab1:
        st.dataframe(filtered_ispa)
        
    with tab2:
        st.dataframe(filtered_weather.sort_values('timestamp', ascending=False).head(1000))

else:
    st.warning("Data could not be loaded. Please check the database connection.")
