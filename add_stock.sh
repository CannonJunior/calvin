#!/bin/bash

# Add Stock to Calvin Earnings System
# Usage: ./add_stock.sh SYMBOL

if [ $# -eq 0 ]; then
    echo "Usage: $0 <STOCK_SYMBOL>"
    echo "Example: $0 MSFT"
    echo ""
    echo "This script will:"
    echo "  1. Fetch company information from Financial Modeling Prep API"
    echo "  2. Retrieve historical and future earnings data"
    echo "  3. Calculate price changes for past earnings"
    echo "  4. Store all data in the Calvin earnings database"
    echo ""
    echo "Make sure to configure your API keys in config.json first!"
    exit 1
fi

SYMBOL=$(echo "$1" | tr '[:lower:]' '[:upper:]')

echo "🚀 Adding $SYMBOL to Calvin Earnings System..."
echo ""

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "❌ config.json not found!"
    echo "Please run ./start-dashboard.sh first to create the config file"
    echo "and add your API keys."
    exit 1
fi

# Validate config.json
if ! python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "❌ config.json is not valid JSON. Please check the file format."
    exit 1
fi

# Check if required APIs are configured
API_KEY=$(python3 -c "
import json
try:
    with open('config.json') as f:
        config = json.load(f)
    key = config['api_keys']['financial_modeling_prep']
    if key == 'demo' or key == 'YOUR_FMP_API_KEY_HERE':
        print('demo')
    else:
        print('configured')
except:
    print('error')
")

if [ "$API_KEY" = "demo" ]; then
    echo "⚠️  WARNING: Using demo API key for Financial Modeling Prep"
    echo "This may result in limited data. Please add your real API key to config.json"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
elif [ "$API_KEY" = "error" ]; then
    echo "❌ Error reading API configuration from config.json"
    exit 1
fi

# Check if Python dependencies are available
if ! python3 -c "import psycopg2, requests" 2>/dev/null; then
    echo "❌ Missing required Python dependencies"
    echo "Please install: pip install psycopg2-binary requests"
    exit 1
fi

# Check if database is accessible
if ! python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost', port=5432, database='calvin_earnings',
        user='calvin_user', password='calvin_pass'
    )
    conn.close()
    print('ok')
except:
    print('error')
" | grep -q "ok"; then
    echo "❌ Cannot connect to Calvin earnings database"
    echo "Make sure PostgreSQL is running and the database is initialized"
    echo "Run: docker-compose up -d postgres"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Run the curation script
echo "📊 Starting data curation for $SYMBOL..."
python3 curate_stock_data.py "$SYMBOL"

RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "🎉 Successfully added $SYMBOL to the Calvin earnings system!"
    echo ""
    echo "Next steps:"
    echo "  - View the data in the earnings dashboard"
    echo "  - Check the database for new earnings entries"
    echo "  - The stock will now appear in earnings timeline visualizations"
else
    echo "❌ Failed to add $SYMBOL to the system"
    echo ""
    echo "Possible causes:"
    echo "  - Symbol not found or invalid"
    echo "  - API rate limits exceeded"
    echo "  - Network connectivity issues"
    echo "  - Database connection problems"
    echo ""
    echo "Check the logs above for specific error details"
fi

exit $RESULT