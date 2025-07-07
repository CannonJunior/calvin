# Calvin Stock Prediction Tool

AI-powered stock market prediction tool for S&P 500 earnings analysis using Ollama, MCP, and vector embeddings.

## Features

- **AI-Powered Analysis**: Ollama agents for deep earnings pattern analysis
- **Real-time Predictions**: Next-day stock performance predictions after earnings
- **Interactive Dashboard**: React frontend with earnings calendar and prediction results
- **Vector Search**: RAG-based historical pattern matching using pgvector
- **MCP Integration**: Multiple Model Context Protocol servers for data collection
- **Comprehensive Analytics**: Sector performance, analyst accuracy, insider trading analysis

## Architecture

### Core Components

- **Frontend**: React + TypeScript with Tailwind CSS
- **Backend**: FastAPI with async database operations
- **AI Agents**: Ollama-powered agents (Llama3.1, Qwen2.5)
- **Database**: PostgreSQL with pgvector for embeddings
- **Cache**: Redis for API response caching
- **Data Pipeline**: MCP-based financial data collection

### Directory Structure

```
calvin/
├── frontend/                 # React + TypeScript web app
├── backend/                  # FastAPI application
├── agents/                   # Ollama AI agents
├── assets/                   # Permanent data storage
├── services/                 # MCP servers
├── docker/                   # Docker configurations
├── scripts/                  # Utility scripts
└── docker-compose.yml        # Service orchestration
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)
- uv (Python package manager)

### 1. API Keys Setup

```bash
# Copy API keys template
cp config/api_keys.env.example config/api_keys.env

# Edit config/api_keys.env with your actual API keys
# Get free API keys from:
# - Polygon.io: https://polygon.io/ (5 calls/minute free)
# - Alpha Vantage: https://www.alphavantage.co/ (500 calls/day free)
# - Tavily: https://tavily.com/ (1,000 credits/month free)
# - Financial Modeling Prep: https://financialmodelingprep.com/ (250 requests free)

# Export API keys to environment
source config/export_api_keys.sh
```

### 2. Automated Setup (Recommended)

```bash
# Run complete system initialization
./scripts/init_system.sh

# This script will:
# - Check prerequisites
# - Setup API keys
# - Build and start all services
# - Download AI models
# - Load S&P 500 data
# - Verify system health
```

### 3. Manual Setup (Alternative)

```bash
# Export API keys
source config/export_api_keys.sh

# Start all services
docker-compose up -d

# Initialize Ollama models
docker-compose exec ollama ollama pull llama3.1:8b
docker-compose exec ollama ollama pull qwen2.5:7b

# Load S&P 500 data
docker-compose exec backend uv run scripts/load_sp500_data.py
```

### 4. Access Applications

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

## Development

### Backend Development

```bash
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
uv run alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Agent Development

```bash
# Test individual agents
uv run agents/analysis_agent.py
uv run agents/prediction_agent.py

# Test agent orchestration
uv run python -m agents.orchestrator
```

## API Usage

### Get Earnings Calendar

```bash
curl "http://localhost:8000/api/v1/earnings/calendar?start_date=2024-01-01&end_date=2024-01-31"
```

### Generate Prediction

```bash
curl -X POST "http://localhost:8000/api/v1/predictions/AAPL/generate" \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2024-02-01"}'
```

### Query AI Agents

```bash
curl -X POST "http://localhost:8000/api/v1/agents/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze AAPL earnings patterns",
    "agent_type": "analysis"
  }'
```

## Data Sources

### Supported APIs

- **Alpha Vantage**: 500 calls/day (free tier)
- **Polygon.io**: 5 calls/minute (free tier)
- **Yahoo Finance**: No formal limits (unofficial)
- **Tavily**: 1,000 credits/month (free tier)

### Data Pipeline

1. **S&P 500 Company Bootstrap**: Fetch complete company list and fundamentals
2. **Daily Data Collection**: Earnings calendar, news sentiment, analyst updates
3. **Historical Analysis**: Pattern recognition and backtesting
4. **Prediction Generation**: ML models with AI-generated explanations

## AI Agents

### Analysis Agent (Llama3.1:8b)
- Earnings pattern analysis
- Statistical correlation analysis
- Historical performance evaluation

### Research Agent (Qwen2.5:7b)
- News sentiment analysis
- Earnings call transcript analysis
- Market intelligence gathering

### Prediction Agent (Llama3.1:8b)
- Stock movement predictions
- Confidence assessment
- Risk factor analysis

### Query Agent (Qwen2.5:7b)
- Natural language data queries
- Similar scenario identification
- Historical pattern explanation

## Web Interface Features

### Dashboard
- Upcoming earnings calendar with predictions
- Market sentiment overview
- High-confidence prediction highlights
- S&P 500 performance statistics

### Company Profiles
- Historical earnings performance
- Beat/miss/meet tracking
- Analyst accuracy analysis
- Insider trading patterns

### Agent Chat
- Natural language queries: "How did AAPL perform after beating earnings in Q3 2023?"
- Pattern recognition: "Find companies similar to MSFT's current setup"
- AI-generated prediction explanations

### Analytics
- Sector performance comparison
- Volatility analysis around earnings
- Backtesting results
- Prediction model accuracy tracking

## Configuration

### Rate Limiting

```yaml
# Free tier limits
ALPHA_VANTAGE_DAILY_LIMIT: 500
POLYGON_MINUTE_LIMIT: 5
TAVILY_MONTHLY_LIMIT: 1000

# Strategies
- Alpha Vantage: Spread 500 calls across 24 hours
- Polygon.io: Queue requests with 12-second intervals
- Tavily: Reserve for targeted earnings searches
```

### Vector Embeddings

```sql
-- pgvector configuration
CREATE INDEX earnings_embeddings_hnsw_idx ON earnings_embeddings 
USING hnsw (combined_embedding vector_cosine_ops);

-- Similarity search
SELECT * FROM find_similar_earnings(target_embedding, 0.8, 10);
```

## Testing

```bash
# Run all tests
uv run pytest

# Test specific components
uv run pytest tests/test_agents.py
uv run pytest tests/test_api_integration.py

# Frontend tests
cd frontend && npm test

# Integration tests with rate limiting
uv run pytest tests/test_api_integration.py --slow
```

## Deployment

### Production Considerations

1. **API Keys**: Store in secure secret management
2. **Rate Limiting**: Implement proper throttling and caching
3. **Monitoring**: Track API usage against free tier limits
4. **Scaling**: Use Kubernetes for multi-instance deployment
5. **Data Persistence**: Regular database backups
6. **Security**: HTTPS, authentication, input validation

### Docker Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with restart policies
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

- **API Usage**: Daily call counts against free tier limits
- **Data Quality**: Validation of incoming data completeness
- **Prediction Performance**: Track accuracy against actual returns
- **Service Health**: Monitor agent availability and response times

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE.md for details

## Support

- **Issues**: GitHub Issues
- **Documentation**: /docs directory
- **API Reference**: http://localhost:8000/docs

---

🤖 **Calvin** - AI-powered stock prediction for the modern investor