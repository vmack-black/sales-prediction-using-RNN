#!/bin/bash
# ================================================================
#  Juice Shop - All-in-One Start Script
#  Starts the Python backend and Node.js frontend
# ================================================================

echo ""
echo "================================================"
echo "  🥤  JUICE SHOP - STARTING  🥤"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ===== CLEAN UP =====
echo "🧹 Cleaning up existing processes..."
fuser -k 5000/tcp 2>/dev/null && echo "   Stopped backend on port 5000" || true
fuser -k 3000/tcp 2>/dev/null && echo "   Stopped frontend on port 3000" || true
sleep 2

# ===== CHECK DEPENDENCIES =====
echo ""
echo "📋 Checking dependencies..."

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "   Installing Node.js dependencies first..."
    cd frontend && npm install --silent && cd ..
fi

# Check if database exists
if [ ! -f "backend/juice_shop.db" ]; then
    echo "   Initializing database first..."
    cd backend && python3 database.py && cd ..
fi

# Check if model exists
if [ ! -f "ml_model/sales_rnn_model.h5" ]; then
    echo "   Training RNN model first (this takes ~1-2 minutes)..."
    cd ml_model && python3 train_model.py 2>&1 | grep -E "(Model saved|Done|Training)" | head -3 && cd ..
fi

ok() { echo "   ✅ $1"; }
fail() { echo "   ❌ $1"; }

# ===== STEP 1: Start Python Backend =====
echo ""
echo "🐍 Step 1: Starting Python Flask backend (port 5000)..."
cd backend
nohup python3 app.py > /tmp/juice_backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 5

if curl -s http://localhost:5000/api/products > /dev/null 2>&1; then
    ok "Backend running on http://localhost:5000 (PID: $BACKEND_PID)"
else
    fail "Backend failed to start!"
    echo "   Log: /tmp/juice_backend.log"
    tail -10 /tmp/juice_backend.log
    exit 1
fi

# ===== STEP 2: Start Node.js Frontend =====
echo ""
echo "🟢 Step 2: Starting Node.js frontend (port 3000)..."
cd frontend
nohup node server.js > /tmp/juice_frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 4

if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    ok "Frontend running on http://localhost:3000 (PID: $FRONTEND_PID)"
else
    fail "Frontend failed to start!"
    echo "   Log: /tmp/juice_frontend.log"
    tail -10 /tmp/juice_frontend.log
    exit 1
fi

# ===== DONE =====
echo ""
echo "================================================"
echo "  🎉  JUICE SHOP IS RUNNING!  🎉"
echo "================================================"
echo ""
echo "  📱 Frontend:  http://localhost:3000"
echo "  🔧 Backend:   http://localhost:5000"
echo ""
echo "  🔐 Login Credentials:"
echo "     Customer: customer / customer123"
echo "     Manager:  manager / manager123"
echo ""
echo "  📊 Backend PID:  $BACKEND_PID"
echo "  📊 Frontend PID: $FRONTEND_PID"
echo ""
echo "  🛑 To stop:  fuser -k 5000/tcp 3000/tcp"
echo "================================================"
echo ""
