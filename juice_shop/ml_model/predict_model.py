"""
Juice Shop - Sales Prediction Module
Loads the trained RNN (LSTM) model and predicts future sales.
Falls back to statistical moving-average model if RNN model not available.
"""
import os
import numpy as np
import datetime

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "sales_rnn_model.h5")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.npy")
SEQ_LENGTH = 14

_model = None
_tf_available = False

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    _tf_available = True
except Exception:
    _tf_available = False

def _load_model():
    global _model
    if _model is not None:
        return _model
    if _tf_available and os.path.exists(MODEL_PATH):
        try:
            _model = load_model(MODEL_PATH, compile=False)
            return _model
        except Exception:
            pass
    return None

def get_model_info():
    """Return info about the loaded model."""
    model = _load_model()
    scaler = _load_scaler()
    if model is not None:
        return {"status": "RNN (LSTM) model loaded", "model_type": "LSTM",
                "sequence_length": SEQ_LENGTH, "framework": "TensorFlow/Keras",
                "scaler": {"mean": float(scaler[0]), "std": float(scaler[1])}}
    elif os.path.exists(SCALER_PATH):
        return {"status": "Fallback statistical model (moving average)", "model_type": "MovingAverage",
                "sequence_length": SEQ_LENGTH, "framework": "NumPy (statistical fallback)"}
    return {"status": "No model trained yet - run train_model.py", "model_type": "none"}

def _load_scaler():
    if os.path.exists(SCALER_PATH):
        return np.load(SCALER_PATH)
    return np.array([30.0, 10.0])  # default

def _get_recent_sales():
    """Get recent sales quantities from DB."""
    import sqlite3
    db = os.path.join(os.path.dirname(__file__), "..", "backend", "juice_shop.db")
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT date, SUM(quantity_sold) as qty FROM sales_history GROUP BY date ORDER BY date DESC LIMIT 30").fetchall()
        conn.close()
        if rows:
            return [r[1] for r in reversed(rows)]
    # Fallback synthetic-ish data
    np.random.seed(42)
    base = 30
    data = []
    for i in range(30):
        d = datetime.date.today() - datetime.timedelta(days=29-i)
        wk = 1.4 if d.weekday() >= 5 else 1.0
        data.append(max(5, int(base * wk * (1 + i*0.01) + np.random.normal(0, 5))))
    return data

def predict_future_sales(days=7):
    """
    Predict sales for the next `days` days.
    Returns list of {date, predicted_qty, predicted_revenue, confidence}
    """
    model = _load_model()
    scaler = _load_scaler()
    q_mean, q_std = float(scaler[0]), float(scaler[1])

    recent = _get_recent_sales()
    if len(recent) < SEQ_LENGTH:
        # pad with mean
        recent = [int(q_mean)] * (SEQ_LENGTH - len(recent)) + recent

    # Take last SEQ_LENGTH as seed
    window = np.array(recent[-SEQ_LENGTH:], dtype=float)
    window_norm = (window - q_mean) / q_std

    predictions = []
    today = datetime.date.today()

    for i in range(days):
        if model is not None:
            x = window_norm.reshape(1, SEQ_LENGTH, 1)
            pred_norm = model.predict(x, verbose=0)[0][0]
            pred_qty = pred_norm * q_std + q_mean
        else:
            # Fallback: weighted moving average with trend
            weights = np.array([0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 0.15, 0.15, 0.3])
            weights = weights / weights.sum()
            pred_qty = np.dot(window_norm[-len(weights):], weights) * q_std + q_mean
            # add slight upward trend
            pred_qty = pred_qty * (1 + i * 0.005)

        pred_qty = max(1, int(round(pred_qty)))
        pred_rev = round(pred_qty * 5.0, 2)

        # Confidence based on model type
        confidence = 85 if model is not None else 70

        pred_date = (today + datetime.timedelta(days=i+1)).isoformat()
        day_name = (today + datetime.timedelta(days=i+1)).strftime("%A")
        predictions.append({
            "date": pred_date,
            "day": day_name,
            "predicted_qty": pred_qty,
            "predicted_revenue": pred_rev,
            "confidence": confidence,
            "model": "LSTM-RNN" if model is not None else "MovingAverage-Fallback"
        })

        # Update window for next prediction
        new_val = (pred_qty - q_mean) / q_std
        window_norm = np.append(window_norm[1:], new_val)

    return predictions

if __name__ == "__main__":
    info = get_model_info()
    print("Model Info:", info)
    preds = predict_future_sales(7)
    print("\n7-Day Sales Prediction:")
    for p in preds:
        print(f"  {p['date']} ({p['day']}): {p['predicted_qty']} units | ${p['predicted_revenue']} | confidence: {p['confidence']}%")
