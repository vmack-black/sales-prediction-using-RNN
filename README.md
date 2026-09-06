# 🥤 Juice Shop - Full Stack Application

A complete juice shop web application with two user roles (Customer & Manager), built with a **Node.js frontend**, **Python Flask backend**, and an **RNN (LSTM) model for sales prediction**.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    JUICE SHOP                             │
│                                                          │
│  ┌──────────────┐     HTTP/API     ┌──────────────────┐  │
│  │   FRONTEND   │ ◄──────────────► │     BACKEND      │  │
│  │   Node.js    │                  │    Python Flask   │  │
│  │  Express+EJS │                  │   REST API (5000) │  │
│  │   Port 3000  │                  │                   │  │
│  └──────────────┘                  └────────┬──────────┘  │
│                                              │             │
│                                              ▼             │
│                                    ┌──────────────────┐   │
│                                    │   ML MODEL (RNN) │   │
│                                    │  TensorFlow/Keras│   │
│                                    │  LSTM Prediction  │   │
│                                    └────────┬──────────┘   │
│                                              │             │
│                                              ▼             │
│                                    ┌──────────────────┐   │
│                                    │   SQLite DB       │   │
│                                    │  20 products,     │   │
│                                    │  users, orders,   │   │
│                                    │  reviews, alerts  │   │
│                                    └──────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 👥 User Roles

### 🛒 Customer Portal
- **Browse Shop** — View all 20 juice products with category filters
- **Product Details** — Full product info, nutritional data, stock status
- **Shopping Cart** — Add items, adjust quantities, checkout
- **Place Orders** — Submit orders (auto-updates inventory & sales history)
- **My Orders** — View order history with itemized details
- **Reviews & Ratings** — Rate products 1-5 stars and write comments
- **Profile** — View account information

### 📊 Manager Portal
- **Dashboard** — Overview stats (revenue, orders, customers, ratings, alerts)
- **Inventory Management** — View all stock levels, restock products
- **Alerts** — Auto-generated low-stock alerts, resolve alerts, scan for new
- **Sales Prediction (RNN)** — AI-powered 7/14/30-day forecasts using LSTM
- **Sales History** — 30-day sales charts and detailed logs
- **Top Products** — Best-selling items by units and revenue

---

## 🍹 Product Catalog (20 Items)

| # | Product | Category | Price | Size |
|---|---------|----------|-------|------|
| 1 | Orange Burst | Citrus | $4.50 | 250ml |
| 2 | Mango Tango | Tropical | $5.25 | 300ml |
| 3 | Green Detox | Detox | $6.00 | 350ml |
| 4 | Berry Blast | Berry | $5.75 | 300ml |
| 5 | Watermelon Wave | Hydration | $4.25 | 350ml |
| 6 | Pineapple Paradise | Tropical | $5.50 | 300ml |
| 7 | Carrot Glow | Veggie | $4.75 | 250ml |
| 8 | Beet Boost | Veggie | $5.95 | 300ml |
| 9 | Apple Crisp | Fruit | $3.95 | 250ml |
| 10 | Pomegranate Power | Antioxidant | $6.50 | 250ml |
| 11 | Cucumber Cooler | Hydration | $4.00 | 350ml |
| 12 | Strawberry Sunrise | Berry | $5.25 | 300ml |
| 13 | Lemon Zest | Citrus | $3.75 | 300ml |
| 14 | Avocado Cream | Creamy | $7.25 | 350ml |
| 15 | Peach Perfection | Fruit | $5.00 | 300ml |
| 16 | Kiwi Kick | Fruit | $4.85 | 250ml |
| 17 | Coconut Bliss | Tropical | $4.50 | 350ml |
| 18 | Cherry Charm | Berry | $6.25 | 250ml |
| 19 | Grape Galaxy | Fruit | $4.25 | 250ml |
| 20 | Ginger Fire | Wellness | $5.50 | 150ml |

---

## 🧠 RNN Sales Prediction Model

The sales prediction uses a **LSTM (Long Short-Term Memory)** network, a type of Recurrent Neural Network (RNN) designed for time-series forecasting.

### Model Architecture
```
LSTM(64, return_sequences=True) → Dropout(0.2)
LSTM(32) → Dropout(0.2)
Dense(16, relu) → Dense(1)
```

### How It Works
1. **Data Source**: Uses historical sales data from the database (auto-generates synthetic data with weekly seasonality if insufficient real data)
2. **Preprocessing**: Normalizes quantities using mean/std scaling
3. **Sequence Window**: Uses 14 days of history to predict the next day
4. **Training**: 100 epochs with Adam optimizer, MSE loss, early stopping
5. **Prediction**: Autoregressive — each prediction feeds back into the window for multi-step forecasting
6. **Fallback**: If TensorFlow is unavailable, uses weighted moving average as statistical fallback

