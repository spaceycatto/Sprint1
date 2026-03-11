# Sprint1
Mumbai AQI Predictor Project Overview -
This project provides a data-driven approach to monitoring and predicting Air Quality Index (AQI) across various micro-climates in Mumbai (Bandra, Colaba, Chembur, etc.). By integrating real-time telemetry with machine learning, the system offers actionable insights into urban air pollution.

Key Features
1. Unified Telemetry: Real-time extraction of PM 2.5, PM 10, NO 2, SO 2, CO, and O3 using the OpenWeather Air Pollution API.
2. Hybrid Modeling: Comparison between Random Forest (Ensemble Learning) and LSTM (Long Short-Term Memory) networks for time-series forecasting.
3. 7-Day Recursive Forecast: Implements a sliding-window inference loop to project pollution trends for the upcoming week.
4. Dynamic Dashboard: Built with Streamlit, featuring interactive gauges, chemical breakdowns, and health advisory logic based on US-EPA standards.

Tech Stack
- Language: Python 3.9+
- ML Libraries: Scikit-Learn, TensorFlow/Keras
- Data Handling: Pandas, NumPy
- API Integration: Requests (OpenWeatherMap API)
- Frontend: Streamlit, Plotly
