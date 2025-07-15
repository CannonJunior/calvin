#!/bin/bash

# S&P 500 Earnings Dashboard Starter
# Starts the essential services for earnings_dashboard.html to work properly

echo "🚀 Starting S&P 500 Earnings Dashboard..."

# Check if config.json exists, create from template if needed
if [ ! -f "config.json" ]; then
    echo "⚙️  Config file not found. Creating config.json from template..."
    if [ -f "config.example.json" ]; then
        cp config.example.json config.json
        echo "✅ Created config.json from config.example.json"
        echo "⚠️  Please edit config.json and add your API keys:"
        echo "   - Alpha Vantage: https://www.alphavantage.co/support/#api-key"
        echo "   - Finnhub: https://finnhub.io/register"
        echo "   - Financial Modeling Prep: https://financialmodelingprep.com/developer/docs"
        echo ""
    else
        echo "❌ config.example.json not found. Creating basic config..."
        cat > config.json << 'EOF'
{
  "api_keys": {
    "alpha_vantage": "demo",
    "finnhub": "demo", 
    "financial_modeling_prep": "demo"
  }
}
EOF
        echo "⚠️  Basic config.json created with demo keys. Add real API keys for full functionality."
    fi
else
    echo "✅ Found config.json"
fi

# Validate config.json format
if ! python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "❌ config.json is not valid JSON. Please check the file format."
    exit 1
fi

# Check if S&P 500 data exists, fetch if needed
if [ ! -f "sp500_companies.json" ]; then
    echo "📊 S&P 500 data not found, fetching from Wikipedia..."
    if ! python3 fetch_sp500.py; then
        echo "❌ Failed to fetch S&P 500 data"
        exit 1
    fi
fi

# Check Ollama status (for AI chat functionality)
OLLAMA_RUNNING=false
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running - AI chat enabled"
    OLLAMA_RUNNING=true
else
    echo "⚠️  Ollama not running on localhost:11434"
    echo "   AI chat will be disabled. To enable: ollama serve"
fi

# Start S&P 500 API service (essential for company data)
echo "🔌 Starting S&P 500 API service on port 5001..."
python3 sp500_api.py &
SP500_API_PID=$!

# Wait for S&P 500 API to start
sleep 3

# Check if S&P 500 API started successfully
if ! curl -s http://localhost:5001/api/health > /dev/null; then
    echo "❌ Failed to start S&P 500 API service"
    kill $SP500_API_PID 2>/dev/null
    exit 1
fi

# Start HTTP server to serve the dashboard
echo "🌐 Starting HTTP server on port 8080..."
python3 -m http.server 8080 &
WEB_PID=$!

# Wait for web server to start
sleep 2

# Check if web server started successfully
if ! curl -s http://localhost:8080 > /dev/null; then
    echo "❌ Failed to start web server"
    kill $SP500_API_PID $WEB_PID 2>/dev/null
    exit 1
fi

echo ""
echo "✅ Dashboard services started successfully!"
echo ""
echo "🎯 DASHBOARD ACCESS:"
echo "   📱 Main Dashboard: http://localhost:8080/earnings_dashboard.html"
echo ""
echo "🔗 SERVICE STATUS:"
echo "   📊 S&P 500 API: http://localhost:5001/api/health"
if [ "$OLLAMA_RUNNING" = true ]; then
    echo "   🤖 AI Chat: ✅ Enabled (Ollama running)"
else
    echo "   🤖 AI Chat: ❌ Disabled (start with: ollama serve)"
fi
echo ""
echo "📊 DATA SOURCES:"
echo "   🏢 Companies: S&P 500 from Wikipedia (503 companies)"
echo "   📈 Earnings: Local earnings-icons directory (auto-fallback)"
echo "   💹 Market Data: External APIs (Alpha Vantage, Finnhub, FMP)"
echo ""
echo "💡 FEATURES AVAILABLE:"
echo "   ✅ Interactive earnings timeline with animations"
echo "   ✅ Real-time market data and tooltips"
echo "   ✅ Sector-based portfolio management"
echo "   ✅ Earnings-icons data fallback (no PostgreSQL needed)"
if [ "$OLLAMA_RUNNING" = true ]; then
    echo "   ✅ AI-powered chat interface"
else
    echo "   ⚠️  AI chat disabled (start Ollama to enable)"
fi
echo ""
echo "🎯 Click on timeline icons to see detailed earnings data!"
echo "🔄 Use Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $SP500_API_PID $WEB_PID 2>/dev/null
    echo "👋 Dashboard services stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait