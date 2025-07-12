#!/bin/bash

# API Keys Export Script for Calvin Stock Prediction Tool
# This script exports API keys from config/api_keys.env as environment variables

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_KEYS_FILE="$SCRIPT_DIR/api_keys.env"

echo "🔑 Calvin Stock Prediction Tool - API Keys Setup"
echo "================================================"

# Check if API keys file exists
if [ ! -f "$API_KEYS_FILE" ]; then
    echo "❌ Error: API keys file not found at $API_KEYS_FILE"
    echo "Please create the file by copying from config/api_keys.env.example"
    exit 1
fi

echo "📁 Loading API keys from: $API_KEYS_FILE"

# Read and export each API key
while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip empty lines and comments
    if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Remove leading/trailing whitespace
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Export the environment variable
    if [ -n "$value" ] && [ "$value" != "your_*_api_key_here" ]; then
        export "$key=$value"
        
        # Show masked key for security
        if [[ "$key" == *"API_KEY"* ]]; then
            masked_value="${value:0:8}...${value: -4}"
            echo "✅ Exported $key: $masked_value"
        else
            echo "✅ Exported $key: $value"
        fi
    else
        echo "⚠️  Warning: $key is not set or has placeholder value"
    fi
done < "$API_KEYS_FILE"

echo ""
echo "🔐 API Key Validation"
echo "===================="

# Validate required API keys
required_keys=("POLYGON_API_KEY" "ALPHA_VANTAGE_API_KEY" "TAVILY_API_KEY")
missing_keys=()

for key in "${required_keys[@]}"; do
    if [ -z "${!key}" ] || [[ "${!key}" == *"your_"*"_api_key_here" ]]; then
        missing_keys+=("$key")
    fi
done

if [ ${#missing_keys[@]} -gt 0 ]; then
    echo "⚠️  Warning: The following required API keys are missing or have placeholder values:"
    for key in "${missing_keys[@]}"; do
        echo "   - $key"
    done
    echo ""
    echo "📋 To get free API keys:"
    echo "   - Polygon.io: https://polygon.io/ (5 calls/minute free)"
    echo "   - Alpha Vantage: https://www.alphavantage.co/ (500 calls/day free)"
    echo "   - Tavily: https://tavily.com/ (1,000 credits/month free)"
    echo "   - Financial Modeling Prep: https://financialmodelingprep.com/ (250 requests free)"
    echo ""
    echo "🚀 You can still run the system with limited functionality using yfinance (no API key required)"
else
    echo "✅ All required API keys are configured!"
fi

echo ""
echo "🚀 Next Steps"
echo "============"
echo "1. Run: docker-compose up -d"
echo "2. Initialize Ollama models: docker-compose exec ollama ollama pull llama3.1:8b"
echo "3. Load S&P 500 data: docker-compose exec backend uv run scripts/load_sp500_data.py"
echo "4. Access web interface: http://localhost:3000"
echo ""

# Save current environment to a temporary file for docker-compose
ENV_FILE="$SCRIPT_DIR/../.env.generated"
echo "# Generated environment file - DO NOT EDIT MANUALLY" > "$ENV_FILE"
echo "# Generated at: $(date)" >> "$ENV_FILE"
echo "" >> "$ENV_FILE"

# Export database and service configurations
cat << EOF >> "$ENV_FILE"
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=stockprediction
POSTGRES_USER=postgres
POSTGRES_PASSWORD=stockprediction123

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Application Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=calvin-secret-key-change-in-production
API_V1_STR=/api/v1

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Security
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

EOF

# Append API keys to the generated env file
while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip empty lines and comments
    if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Remove leading/trailing whitespace
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    if [ -n "$key" ]; then
        echo "$key=$value" >> "$ENV_FILE"
    fi
done < "$API_KEYS_FILE"

echo "📝 Generated .env.generated file for docker-compose"
echo "🔒 Environment variables exported to current shell session"
echo ""
echo "💡 Tip: Add 'source config/export_api_keys.sh' to your ~/.bashrc or ~/.zshrc"
echo "   to automatically load API keys in new terminal sessions"