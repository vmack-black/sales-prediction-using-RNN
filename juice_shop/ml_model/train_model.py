"""
Juice Shop - RNN Sales Prediction Model
Uses LSTM (a type of RNN) to predict future sales based on historical data.
- Generates synthetic sales data if no real data exists
- Trains LSTM model
- Saves model to disk for use by the Flask backend
"""
import os
import numpy as np
import datetime
import sqlite3

# TensorFlow imports
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False
    print("WARNING: TensorFlow not available. Will use fallback statistical model.")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "juice_shop.db")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "sales_rnn_model.h5")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.npy")

SEQ_LENGTH = 14  # use 14 days history to predict next day

def generate_synthetic_sales(days=90):
    """Generate synthetic daily sales data with trends and weekly seasonality."""
    np.random.seed(42)
    dates = [(datetime.date.today() - datetime.timedelta(days=days-i)) for i in range(days)]
    sales = []
    base = 30
    for i, d in enumerate(dates):
        # weekly seasonality (weekends sell more)
        dow = d.weekday()
        weekend_boost = 1.4 if dow >= 5 else 1.0
        # upward trend
        trend = 1 + (i / days) * 0.5
        # random noise
        noise = np.random.normal(0, 5)
        qty = max(5, int(base * weekend_boost * trend + noise))
        revenue = round(qty * 5.0 + np.random.normal(0, 2), 2)
        sales.append({"date": d.isoformat(), "qty": qty, "revenue": revenue})
    return sales

def get_or_create_sales_data():
    """Get sales data from DB, or generate synthetic if insufficient."""
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT date, SUM(quantity_sold) as qty, SUM(revenue) as rev FROM sales_history GROUP BY date ORDER BY date").fetchall()
        conn.close()
        if len(rows) >= SEQ_LENGTH + 10:
            return [{"date": r[0], "qty": r[1], "revenue": r[2]} for r in rows]
    # Generate synthetic and save to DB
    sales = generate_synthetic_sales(90)
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        products = conn.execute("SELECT id FROM products").fetchall()
        if products:
            for s in sales:
                # distribute daily qty across products
                remaining = s["qty"]
                for j, (pid,) in enumerate(products):
                    if j == len(products)-1:
                        q = remaining
                    else:
                        q = max(1, remaining // (len(products)-j))
                        remaining -= q
                    conn.execute("INSERT OR IGNORE INTO sales_history (product_id, date, quantity_sold, revenue) VALUES (?,?,?,?)",
                                 (pid, s["date"], q, round(q*5,2)))
            conn.commit()
        conn.close()
    return sales

def create_sequences(data, seq_length):
    """Create input sequences and targets for the RNN."""
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

def train_model():
    """Train the LSTM model on sales data."""
    sales = get_or_create_sales_data()
    quantities = np.array([s["qty"] for s in sales], dtype=float)

    # Normalize
    q_mean = quantities.mean()
    q_std = quantities.std() if quantities.std() > 0 else 1
    quantities_norm = (quantities - q_mean) / q_std

    # Save scaler params
    np.save(SCALER_PATH, np.array([q_mean, q_std]))

    if TF_AVAILABLE:
        X, y = create_sequences(quantities_norm, SEQ_LENGTH)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        model = Sequential([
            LSTM(64, activation="relu", return_sequences=True, input_shape=(SEQ_LENGTH, 1)),
            Dropout(0.2),
            LSTM(32, activation="relu"),
            Dropout(0.2),
            Dense(16, activation="relu"),
            Dense(1)
        ])
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        print(f"Training RNN (LSTM) model on {len(X)} sequences...")
        es = EarlyStopping(monitor="loss", patience=15, restore_best_weights=True)
        model.fit(X, y, epochs=100, batch_size=8, verbose=1, callbacks=[es])
        model.save(MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")
        return model, q_mean, q_std, True
    else:
        print("TensorFlow not available. Saving fallback model info.")
        np.save(SCALER_PATH, np.array([q_mean, q_std]))
        return None, q_mean, q_std, False

if __name__ == "__main__":
    print("=" * 60)
    print("Juice Shop - RNN Sales Prediction Model Training")
    print("=" * 60)
    train_model()
    print("Done!")
