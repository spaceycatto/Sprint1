''' import requests
import numpy as np

def get_waqi_pollution():
    """Fetches PM2.5 and AQI from WAQI API"""
    token = "046e8814cc209bffac1454aa547b512e4e0310ba"
    url = f"https://api.waqi.info/feed/mumbai/?token={token}"
    try:
        res = requests.get(url).json()
        if res['status'] == 'ok':
            return {
                "aqi": res['data'].get('aqi', 0),
                "pm25": res['data'].get('iaqi', {}).get('pm25', {}).get('v', "N/A"),
                "station": res['data'].get('city', {}).get('name', 'Mumbai')
            }
    except Exception as e:
        print(f"WAQI API Error: {e}")
        return None

def get_openweathermap_weather():
    """Fetches accurate Temp/Humidity from OpenWeatherMap"""
    api_key = "037300ab2402f0676a39e3f06a61c10a"
    lat, lon = 19.0760, 72.8777
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        res = requests.get(url).json()
        return {
            "temp": res['main']['temp'],
            "humidity": res['main']['humidity'],
            "desc": res['weather'][0]['description'].title()
        }
    except Exception as e:
        print(f"OpenWeather API Error: {e}")
        return None

def get_historical_aqi():
    """Fetches past 3 days of AQI from Open-Meteo"""
    lat, lon = 19.0760, 72.8777
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=pm2_5&past_days=3"
    try:
        res = requests.get(url).json()
        pm25 = res['hourly']['pm2_5']
        
        # Internal math to convert PM2.5 to AQI
        def to_aqi(pm):
            if pm <= 12: return pm * 4.16
            if pm <= 35: return (pm - 12) * 2.17 + 50
            return (pm - 35) * 0.66 + 100
            
        return [
            round(to_aqi(np.mean(pm25[0:24]))), 
            round(to_aqi(np.mean(pm25[24:48]))), 
            round(to_aqi(np.mean(pm25[48:72])))
        ]
    except:
        return [105, 112, 118] # Fallback values '''

''' import requests
import numpy as np

# --- 1. CONFIGURATION ---
API_KEY = "037300ab2402f0676a39e3f06a61c10a"

# Mapping of locations to their coordinates
LOCATIONS = {
    "Mumbai Central": {"lat": 19.0760, "lon": 72.8777},
    "Bandra": {"lat": 19.0596, "lon": 72.8295},
    "Colaba": {"lat": 18.9067, "lon": 72.8147},
    "Andheri": {"lat": 19.1136, "lon": 72.8697},
    "Chembur": {"lat": 19.0510, "lon": 72.8940},
    "Borivali": {"lat": 19.2307, "lon": 72.8567}
}

# --- 2. MATH UTILITIES ---
def calculate_aqi_us(pm25):
    """
    Standard US-EPA formula to convert PM2.5 to AQI (0-500).
    OpenWeather provides raw PM2.5; our model expects the AQI scale.
    """
    if pm25 <= 12.0: return (50/12.0) * pm25
    elif pm25 <= 35.4: return ((100-51)/(35.4-12.1)) * (pm25-12.1) + 51
    elif pm25 <= 55.4: return ((150-101)/(55.4-35.5)) * (pm25-35.5) + 101
    elif pm25 <= 150.4: return ((200-151)/(150.4-55.5)) * (pm25-55.5) + 151
    else: return pm25 * 1.5 # Simple linear approximation for very high values

# --- 3. DYNAMIC FETCH FUNCTIONS ---

 def get_live_data(lat, lon):
    """Fetches real-time Pollution and Weather from OpenWeather"""
    pol_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    wea_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    try:
        p_res = requests.get(pol_url).json()
        w_res = requests.get(wea_url).json()
        
        pm25 = p_res['list'][0]['components']['pm2_5']
        
        return {
            "aqi": round(calculate_aqi_us(pm25)),
            "pm25": pm25,
            "temp": w_res['main']['temp'],
            "humidity": w_res['main']['humidity'],
            "desc": w_res['weather'][0]['description'].title(),
            "station": w_res.get('name', 'Local Area')
        }
    except Exception as e:
        print(f"OpenWeather Real-time Error: {e}")
        return None

def get_historical_aqi(lat, lon):
    """
    Fetches past 3 days of AQI. 
    Uses OpenWeather Air Pollution History endpoint.
    """
    import time
    end = int(time.time())
    start = end - (3 * 24 * 60 * 60) # 3 days ago
    
    url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={end}&appid={API_KEY}"
    
    try:
        res = requests.get(url).json()
        history = res['list']
        
        # Group data into 24-hour chunks and calculate average AQI
        # (Assuming the API returns hourly data)
        chunk = len(history) // 3
        day3_pm = np.mean([x['components']['pm2_5'] for x in history[0:chunk]])
        day2_pm = np.mean([x['components']['pm2_5'] for x in history[chunk:chunk*2]])
        day1_pm = np.mean([x['components']['pm2_5'] for x in history[chunk*2:]])
        
        return [
            round(calculate_aqi_us(day3_pm)),
            round(calculate_aqi_us(day2_pm)),
            round(calculate_aqi_us(day1_pm))
        ]
    except Exception as e:
        print(f"OpenWeather History Error: {e}")
        return [105, 112, 118] # Fallback values '''

import requests
import numpy as np
import time

# --- 1. CONFIGURATION ---
API_KEY = "037300ab2402f0676a39e3f06a61c10a"

LOCATIONS = {
    "Mumbai Central": {"lat": 19.0760, "lon": 72.8777},
    "Bandra": {"lat": 19.0596, "lon": 72.8295},
    "Colaba": {"lat": 18.9067, "lon": 72.8147},
    "Andheri": {"lat": 19.1136, "lon": 72.8697},
    "Chembur": {"lat": 19.0510, "lon": 72.8940},
    "Borivali": {"lat": 19.2307, "lon": 72.8567}
}

# --- 2. MATH UTILITIES ---
def calculate_aqi_us(pm25):
    """Standard US-EPA formula to convert PM2.5 to AQI (0-500)"""
    if pm25 <= 12.0: return (50/12.0) * pm25
    elif pm25 <= 35.4: return ((100-51)/(35.4-12.1)) * (pm25-12.1) + 51
    elif pm25 <= 55.4: return ((150-101)/(55.4-35.5)) * (pm25-35.5) + 101
    elif pm25 <= 150.4: return ((200-151)/(150.4-55.5)) * (pm25-55.5) + 151
    else: return pm25 * 1.5 

# --- 3. DYNAMIC FETCH FUNCTIONS ---

def get_live_data(lat, lon):
    """Fetches full pollutant suite and Weather from OpenWeather"""
    pol_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    wea_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    try:
        p_res = requests.get(pol_url).json()
        w_res = requests.get(wea_url).json()
        
        # OpenWeather returns all chemicals in the 'components' dictionary
        comp = p_res['list'][0]['components']
        
        return {
            "aqi": round(calculate_aqi_us(comp.get('pm2_5', 0))),
            "pm25": comp.get('pm2_5'),
            "pm10": comp.get('pm10'),
            "no2": comp.get('no2'),
            "so2": comp.get('so2'),
            "co": comp.get('co'),
            "o3": comp.get('o3'),
            "temp": w_res['main']['temp'],
            "humidity": w_res['main']['humidity'],
            "desc": w_res['weather'][0]['description'].title(),
            "station": w_res.get('name', 'Local Area')
        }
    except Exception as e:
        print(f"OpenWeather Real-time Error: {e}")
        return None

def get_historical_aqi(lat, lon):
    """Fetches past 3 days of AQI using historical PM2.5 averages"""
    end = int(time.time())
    start = end - (3 * 24 * 60 * 60) 
    
    url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={end}&appid={API_KEY}"
    
    try:
        res = requests.get(url).json()
        history = res.get('list', [])
        
        if not history: return [105, 112, 118]

        # Splitting the history list into 3 days (approx 24 data points per day)
        chunk = len(history) // 3
        day3_pm = np.mean([x['components']['pm2_5'] for x in history[0:chunk]])
        day2_pm = np.mean([x['components']['pm2_5'] for x in history[chunk:chunk*2]])
        day1_pm = np.mean([x['components']['pm2_5'] for x in history[chunk*2:]])
        
        return [
            round(calculate_aqi_us(day3_pm)),
            round(calculate_aqi_us(day2_pm)),
            round(calculate_aqi_us(day1_pm))
        ]
    except Exception as e:
        print(f"OpenWeather History Error: {e}")
        return [105, 112, 118]