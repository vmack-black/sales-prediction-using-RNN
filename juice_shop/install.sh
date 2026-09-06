#!/bin/bash
# ================================================================
#  Juice Shop - All-in-One Installer
#  Installs all dependencies, initializes database, trains RNN
# ================================================================

set -e

echo ""
echo "================================================"
echo "  🥤  JUICE SHOP - INSTALLER  🥤"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
err()  { echo -e "${RED}  ❌ $1${NC}"; }
info() { echo -e "${CYAN}  ℹ️  $1${NC}"; }

# ===== STEP 1: Check Python =====
echo "── Step 1: Checking Python ────────────────────"
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1)
    ok "Python found: $PYVER"
else
    err "Python 3 not found!"
    echo "  Please install Python 3.11+:"
    echo "    Ubuntu: sudo apt install python3 python3-pip"
    echo "    macOS:  brew install python@3.11"
    echo "    Windows: choco install python"
    exit 1
fi

# ===== STEP 2: Check Node.js =====
echo ""
echo "── Step 2: Checking Node.js ───────────────────"
if command -v node &>/dev/null; then
    NODEVER=$(node --version 2>&1)
    ok "Node.js found: $NODEVER"
else
    err "Node.js not found!"
    echo "  Please install Node.js 20+:"
    echo "    Ubuntu: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install nodejs"
    echo "    macOS:  brew install node@20"
    echo "    Windows: choco install nodejs-lts"
    exit 1
fi

if command -v npm &>/dev/null; then
    ok "npm found: $(npm --version)"
else
    err "npm not found!"
    exit 1
fi

# ===== STEP 3: Install Python Dependencies =====
echo ""
echo "── Step 3: Installing Python dependencies ─────"
info "Installing: flask, flask-cors, tensorflow, numpy"
pip install --quiet flask flask-cors tensorflow numpy 2>&1 | grep -v "WARNING" || true
ok "Python dependencies installed"

# Verify key packages
python3 -c "import flask; import flask_cors" 2>/dev/null && ok "Flask verified" || warn "Flask import issue - check pip"
python3 -c "import tensorflow" 2>/dev/null && ok "TensorFlow verified" || warn "TensorFlow not available - will use statistical fallback for predictions"
python3 -c "import numpy" 2>/dev/null && ok "NumPy verified" || warn "NumPy import issue"

# ===== STEP 4: Initialize Database =====
echo ""
echo "── Step 4: Initializing database ──────────────"
cd backend
python3 database.py
cd ..
ok "Database ready (20 products, 2 users)"

# ===== STEP 5: Train RNN Model =====
echo ""
echo "── Step 5: Training RNN (LSTM) model ──────────"
if [ -f "ml_model/sales_rnn_model.h5" ]; then
    warn "Model already exists. Skipping training."
    info "To retrain: rm ml_model/sales_rnn_model.h5 && ./install.sh"
else
    info "Training LSTM neural network (this takes ~1-2 minutes)..."
    cd ml_model
    python3 train_model.py 2>&1 | grep -E "(Training|Epoch 1/|Epoch 100/|Model saved|Done|ERROR|WARNING: TensorFlow)" | head -10
    cd ..
    if [ -f "ml_model/sales_rnn_model.h5" ]; then
        ok "RNN model trained and saved"
    else
        warn "Model training may have had issues. Statistical fallback will be used."
    fi
fi

# ===== STEP 6: Install Node.js Dependencies =====
echo ""
echo "── Step 6: Installing Node.js dependencies ────"
cd frontend
info "Running npm install (this takes ~1 minute)..."
npm install --silent 2>&1 | tail -3 || true
cd ..
if [ -d "frontend/node_modules" ] && [ -d "frontend/node_modules/express" ]; then
    ok "Node.js dependencies installed"
else
    err "npm install failed. Try manually: cd frontend && npm install"
    exit 1
fi

# ===== DONE =====
echo ""
echo "================================================"
echo "  🎉  INSTALLATION COMPLETE!  🎉"
echo "================================================"
echo ""
echo "  To start the application, run:"
echo ""
echo "    ./start.sh"
echo ""
echo "  Then open: http://localhost:3000"
echo ""
echo "  Demo Credentials:"
echo "    Customer: customer / customer123"
echo "    Manager:  manager / manager123"
echo ""
echo "================================================"
echo ""
