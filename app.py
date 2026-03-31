import streamlit as st
import os
import numpy as np
import pandas as pd
import datetime
from src.api_utils import LOCATIONS, get_live_data, get_historical_aqi
from src.model_utils import load_all_assets, run_predictions, create_gauge, predict_7_days
from src.database_utils import init_db, log_aqi_data
import requests

# --- 1. INITIALIZE SESSION STATE ---
if 'aqi_data' not in st.session_state:
    st.session_state['aqi_data'] = [100.0, 100.0, 100.0]
if 'live_weather' not in st.session_state:
    st.session_state['live_weather'] = None

# --- 2. ASSET LOADING ---
rf_model, lstm_model, scaler = load_all_assets()

# --- 3. PAGE SETUP ---
st.set_page_config(page_title="Mumbai AQI Predictor", layout="wide")

# --- 4. CSS INJECTION (Atmospheric Background Logic) ---

# Default: Clear Blue Sky (Good AQI)
sky_top = "#4facfe"   # Bright Blue
sky_bottom = "#00f2fe" # Light Cyan
overlay_opacity = "0.1" # Subtle clouds

if st.session_state['live_weather']:
    aqi = st.session_state['live_weather']['aqi']
    
    if 50 < aqi <= 100: # Satisfactory / Moderate (Hazy Yellowish)
        sky_top = "#757F9A"    # Steel Grey
        sky_bottom = "#D7E1EC" # Hazy Blue
        overlay_opacity = "0.3" # Thicker haze
        
    elif aqi > 100: # Poor / Unhealthy (Smoggy Brown/Orange)
        sky_top = "#3e5151"    # Dark Smog
        sky_bottom = "#decba4" # Dust/Sand color
        overlay_opacity = "0.6" # Heavy smog/clouds

st.markdown(f"""
<style>
/* --- HIDE STREAMLIT BRANDING --- */
    .stAppDeployButton {{
        display: none !important;
    }}
    header {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    /* 1. ATMOSPHERIC BACKGROUND */
    .stApp {{
        background: linear-gradient(to bottom, {sky_top}, {sky_bottom});
        background-attachment: fixed;
        color: #1e1e1e; /* Darker text for better contrast on light sky */
    }}

    /* 2. MOVING HAZE/CLOUD EFFECT */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,{overlay_opacity}) 0%, transparent 70%);
        animation: moveClouds 20s linear infinite;
        pointer-events: none;
        z-index: 0;
    }}

    @keyframes moveClouds {{
        from {{ transform: translate(-10%, -10%); }}
        to {{ transform: translate(10%, 10%); }}
    }}

    /* 3. CARD GLASSMORPHISM (Dark mode cards on light sky) */
    .hero-card {{
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    }}
    
    .aqi-value {{ font-size: 85px; font-weight: 800; margin: 0; line-height: 1; }}
    .aqi-label {{ font-size: 24px; font-weight: bold; text-transform: uppercase; }}
    
    .pollutant-box {{
        background: rgba(255, 255, 255, 0.4);
        padding: 15px;
        border-radius: 12px;
        border-bottom: 4px solid #1e1e1e;
        text-align: center;
        font-weight: bold;
    }}
    
    .poll-label {{ color: #444; font-size: 13px; font-weight: 700; }}
    .poll-val {{ font-size: 20px; color: #000; }}

    /* Fix sidebar contrast */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.8);
    }}
</style>
""", unsafe_allow_html=True)

st.title("🌬️ Mumbai Real-Time AQI Predictor")
init_db()

# --- 5. SIDEBAR (LOCKED) ---
st.sidebar.header("📍 Location Settings")
selected_location = st.sidebar.selectbox("Select Station Area", list(LOCATIONS.keys()))
coords = LOCATIONS[selected_location]

if st.sidebar.button("Fetch Last 3 Days History"):
    with st.sidebar:
        with st.spinner(f"Accessing history..."):
            st.session_state['aqi_data'] = get_historical_aqi(coords['lat'], coords['lon'])
            st.success("History Updated!")

st.sidebar.divider()
st.sidebar.subheader("📊 Past AQI Data")

# Fetch the values from session state
d3, d2, d1 = st.session_state['aqi_data']

# Display as clean metrics instead of input boxes
st.sidebar.metric("AQI 3 Days Ago", f"{d3:.0f}")
st.sidebar.metric("AQI 2 Days Ago", f"{d2:.0f}")
st.sidebar.metric("Today's AQI", f"{d1:.0f}")

# --- 6. MAIN DASHBOARD ---
if st.button(f"Refresh Live Data for {selected_location}", type="secondary"):
    with st.spinner(f"Connecting to sensors..."):
        data = get_live_data(coords['lat'], coords['lon'])
        if data:
            data['station'] = selected_location
            st.session_state['live_weather'] = data
            st.session_state['aqi_data'][2] = float(data["aqi"])
            log_aqi_data(selected_location, data['aqi'], data['temp'], data['humidity'], data['pm25'])
            st.rerun()

