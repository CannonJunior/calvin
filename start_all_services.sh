#!/bin/bash

# Start Complete S&P 500 Dashboard with PostgreSQL Integration
# This script starts all services: PostgreSQL, APIs, and web server

echo "🚀 Starting Complete S&P 500 Dashboard with PostgreSQL..."

# Check if required files exist
if [ ! -f "sp500_companies.json" ]; then
    echo "📊 S&P 500 data not found, fetching from Wikipedia..."
    python3 fetch_sp500.py
fi

# Start PostgreSQL with Docker
echo "🐘 Starting PostgreSQL with pgvector..."
docker-compose up postgres -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 15

# Check if database is populated
COMPANY_COUNT=$(docker exec calvin-postgres psql -U calvin_user -d calvin_earnings -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')

if [ "$COMPANY_COUNT" != "503" ]; then
    echo "📊 Populating database with S&P 500 and earnings data..."
    python3 simple_earnings_ingestion.py
fi

# Start the S&P 500 API service
echo "🔌 Starting S&P 500 API service on port 5001..."
python3 sp500_api.py &
SP500_API_PID=$!

# Start the PostgreSQL Earnings API service
echo "📊 Starting PostgreSQL Earnings API service on port 5002..."
python3 postgres_api.py &
POSTGRES_API_PID=$!

# Wait for APIs to start
sleep 3

# Start the web server for the dashboard
echo "🌐 Starting web server on port 8080..."
python3 -m http.server 8080 &
WEB_PID=$!

# Wait for web server to start
sleep 2

echo "✅ All services started successfully!"
echo ""
echo "🎯 DASHBOARD URLs:"
echo "   📱 Main Dashboard: http://localhost:8080/earnings_dashboard.html"
echo ""
echo "🔗 API Health Checks:"
echo "   📊 S&P 500 API: http://localhost:5001/api/health"
echo "   🐘 PostgreSQL API: http://localhost:5002/api/health"
echo ""
echo "📊 Database Information:"
echo "   🏢 Companies: $(docker exec calvin-postgres psql -U calvin_user -d calvin_earnings -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ') S&P 500 companies"
echo "   📈 Earnings: $(docker exec calvin-postgres psql -U calvin_user -d calvin_earnings -t -c "SELECT COUNT(*) FROM earnings;" 2>/dev/null | tr -d ' ') earnings events"
echo ""
echo "💡 Features:"
echo "   ✅ Real S&P 500 data from Wikipedia (503 companies)"
echo "   ✅ PostgreSQL database with pgvector"
echo "   ✅ Real earnings data for timeline icons"
echo "   ✅ Interactive timeline with hover tooltips"
echo "   ✅ Sector-based portfolio management"
echo "   ✅ AI-powered chat interface"
echo ""
echo "🎯 Click on timeline icons to see real earnings data!"
echo "🔄 Use Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $SP500_API_PID $POSTGRES_API_PID $WEB_PID 2>/dev/null
    docker-compose down postgres
    echo "👋 All services stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait