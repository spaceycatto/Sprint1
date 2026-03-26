import joblib
import tensorflow as tf
import numpy as np
import plotly.graph_objects as go
import datetime

def load_all_assets():
    """Loads RF, LSTM, and Scaler from the models folder"""
    rf_model = joblib.load('models/mumbai_aqi_rf.pkl')
    lstm_model = tf.keras.models.load_model('models/mumbai_aqi_lstm.h5', compile=False)
    scaler = joblib.load('models/scaler.pkl')
    return rf_model, lstm_model, scaler

def run_predictions(day_3, day_2, day_1, rf_model, lstm_model, scaler):
    """Processes inputs and returns real AQI predictions"""
    # 1. Scaling
    input_raw = np.array([[day_3], [day_2], [day_1]])
    input_scaled = scaler.transform(input_raw)
    
    # 2. Reshaping
    rf_in = input_scaled.reshape(1, 3)
    lstm_in = input_scaled.reshape(1, 3, 1)
    
    # 3. Predicting
    rf_p = rf_model.predict(rf_in)
    lstm_p = lstm_model.predict(lstm_in)
    
    # 4. Inverse Scaling
    rf_final = scaler.inverse_transform(rf_p.reshape(-1, 1))[0][0]
    lstm_final = scaler.inverse_transform(lstm_p.reshape(-1, 1))[0][0]
    
    return rf_final, lstm_final

def predict_7_days(day_3, day_2, day_1, rf_model, scaler):
    """
    Generates a 7-day forecast by feeding predictions back into the model.
    """
    # 1. Start with the current 3-day window
    current_window = np.array([day_3, day_2, day_1]).reshape(-1, 1)
    # 2. Scale it (the model expects scaled inputs)
    current_window_scaled = scaler.transform(current_window).flatten()
    
    forecast_results = []
    
    for _ in range(7):
        # Reshape for RF: [1, 3]
        inp = current_window_scaled.reshape(1, 3)
        
        # Predict next step (scaled)
        pred_scaled = rf_model.predict(inp)[0]
        
        # Inverse scale to get actual AQI value for display
        actual_val = scaler.inverse_transform([[pred_scaled]])[0][0]
        forecast_results.append(round(actual_val, 2))
        
        # Update the window: [Day2, Day1, NewPrediction]
        current_window_scaled = np.roll(current_window_scaled, -1)
        current_window_scaled[-1] = pred_scaled
        
    return forecast_results

def create_gauge(aqi_value):
    """Generates the Plotly Gauge Chart"""
    # Determine color based on AQI standards
    if aqi_value <= 50: color = "green"
    elif aqi_value <= 100: color = "yellow"
    elif aqi_value <= 150: color = "orange"
    else: color = "red"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = aqi_value,
        title = {'text': "Predicted AQI Tomorrow", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [0, 500]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "rgba(0,255,0,0.2)"},
                {'range': [51, 100], 'color': "rgba(255,255,0,0.2)"},
                {'range': [101, 150], 'color': "rgba(255,165,0,0.2)"},
                {'range': [151, 500], 'color': "rgba(255,0,0,0.2)"}
            ]
        }
    ))
    fig.update_layout(height=350)
    return fig