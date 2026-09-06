#!/bin/bash
# Juice Shop - Stop Script
echo "🛑 Stopping Juice Shop..."
fuser -k 5000/tcp 2>/dev/null && echo "   ✅ Backend stopped (port 5000)" || echo "   Backend was not running"
fuser -k 3000/tcp 2>/dev/null && echo "   ✅ Frontend stopped (port 3000)" || echo "   Frontend was not running"
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "node server.js" 2>/dev/null || true
echo ""
echo "✅ Juice Shop stopped."