### Prediction Output
- Daily predicted units sold
- Predicted revenue
- Confidence score
- AI-generated insights (peak demand day, low demand day, stock recommendations)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- pip, npm

### One-Command Startup
```bash
cd juice_shop
chmod +x start.sh
./start.sh
```

### Manual Startup

**1. Install Python dependencies:**
```bash
pip install flask flask-cors tensorflow numpy
```

**2. Install Node.js dependencies:**
```bash
cd frontend
npm install
cd ..
```

**3. Initialize database:**
```bash
cd backend
python3 database.py
cd ..
```

**4. Train RNN model:**
```bash
cd ml_model
python3 train_model.py
cd ..
```

**5. Start backend (port 5000):**
```bash
cd backend
python3 app.py
```

**6. Start frontend (port 3000) — in a new terminal:**
```bash
cd frontend
node server.js
```

**7. Open your browser:**
```
http://localhost:3000
```

---

## 🔐 Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Customer | `customer` | `customer123` |
| Manager | `manager` | `manager123` |

---

## 📁 Project Structure

```
juice_shop/
├── start.sh                    # One-command startup script
├── README.md                   # This file
├── backend/                    # Python Flask Backend
│   ├── app.py                  # Main Flask API (all endpoints)
│   ├── database.py             # SQLite DB schema + seed data
│   └── juice_shop.db           # SQLite database (auto-created)
├── ml_model/                   # RNN Sales Prediction
│   ├── train_model.py          # LSTM model training script
│   ├── predict_model.py        # Prediction module (used by backend)
│   ├── sales_rnn_model.h5      # Trained model (auto-created)
│   └── scaler.npy              # Normalization params
└── frontend/                   # Node.js Frontend
    ├── server.js               # Express server + routes
    ├── package.json            # Node dependencies
    ├── public/
    │   └── css/style.css       # Global stylesheet
    └── views/                  # EJS templates
        ├── landing.ejs         # Home page
        ├── login.ejs           # Login page
        ├── register.ejs        # Registration page
        ├── partials/           # Shared components
        │   ├── header.ejs
        │   ├── footer.ejs
        │   ├── navbar-customer.ejs
        │   └── navbar-manager.ejs
        ├── customer/           # Customer pages
        │   ├── shop.ejs        # Product browsing + cart
        │   ├── product.ejs     # Product detail + reviews
        │   ├── orders.ejs      # Order history
        │   ├── reviews.ejs     # Reviews overview
        │   └── profile.ejs     # Customer profile
        └── manager/            # Manager pages
            ├── dashboard.ejs   # Stats overview
            ├── inventory.ejs   # Stock management
            ├── alerts.ejs      # Alert notifications
            ├── predictions.ejs # RNN sales prediction
            └── sales.ejs       # Sales history charts
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Login (customer/manager) |
| POST | `/api/register` | Register new customer |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all 20 products with ratings |
| GET | `/api/products/:id` | Product detail with reviews |

### Customer: Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders` | Create order (updates inventory) |
| GET | `/api/orders/:user_id` | Get user's order history |
| PUT | `/api/orders/:id/status` | Update order status |

### Customer: Reviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reviews` | Submit/update review & rating |
| GET | `/api/products/:id/reviews` | Get product reviews |

### Manager: Inventory
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/inventory` | All products with stock status |
| PUT | `/api/inventory/:id/restock` | Restock a product |

### Manager: Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | Get active alerts |
| POST | `/api/alerts/check` | Scan for new low-stock alerts |
| PUT | `/api/alerts/:id/resolve` | Resolve an alert |

### Manager: Dashboard & Sales
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Dashboard statistics |
| GET | `/api/sales/history` | Sales history (30 days) |
| GET | `/api/sales/product/:id/history` | Product sales history |

### Manager: Predictions (RNN)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predict/sales?days=7` | Get RNN sales forecast |
| GET | `/api/predict/info` | Get model information |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Node.js, Express, EJS, CSS3 |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite |
| ML Model | TensorFlow/Keras, LSTM (RNN) |
| HTTP Client | Axios (frontend→backend) |

---

## 🔄 Data Flow

1. **Customer browses** → Frontend requests products from backend API
2. **Customer orders** → Backend creates order, deducts stock, records sales history, generates alerts if low
3. **Customer reviews** → Backend stores rating & comment, updates average
4. **Manager views dashboard** → Backend aggregates stats from all tables
5. **Manager runs prediction** → Backend loads LSTM model, uses 14-day sales history, predicts future sales autoregressively
6. **Manager manages inventory** → Restock updates stock, logs changes
7. **Manager handles alerts** → Auto-generated on low stock, manually resolvable
