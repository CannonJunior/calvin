# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a stock market prediction tool focused on predicting S&P 500 stock performance the day after earnings announcements. The system uses sentiment analysis, historical patterns, and machine learning to generate predictions based on earnings data, analyst reports, and market sentiment.

## Development Commands

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package-name>

# Run Python scripts
uv run <script.py>

# Run specific services
uv run finance_server.py
uv run sentiment_analysis_server.py
```

### Docker Services
```bash
# Start all services (includes web app + Ollama)
docker-compose up -d

# Start specific service
docker-compose up -d postgres ollama backend frontend

# View logs
docker-compose logs -f <service-name>

# Stop services
docker-compose down

# Pull and run Ollama models
docker-compose exec ollama ollama pull llama3.1:8b
docker-compose exec ollama ollama pull qwen2.5:7b
```

### Web Application
```bash
# Access web interface
http://localhost:3000

# API documentation
http://localhost:8000/docs

# Ollama API
http://localhost:11434
```

### Database Operations
```bash
# Connect to PostgreSQL with pgvector
docker-compose exec postgres psql -U postgres -d stockprediction

# Run migrations
uv run scripts/migrate.py

# Load S&P 500 data
uv run scripts/load_sp500_data.py
```

## Architecture

### Core Components

1. **Frontend Layer (React + TypeScript)**
   - **Dashboard**: Real-time earnings calendar with prediction confidence scores
   - **Company Profiles**: Historical performance charts, analyst accuracy tracking
   - **Prediction Interface**: Next-day performance predictions with AI-generated reasoning
   - **Agent Chat**: Natural language interface for querying historical patterns

2. **Backend Layer (FastAPI)**
   - **API Gateway**: RESTful endpoints and WebSocket for real-time updates
   - **Agent Orchestration**: Coordinates Ollama-powered AI agents
   - **MCP Integration**: Tavily, Polygon.io, Alpha Vantage, Yahoo Finance connectors
   - **Rate Limiting**: Respect free tier limits (Alpha Vantage: 500/day, Polygon: 5/min, Tavily: 1000/month)

3. **AI Agent Layer (Ollama)**
   - **Analysis Agent**: Deep dive into earnings patterns using local LLMs (Llama3.1, Qwen2.5)
   - **Research Agent**: Automated web scraping and sentiment analysis
   - **Prediction Agent**: Generate explanations for stock movement predictions
   - **Query Agent**: Natural language interface for historical data exploration

4. **Data Processing Services**
   - **Finance Server** (`finance_server.py`): Market data aggregation and analysis
   - **Sentiment Server** (`sentiment_analysis_server.py`): Text analysis of earnings reports, news, analyst notes
   - **Data Pipeline**: ETL processes for continuous data ingestion

5. **Storage Layer**
   - **PostgreSQL + pgvector**: Vector embeddings for RAG-based similarity search
   - **Assets Directory**: Permanent JSON files for S&P 500 company profiles
   - **Redis Cache**: API response caching to manage rate limits

6. **Prediction Engine**
   - **RAG System**: Historical pattern matching using vector similarity
   - **Feature Engineering**: Earnings surprise, sentiment delta, analyst accuracy tracking
   - **ML Pipeline**: Models trained on post-earnings stock performance

### Directory Structure

```
calvin/
├── assets/                    # Permanent data storage
│   ├── sp500_companies/      # Company profiles (.json files)
│   ├── earnings_data/        # Historical earnings data
│   ├── analyst_data/         # Analyst ratings and targets
│   └── insider_trading/      # Insider transaction data
├── frontend/                 # React + TypeScript web app
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Main application pages
│   │   ├── services/        # API clients
│   │   └── utils/           # Utility functions
│   ├── package.json
│   └── Dockerfile
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── agents/          # Agent orchestration
│   │   ├── models/          # Database models
│   │   └── services/        # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── agents/                   # Ollama AI agents
│   ├── analysis_agent.py    # Earnings pattern analysis
│   ├── research_agent.py    # Web scraping & sentiment
│   ├── prediction_agent.py  # Stock movement predictions
│   └── query_agent.py       # Natural language queries
├── services/                 # MCP and processing services
├── docker/                   # Docker configurations
├── config/                   # Configuration files
├── scripts/                  # Utility and migration scripts
├── docs/                     # Documentation
├── finance_server.py         # Existing finance MCP server
├── sentiment_analysis_server.py  # Existing sentiment MCP server
└── docker-compose.yml        # Service orchestration
```

## MCP Tool Integration

### Required MCP Servers

1. **Tavily Search** (`mcp-tavily`)
   - Web scraping for earnings reports, analyst notes, company news
   - 1,000 free credits/month
   - Use for targeted financial content searches

2. **Polygon.io** (`mcp_polygon`)
   - Real-time market data, historical prices, insider trading
   - 5 API calls/minute free tier
   - Use for high-quality market data

3. **Alpha Vantage** (`alpha-vantage-mcp`)
   - Company fundamentals, earnings calendar, analyst ratings
   - 500 calls/day free tier
   - Primary source for S&P 500 daily updates

4. **Yahoo Finance** (`yfinance-mcp`)
   - Backup data source, S&P 500 constituents
   - No formal limits but implement throttling
   - Use for bulk historical data collection

### Installation
```bash
# Clone and install MCP servers
git clone https://github.com/tavily-ai/tavily-mcp.git services/tavily-mcp
git clone https://github.com/polygon-io/mcp_polygon.git services/mcp_polygon
git clone https://github.com/berlinbra/alpha-vantage-mcp.git services/alpha-vantage-mcp
git clone https://github.com/narumiruna/yfinance-mcp.git services/yfinance-mcp
```

## Data Collection Strategy

### S&P 500 Company Bootstrap
1. Fetch complete S&P 500 list using Financial Modeling Prep API
2. Create company profile JSON files in `assets/sp500_companies/`
3. Collect historical earnings dates, dividend schedules, insider trading patterns
4. Gather analyst coverage and historical target price accuracy

### Daily Data Pipeline
1. **Pre-market** (6 AM ET): Update earnings calendar, scrape pre-market news
2. **Post-market** (6 PM ET): Collect earnings results, analyze sentiment of calls/releases
3. **Continuous**: Monitor analyst rating changes, insider trading filings

### Rate Limit Management
- **Alpha Vantage**: 500 calls/day → Schedule S&P 500 updates across 24 hours
- **Polygon.io**: 5 calls/minute → Queue requests with 12-second intervals
- **Tavily**: 1,000 credits/month → Reserve for earnings announcement searches
- **yfinance**: Implement 1-second delays between requests to avoid blocks

## Key Features to Implement

### Next-Day Earnings Performance Prediction
1. **Feature Engineering**:
   - Earnings surprise magnitude (actual vs. expected)
   - Sentiment delta (pre vs. post-earnings announcement)
   - Historical analyst accuracy for specific company
   - Market conditions context (VIX, sector performance)

2. **Historical Pattern Analysis**:
   - Post-earnings stock movements (+1 day performance)
   - Correlation with sentiment scores from earnings calls
   - Analyst accuracy tracking and weighting
   - Sector-relative performance adjustments

3. **RAG-based Similarity Search**:
   - Vector embeddings of earnings announcements and results
   - Find similar historical scenarios using pgvector
   - Weight predictions based on historical outcome patterns

## Web Application Features

### Earnings Calendar Dashboard
- **Upcoming Earnings**: S&P 500 companies with earnings dates in next 30 days
- **Prediction Confidence**: Color-coded indicators (high/medium/low confidence)
- **Historical Accuracy**: Track record of prediction model for each company
- **Market Sentiment**: Real-time sentiment indicators from news and analyst reports

### Company Deep Dive Pages
- **Historical Performance**: Charts showing post-earnings stock movements (+1 day)
- **Earnings History**: Beat/miss/meet expectations with sentiment analysis scores
- **Analyst Tracking**: Historical accuracy of analysts covering the stock
- **Insider Activity**: Recent insider trading patterns and correlation to performance
- **Sector Comparison**: Performance relative to sector after earnings announcements

### AI Agent Chat Interface
- **Natural Language Queries**: "How did AAPL perform after beating earnings in Q3 2023?"
- **Pattern Recognition**: "Find companies similar to MSFT's current earnings setup"
- **Prediction Explanations**: AI-generated reasoning for stock movement predictions
- **Historical Analysis**: Deep dive into patterns using Ollama-powered agents

### Prediction Results Dashboard
- **Next-Day Predictions**: Stock movement predictions for upcoming earnings
- **Confidence Intervals**: Uncertainty quantification and risk assessment
- **Similar Scenarios**: RAG-based historical pattern matching with explanations
- **Backtesting Performance**: Model accuracy over time with detailed metrics

## Ollama AI Agents

### Analysis Agent (Llama3.1:8b)
- **Earnings Pattern Analysis**: Deep dive into historical earnings patterns
- **Feature Engineering**: Extract predictive signals from earnings data
- **Correlation Analysis**: Identify relationships between sentiment and stock performance

### Research Agent (Qwen2.5:7b) 
- **Web Scraping**: Automated collection of earnings reports and analyst notes
- **Sentiment Analysis**: Analyze tone and sentiment of financial communications
- **News Aggregation**: Collect and summarize relevant news for each company

### Prediction Agent (Llama3.1:8b)
- **Stock Movement Predictions**: Generate next-day performance forecasts
- **Reasoning Generation**: Explain prediction logic in natural language
- **Risk Assessment**: Quantify prediction uncertainty and confidence levels

### Query Agent (Qwen2.5:7b)
- **Natural Language Interface**: Process user queries about historical data
- **Data Exploration**: Help users discover patterns and insights
- **Report Generation**: Create custom analysis reports based on user requests

## Environment Variables

```bash
# API Keys
POLYGON_API_KEY=your_polygon_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TAVILY_API_KEY=your_tavily_key
FINANCIAL_MODELING_PREP_API_KEY=your_fmp_key

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=stockprediction
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Cache & Services
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434

