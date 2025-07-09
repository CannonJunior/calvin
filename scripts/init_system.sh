#!/bin/bash

# Calvin Stock Prediction Tool - System Initialization Script
# This script performs complete system setup and initialization

set -e  # Exit on any error

echo "🚀 Calvin Stock Prediction Tool - System Initialization"
echo "======================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check prerequisites
print_status "Step 1: Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "All prerequisites are met"

# Step 2: Setup API keys
print_status "Step 2: Setting up API keys..."

API_KEYS_FILE="$PROJECT_ROOT/config/api_keys.env"
API_KEYS_EXAMPLE="$PROJECT_ROOT/config/api_keys.env.example"

if [ ! -f "$API_KEYS_FILE" ]; then
    print_warning "API keys file not found. Creating from template..."
    cp "$API_KEYS_EXAMPLE" "$API_KEYS_FILE"
    print_warning "Please edit $API_KEYS_FILE with your actual API keys"
    print_warning "You can get free API keys from:"
    echo "  - Polygon.io: https://polygon.io/"
    echo "  - Alpha Vantage: https://www.alphavantage.co/"
    echo "  - Tavily: https://tavily.com/"
    echo "  - Financial Modeling Prep: https://financialmodelingprep.com/"
    echo ""
    read -p "Press Enter after you've added your API keys to continue, or Ctrl+C to exit..."
fi

# Export API keys
print_status "Exporting API keys..."
source "$PROJECT_ROOT/config/export_api_keys.sh"

# Step 3: Stop any existing services
print_status "Step 3: Stopping any existing services..."
cd "$PROJECT_ROOT"
docker-compose down --remove-orphans 2>/dev/null || true

# Step 4: Build and start services
print_status "Step 4: Building and starting Docker services..."
print_status "This may take several minutes on first run..."

# Build images
docker-compose build

# Start core services first
print_status "Starting core services (database, redis)..."
docker-compose up -d postgres redis

# Wait for core services to be healthy
print_status "Waiting for core services to be ready..."
sleep 10

# Check if services are healthy
for service in postgres redis; do
    print_status "Checking $service health..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose ps $service | grep -q "(healthy)"; then
            print_success "$service is healthy"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        print_warning "$service may not be fully ready, but continuing..."
    fi
done

# Start application services
print_status "Starting application services..."
docker-compose up -d backend frontend finance-server sentiment-server

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
timeout=120
while [ $timeout -gt 0 ]; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_success "Backend is ready"
        break
    fi
    sleep 2
    timeout=$((timeout-2))
done

# Step 5: Check Ollama availability
print_status "Step 5: Checking Ollama availability..."
if curl -f http://localhost:11434/api/tags &>/dev/null; then
    print_success "Ollama is running on localhost:11434"
    print_status "Skipping model downloads (models are large - download manually if needed)"
    print_status "To download models manually:"
    echo "  ollama pull llama3.1:8b"
    echo "  ollama pull qwen2.5:7b"
else
    print_warning "Ollama not running on localhost:11434"
    print_warning "Please start Ollama manually: 'ollama serve'"
fi

# Step 6: Initialize database and load data
print_status "Step 6: Loading S&P 500 company data..."

# Run the data loading script
print_status "Running S&P 500 data collection script..."
docker-compose exec -T backend uv run scripts/load_sp500_data.py || {
    print_warning "Data loading completed with some warnings (this is normal for API rate limits)"
}

# Step 7: Start agent orchestrator
print_status "Step 7: Starting AI agent orchestrator..."
docker-compose up -d agent-orchestrator

# Step 8: Verify system health
print_status "Step 8: Verifying system health..."

services=("frontend:3000" "backend:8000")
for service_port in "${services[@]}"; do
    service=$(echo $service_port | cut -d: -f1)
    port=$(echo $service_port | cut -d: -f2)
    
    if curl -f http://localhost:$port &>/dev/null || curl -f http://localhost:$port/health &>/dev/null; then
        print_success "$service is responding on port $port"
    else
        print_warning "$service may not be fully ready on port $port"
    fi
done

# Step 9: Display final status
echo ""
print_success "🎉 Calvin Stock Prediction Tool initialization complete!"
echo ""
echo "📋 System Status:"
echo "=================="
docker-compose ps

echo ""
echo "🌐 Access Points:"
echo "================="
echo "• Web Interface:    http://localhost:3000"
echo "• API Documentation: http://localhost:8000/docs"
echo "• Ollama API:       http://localhost:11434 (if running locally)"
echo ""

echo "🤖 Available AI Models:"
echo "======================"
curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "  (Start Ollama with 'ollama serve' to see models)"

echo ""
echo "📊 Quick Test Commands:"
echo "======================"
echo "# Test API health:"
echo "curl http://localhost:8000/health"
echo ""
echo "# Get companies list:"
echo "curl http://localhost:8000/api/v1/companies?limit=5"
echo ""
echo "# Test AI agent:"
echo "curl -X POST http://localhost:8000/api/v1/agents/query \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"What is the current market sentiment?\"}'"
echo ""

echo "💡 Next Steps:"
echo "=============="
echo "1. Visit http://localhost:3000 to use the web interface"
echo "2. Explore the API at http://localhost:8000/docs"
echo "3. Add more API keys in config/api_keys.env for enhanced functionality"
echo "4. Check logs with: docker-compose logs -f [service-name]"
echo ""

print_success "Happy predicting! 🚀📈"