if st.session_state['live_weather']:
    w = st.session_state['live_weather']
    status_color = "#4CAF50" if w['aqi'] <= 50 else "#FFC107" if w['aqi'] <= 100 else "#FF5722"
    status_text = "GOOD" if w['aqi'] <= 50 else "SATISFACTORY" if w['aqi'] <= 100 else "POOR"
    
    st.markdown(f"""
        <div class="hero-card">
            <p style="color: #8b949e; margin-bottom: 5px;">Mumbai, Maharashtra • <b>{w['station']} Station</b></p>
            <div class="aqi-label" style="color: {status_color};">{status_text}</div>
            <h1 class="aqi-value" style="color: {status_color};">{int(w['aqi'])}</h1>
            <p style="margin-top: 10px; color: #8b949e;">{w['desc'].title()} • {w['temp']}°C • {w['humidity']}% Humidity</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧪 Major Air Pollutants")
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    pollutants = [("PM 2.5", w['pm25']), ("PM 10", w['pm10']), ("NO2", w['no2']),
                  ("SO2", w['so2']), ("CO", w['co']), ("O3", w['o3'])]
    cols = [g1, g2, g3, g4, g5, g6]
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"""<div class="pollutant-box">
                <div class="poll-label">{pollutants[i][0]}</div>
                <div class="poll-val">{pollutants[i][1]}</div>
                <small style="color: #8b949e;">µg/m³</small>
            </div>""", unsafe_allow_html=True)

# --- 7. PREDICTION LOGIC (VERTICAL STACK) ---
st.divider()

# Tomorrow's Prediction Section
st.subheader("🔮 Tomorrow's Prediction")
if st.button("Predict Tomorrow", type="primary"):
    d3, d2, d1 = st.session_state['aqi_data']
    rf_final, lstm_final = run_predictions(d3, d2, d1, rf_model, lstm_model, scaler)
    st.plotly_chart(create_gauge(rf_final), use_container_width=True)
    
    if rf_final < 100:
        st.success(f"Target AQI: {rf_final:.2f} - Satisfactory")
    else:
        st.warning(f"Target AQI: {rf_final:.2f} - High Pollution")

st.markdown("---") # Visual separator

# Weekly Trend Section
st.subheader("📅 7-Day Weekly Trend")
if st.button("Generate Weekly Forecast"):
    with st.spinner("Calculating..."):
        d3, d2, d1 = st.session_state['aqi_data']
        forecast_values = predict_7_days(d3, d2, d1, rf_model, scaler)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        dates = pd.date_range(start=tomorrow, periods=7).strftime('%b %d')
        df_forecast = pd.DataFrame({"Date": dates, "Predicted AQI": forecast_values})
        st.line_chart(df_forecast.set_index("Date"))
        st.table(df_forecast.T) # Table view like the image

# --- 8. AQI SCALE INFORMATION SECTION ---
st.divider()
st.header("📊 Understanding the AQI Scale")
st.write("Know about the category of air quality index (AQI) your ambient air falls in and what it implies.")

# Custom CSS for Information Cards
st.markdown("""
<style>
    .info-card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        background-color: rgba(28, 33, 40, 0.9);
        border-left: 10px solid;
    }
    .info-dot {
        height: 20px;
        width: 20px;
        border-radius: 50%;
        margin-right: 15px;
        display: inline-block;
    }
    .category-title { font-weight: bold; font-size: 18px; min-width: 150px; }
    .category-desc { color: #8b949e; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# Define the categories for the information section
aqi_categories = [
    {"name": "Good", "range": "0 to 50", "color": "#4CAF50", "desc": "The air is fresh and free from toxins. Enjoy outdoor activities without any health concerns."},
    {"name": "Moderate", "range": "51 to 100", "color": "#FFEB3B", "desc": "Air quality is acceptable for most, but sensitive individuals might experience mild discomfort."},
    {"name": "Poor", "range": "101 to 150", "color": "#FF9800", "desc": "Breathing may become slightly uncomfortable, especially for those with respiratory issues."},
    {"name": "Unhealthy", "range": "151 to 200", "color": "#F44336", "desc": "This air quality is particularly risky for children, pregnant women, and the elderly. Limit outdoor activities."},
    {"name": "Severe", "range": "201 to 300", "color": "#9C27B0", "desc": "Prolonged exposure can cause chronic health issues or organ damage. Avoid outdoor activities."},
    {"name": "Hazardous", "range": "301+", "color": "#795548", "desc": "Dangerously high pollution levels. Life-threatening health risks with prolonged exposure. Stay indoors."}
]

# Display cards
for cat in aqi_categories:
    st.markdown(f"""
        <div class="info-card" style="border-left-color: {cat['color']};">
            <div class="info-dot" style="background-color: {cat['color']};"></div>
            <div class="category-title" style="color: {cat['color']};">{cat['name']}<br><small style="color:white">({cat['range']})</small></div>
            <div class="category-desc">{cat['desc']}</div>
        </div>
    """, unsafe_allow_html=True)

# --- 9. FOOTER ---
st.markdown("<br><br><p style='text-align: center; color: #8b949e;'>Real-time data powered by OpenWeather • Mumbai AQI Predictor 2026</p>", unsafe_allow_html=True)