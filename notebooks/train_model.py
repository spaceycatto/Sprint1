import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

# Load data
df = pd.read_csv(r"C:\Users\Sneha Malale\OneDrive\Desktop\AQIProject\data\air_quality_historical.csv")
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Fill missing values using forward fill (common for time series)
df = df.ffill()
# Drop any remaining NaNs at the beginning
df = df.dropna(subset=['us_aqi'])

# We will use 'us_aqi' as our target and main feature
data = df[['us_aqi']].values

# --- Feature Scaling ---
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

# --- Prepare Data for Models ---
# We want to use past 3 days to predict the next day
lookback = 3
X, y = [], []
for i in range(lookback, len(scaled_data)):
    X.append(scaled_data[i-lookback:i, 0])
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)

# Split into Train and Test (80-20, no shuffle for time series)
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# --- 1. Random Forest Training ---
# RF expects 2D input: [samples, features]
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# RF Predictions
rf_pred_scaled = rf_model.predict(X_test)

# --- 2. LSTM Training ---
# Check if tensorflow is available
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout

    # LSTM expects 3D input: [samples, time_steps, features]
    X_train_lstm = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
    X_test_lstm = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    lstm_model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(1)
    ])
    lstm_model.compile(optimizer='adam', loss='mse')
    lstm_model.fit(X_train_lstm, y_train, epochs=20, batch_size=32, verbose=0)

    lstm_pred_scaled = lstm_model.predict(X_test_lstm).flatten()
    lstm_available = True
except ImportError:
    lstm_available = False
    print("Tensorflow not available. Skipping LSTM.")

# --- Evaluation ---
# Invert scaling to get real AQI values
y_test_real = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
rf_pred_real = scaler.inverse_transform(rf_pred_scaled.reshape(-1, 1)).flatten()

# RF Metrics
rf_mae = mean_absolute_error(y_test_real, rf_pred_real)
rf_rmse = np.sqrt(mean_squared_error(y_test_real, rf_pred_real))

print(f"Random Forest - MAE: {rf_mae:.2f}, RMSE: {rf_rmse:.2f}")

if lstm_available:
    lstm_pred_real = scaler.inverse_transform(lstm_pred_scaled.reshape(-1, 1)).flatten()
    lstm_mae = mean_absolute_error(y_test_real, lstm_pred_real)
    lstm_rmse = np.sqrt(mean_squared_error(y_test_real, lstm_pred_real))
    print(f"LSTM - MAE: {lstm_mae:.2f}, RMSE: {lstm_rmse:.2f}")

    # Save LSTM model
    lstm_model.save('mumbai_aqi_lstm.h5')
else:
    lstm_mae, lstm_rmse = None, None

# Save RF model and Scaler
joblib.dump(rf_model, 'mumbai_aqi_rf.pkl')
joblib.dump(scaler, 'scaler.pkl')