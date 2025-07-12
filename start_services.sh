#!/bin/bash

# Start S&P 500 Dashboard Services
# This script starts the API server and web server for the dashboard

echo "🚀 Starting S&P 500 Dashboard Services..."

# Check if required files exist
if [ ! -f "sp500_companies.json" ]; then
    echo "📊 S&P 500 data not found, fetching from Wikipedia..."
    python3 fetch_sp500.py
fi

# Start the S&P 500 API service in background
echo "🔌 Starting S&P 500 API service on port 5001..."
python3 sp500_api.py &
API_PID=$!

# Wait a moment for API to start
sleep 2

# Start the web server for the dashboard
echo "🌐 Starting web server on port 8080..."
python3 -m http.server 8080 &
WEB_PID=$!

# Wait a moment for web server to start
sleep 2

echo "✅ Services started successfully!"
echo ""
echo "📱 Dashboard URL: http://localhost:8080/earnings_dashboard.html"
echo "🔗 API Health: http://localhost:5001/api/health"
echo "📊 API Companies: http://localhost:5001/api/companies"
echo ""
echo "💡 The dashboard now loads all 503 S&P 500 companies from Wikipedia"
echo "📈 Real sector data is displayed in the portfolio section"
echo "🎯 Use Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_PID $WEB_PID 2>/dev/null
    echo "👋 All services stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait