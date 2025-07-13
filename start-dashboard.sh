#!/bin/bash

echo "Starting Earnings Dashboard with MCP Integration..."

# Check if config.json exists, if not create it from template
if [ ! -f "config.json" ]; then
    echo "Config file not found. Creating config.json from template..."
    if [ -f "config.example.json" ]; then
        cp config.example.json config.json
        echo "✅ Created config.json from config.example.json"
        echo "⚠️  Please edit config.json and add your API keys:"
        echo "   - Alpha Vantage: https://www.alphavantage.co/support/#api-key"
        echo "   - Finnhub: https://finnhub.io/register"
        echo "   - Financial Modeling Prep: https://financialmodelingprep.com/developer/docs"
        echo ""
    else
        echo "❌ config.example.json not found. Cannot create config.json"
        exit 1
    fi
else
    echo "✅ Found config.json"
fi

# Validate config.json format
if ! python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "❌ config.json is not valid JSON. Please check the file format."
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Warning: Ollama is not running on localhost:11434"
    echo "Please start Ollama first: ollama serve"
fi

# Start the HTTP server
echo "Starting HTTP server on http://localhost:8080"
npm run dev