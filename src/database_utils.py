import sqlite3
from datetime import datetime
import os

DB_PATH = "aqi_history.db"

def init_db():
    """Creates the database and table if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS aqi_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  location TEXT, 
                  aqi REAL, 
                  temp REAL, 
                  humidity REAL,
                  pm25 REAL)''')
    conn.commit()
    conn.close()

def log_aqi_data(location, aqi, temp, humidity, pm25):
    """Saves a new record to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO aqi_logs (timestamp, location, aqi, temp, humidity, pm25) VALUES (?, ?, ?, ?, ?, ?)",
              (now, location, aqi, temp, humidity, pm25))
    conn.commit()
    conn.close()