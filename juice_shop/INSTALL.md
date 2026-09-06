# Juice Shop - All-in-One Installation Guide

## Quick Start (3 Steps)

### Step 1: Extract the package
```bash
unzip juice_shop_all_in_one.zip
cd juice_shop
```

### Step 2: Run the installer (installs all dependencies + trains model)
```bash
chmod +x install.sh
./install.sh
```

### Step 3: Start the application
```bash
./start.sh
```

Then open: **http://localhost:3000**

---

## Demo Credentials
| Role | Username | Password |
|------|----------|----------|
| Customer | `customer` | `customer123` |
| Manager | `manager` | `manager123` |

---

## Prerequisites (auto-installed by install.sh)

### For Python Backend + RNN Model:
- Python 3.11+
- pip

### For Node.js Frontend:
- Node.js 20+
- npm

The install.sh script checks for these and will attempt to install them if missing.

---

## Manual Step-by-Step Installation

If you prefer to install each component manually, follow these steps:

### 1. Install System Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip curl unzip
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**macOS (Homebrew):**
```bash
brew install python@3.11 node@20
```

**Windows (Chocolatey):**
```powershell
choco install python nodejs-lts
```

### 2. Install Python Dependencies (Backend + ML)
```bash
cd juice_shop/backend
pip install -r requirements.txt
cd ..
```

### 3. Initialize the Database
```bash
cd backend
python3 database.py
cd ..
```
This creates the SQLite database with:
- 2 demo users (customer + manager)
- 20 juice products
- Empty tables for orders, reviews, inventory, alerts, sales history

### 4. Train the RNN (LSTM) Sales Prediction Model
```bash
cd ml_model
python3 train_model.py
cd ..
```
This:
- Generates synthetic sales data (90 days with weekly seasonality)
- Trains an LSTM neural network (100 epochs)
- Saves the model to `ml_model/sales_rnn_model.h5`

### 5. Install Node.js Dependencies (Frontend)
```bash
cd frontend
npm install
cd ..
```

### 6. Start the Backend (Port 5000)
```bash
cd backend
python3 app.py
```
Keep this terminal running.

### 7. Start the Frontend (Port 3000)
Open a NEW terminal:
```bash
cd juice_shop/frontend
node server.js
```
Keep this terminal running.

### 8. Open Your Browser
Go to: **http://localhost:3000**

---

## All-in-One Start Script

Use `start.sh` to start everything at once:
```bash
./start.sh
```
This script:
1. Kills any existing processes on ports 5000 and 3000
2. Initializes the database
3. Trains the RNN model (if not already trained)
4. Starts the Python backend
5. Starts the Node.js frontend
6. Verifies both services are running

---

## Stopping the Application
```bash
fuser -k 5000/tcp 3000/tcp
```
Or simply close both terminal windows.

---

## Troubleshooting

### Port already in use
```bash
fuser -k 5000/tcp   # kill backend
fuser -k 3000/tcp   # kill frontend
```

### Python dependencies fail to install
```bash
pip install flask flask-cors tensorflow numpy
```

### Node.js dependencies fail
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### RNN model not loading
Re-train the model:
```bash
cd ml_model
python3 train_model.py
```

### Database needs reset
```bash
rm backend/juice_shop.db
cd backend && python3 database.py && cd ..
```

### TensorFlow import error
The prediction system has a built-in fallback. If TensorFlow is not available, it uses a weighted moving average statistical model. You can still use all features.

---

## Architecture Overview

```
Browser (http://localhost:3000)
       │
       ▼
┌──────────────┐     HTTP/API     ┌──────────────────┐
│   FRONTEND   │ ◄──────────────► │     BACKEND      │
│   Node.js    │                  │    Python Flask   │
│  Express+EJS │                  │   REST API (5000) │
│   Port 3000  │                  │                   │
└──────────────┘                  └────────┬──────────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                        ┌─────────┐ ┌──────────┐ ┌──────────┐
                        │ RNN/LSTM│ │ SQLite   │ │ Sales    │
                        │ Model   │ │ Database │ │ History  │
                        │(TF/Keras│ │ 20 prods │ │ 90+ days │
                        └─────────┘ └──────────┘ └──────────┘
```