# Web Application
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Development Workflow

### Adding New Data Sources
1. Create MCP server in `services/` directory
2. Add configuration to `config/mcp_servers.json`
3. Update rate limiting logic in data collection scripts
4. Add tests for new data source integration

### Model Training Pipeline
1. Feature extraction from historical data
2. Vector embedding generation for RAG system
3. Model training with cross-validation on historical earnings
4. Backtesting on out-of-sample earnings announcements

## Important Notes

- **Append all new prompts to PROMPTS.md** - This helps track project evolution
- **Respect API rate limits** - Implement proper throttling and caching
- **Focus on earnings day prediction** - The core goal is next-day performance after earnings
- **Use MCP extensively** - Leverage existing tools rather than building from scratch
- **Vector similarity for historical patterns** - Use pgvector for finding similar earnings scenarios

## Development Workflow

### Setting Up Development Environment
```bash
# Clone and setup MCP servers
git clone https://github.com/tavily-ai/tavily-mcp.git services/tavily-mcp
git clone https://github.com/polygon-io/mcp_polygon.git services/mcp_polygon
git clone https://github.com/berlinbra/alpha-vantage-mcp.git services/alpha-vantage-mcp

# Start services
docker-compose up -d postgres redis ollama

# Pull Ollama models
docker-compose exec ollama ollama pull llama3.1:8b
docker-compose exec ollama ollama pull qwen2.5:7b

# Start backend and frontend
docker-compose up -d backend frontend
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
uv run alembic upgrade head
```

### Agent Development
```bash
# Test individual agents
uv run agents/analysis_agent.py
uv run agents/prediction_agent.py

# Test agent orchestration
uv run python -m agents.orchestrator
```

## Testing

```bash
# Run all tests
uv run pytest

# Test specific components
uv run pytest tests/test_finance_server.py
uv run pytest tests/test_sentiment_analysis.py
uv run pytest tests/test_agents.py

# Frontend tests
cd frontend && npm test

# Integration tests with rate limiting
uv run pytest tests/test_api_integration.py --slow

# Test Ollama agents
uv run pytest tests/test_ollama_agents.py
```

## Monitoring

- **API Usage Tracking**: Monitor daily API call counts against free tier limits
- **Data Quality**: Validate incoming data completeness and accuracy
- **Prediction Performance**: Track prediction accuracy against actual next-day returns
- **Service Health**: Monitor MCP server availability and response times