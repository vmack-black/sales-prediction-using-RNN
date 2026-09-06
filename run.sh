#!/bin/bash
# ================================================================
#  Juice Shop - RUN (Install + Start in one command)
#  First run: installs everything and starts the app
#  Subsequent runs: just starts the app
# ================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🥤 Juice Shop - Quick Run"
echo ""

# Check if already installed
NEEDS_INSTALL=false

if [ ! -d "frontend/node_modules" ]; then
    NEEDS_INSTALL=true
fi
if [ ! -f "backend/juice_shop.db" ]; then
    NEEDS_INSTALL=true
fi
if ! python3 -c "import flask" 2>/dev/null; then
    NEEDS_INSTALL=true
fi

if [ "$NEEDS_INSTALL" = true ]; then
    echo "📦 First run detected - installing dependencies..."
    echo ""
    chmod +x install.sh
    ./install.sh
    echo ""
    echo "Starting application..."
    echo ""
fi

chmod +x start.sh
./start.sh
