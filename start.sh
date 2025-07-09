#!/bin/bash
# Calvin Stock Prediction Tool Startup Script

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Calvin Stock Prediction Tool..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed. Please install pip."
    exit 1
fi

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Download NLTK data for TextBlob if needed
echo "📚 Setting up NLP dependencies..."
python -c "
import nltk
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/brown')
except LookupError:
    print('Downloading NLTK data...')
    nltk.download('punkt', quiet=True)
    nltk.download('brown', quiet=True)
"

# Create assets directory if it doesn't exist
mkdir -p assets/sp500_companies
mkdir -p assets/earnings_data
mkdir -p assets/predictions

# Check if Ollama is running (optional)
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running at localhost:11434. AI features will be limited."
    echo "   To enable AI features, install and start Ollama: https://ollama.ai"
fi

# Start the main client
echo "🎯 Starting Calvin Stock Prediction Tool main client..."
python3 main_client.py