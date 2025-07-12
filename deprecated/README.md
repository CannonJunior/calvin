# Calvin Stock Prediction Tool

An AI-powered stock prediction system focused on predicting next-day performance after earnings announcements using MCP (Model Context Protocol) servers and Ollama AI agents.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for NPX installation)
- pip (Python package manager)
- Ollama (optional, for AI features)

### Installation & Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd calvin
   ```

2. **Install and run using NPX:**
   ```bash
   npx calvin-stock-prediction-tool
   ```

3. **Or install dependencies manually:**
   ```bash
   pip install -r requirements.txt
   python main_client.py
   ```

4. **Access the web interface:**
   Open http://localhost:3000 in your browser

## 🏗️ Architecture Overview

The system uses a **proper MCP (Model Context Protocol) architecture** with FastMCP Client pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Main Client (Port 3000)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Web Interface │  │   AI Agent      │  │   API Gateway   │ │
│  │                 │  │   (Ollama)      │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           CalvinMCPClient (FastMCP Client)                  │ │
│  │    Uses mcpServers config to launch and manage servers     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   MCP Servers Config   │
                    └───────────────────────┘
         ┌─────────────┬─────────────┬─────────────┐
         │             │             │             │
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │Company  │  │Earnings │  │Prediction│  │Finance  │
    │Server   │  │Server   │  │Server   │  │Server   │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
         │
    ┌─────────┐
    │Sentiment│
    │Server   │
    └─────────┘
```

## 📦 MCP Servers

The system uses **proper MCP pattern** with FastMCP Client managing server processes through `mcpServers` configuration:

### 1. Company Server
- **Purpose:** S&P 500 company data management
- **Tools:** `get_companies`, `get_company_by_symbol`, `search_companies`, `add_company`
- **Resources:** `companies://list`, `companies://sectors`
- **Launch:** Managed by CalvinMCPClient via python server.py

### 2. Earnings Server
- **Purpose:** Earnings analysis and calendar management
- **Tools:** `get_earnings_calendar`, `analyze_earnings_surprise`, `find_similar_earnings_patterns`
- **Resources:** `earnings://calendar`, `earnings://recent`
- **Launch:** Managed by CalvinMCPClient via python server.py

### 3. Prediction Server
- **Purpose:** Next-day stock performance predictions
- **Tools:** `predict_next_day_performance`, `get_top_predictions`, `analyze_prediction_accuracy`
- **Resources:** `predictions://recent`, `predictions://summary`
- **Launch:** Managed by CalvinMCPClient via python server.py

### 4. Finance Server
- **Purpose:** Market data and stock information
- **Tools:** `get_stock_price`, `get_market_data`, `get_company_info`, `get_market_indices`
- **Resources:** `finance://market-status`, `finance://sp500`
- **Launch:** Managed by CalvinMCPClient via python server.py

### 5. Sentiment Server
- **Purpose:** Financial text sentiment analysis
- **Tools:** `analyze_sentiment`, `analyze_earnings_sentiment`, `batch_sentiment_analysis`
- **Resources:** `sentiment://financial-keywords`
- **Launch:** Managed by CalvinMCPClient via python server.py

## 🤖 AI Agent Integration

The system includes an **Ollama-powered AI agent** that provides:

- **Stock Analysis:** AI-powered insights on market data
- **Chat Interface:** Natural language interaction for queries
- **Prediction Explanations:** Human-readable reasoning for predictions
- **Market Context:** Intelligent interpretation of financial data

### AI Features
- Real-time chat interface via WebSocket
- Automated stock analysis with context
- Pattern recognition and historical comparisons
- Natural language explanations of predictions

## 🌐 Web Interface

The simplified web interface provides:

- **Server Status Dashboard:** Real-time monitoring of all MCP servers
- **Stock Analysis:** Enter symbols for comprehensive analysis
- **Earnings Predictions:** Get next-day performance predictions
- **Company Search:** Find S&P 500 companies by name or symbol
- **AI Chat:** Interactive chat with the AI assistant

## 🔧 Development

### Running Individual MCP Servers

```bash
# Company Server
cd packages/mcp-company-server
python server.py

# Earnings Server
cd packages/mcp-earnings-server
python server.py

# And so on...
```

### API Documentation

Once running, visit `http://localhost:3000/docs` for interactive API documentation.

### Key API Endpoints

- `GET /api/health` - System health check
- `GET /api/servers` - MCP server status
- `POST /api/tools/{server}/{tool}` - Call MCP server tools
- `GET /api/resources/{server}/{resource}` - Get MCP server resources
- `POST /api/ai/analyze` - AI stock analysis
- `POST /api/ai/chat` - Chat with AI agent
- `WS /ws` - WebSocket for real-time updates

## 📊 Data Storage

The system uses **file-based storage** for simplicity:

```
assets/
├── sp500_companies/     # Company profiles (JSON)
├── earnings_data/       # Historical earnings data
├── predictions/         # Prediction history
└── insider_trading/     # Insider trading data
```

## 🎯 Core Features

### Stock Prediction Pipeline
1. **Data Collection:** Real-time market data via yfinance
2. **Sentiment Analysis:** Financial text analysis with TextBlob
3. **Pattern Matching:** Historical earnings pattern recognition
4. **AI Analysis:** Ollama-powered intelligent insights
5. **Prediction Generation:** Next-day performance forecasts
6. **Accuracy Tracking:** Historical prediction performance

### Earnings Focus
- **Earnings Calendar:** Track upcoming S&P 500 earnings
- **Surprise Analysis:** Beat/miss/meet categorization
- **Historical Patterns:** Find similar earnings scenarios
- **Sentiment Tracking:** Pre/post earnings sentiment analysis

## 📈 Usage Examples

### Analyze a Stock
```bash
curl -X POST http://localhost:3000/api/tools/finance/get_stock_price \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

### Get Earnings Calendar
```bash
curl -X POST http://localhost:3000/api/tools/earnings/get_earnings_calendar -H "Content-Type: application/json" -d '{"limit": 10}'
```

### AI Stock Analysis
```bash
curl -X POST http://localhost:3000/api/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "market_data": {"price": 150, "change": 2.5}}'
```

## 🛠️ Configuration

### Environment Variables
```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# MCP Server Ports (optional)
MCP_COMPANY_PORT=8001
MCP_EARNINGS_PORT=8002
MCP_PREDICTION_PORT=8003
MCP_FINANCE_PORT=8004
MCP_SENTIMENT_PORT=8005
```

### Ollama Setup (Optional)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models
ollama pull llama3.1:8b
ollama pull qwen2.5:7b

# Start Ollama
ollama serve
```

## 🔍 Monitoring

### Health Checks
- Main client: `http://localhost:3000/api/health`
- Individual servers: `http://localhost:800X/health`

### Logs
- All services log to stdout
- WebSocket connections for real-time updates
- Server status monitoring in web interface

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Test specific server
python -m pytest tests/test_company_server.py

# Test AI integration
python -m pytest tests/test_ai_agent.py
```

## 🚨 Troubleshooting

### Common Issues

1. **MCP Server Won't Start**
   - Check port availability: `lsof -i :8001`
   - Verify Python dependencies: `pip list`

2. **AI Features Not Working**
   - Ensure Ollama is running: `curl http://localhost:11434/api/tags`
   - Check available models: `ollama list`

3. **Web Interface Connection Issues**
   - Verify main client is running on port 3000
   - Check WebSocket connection in browser console

### Debug Mode
```bash
# Run with debug logging
python main_client.py --log-level debug
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🔮 Future Enhancements

- **Real-time Data:** WebSocket feeds for live market data
- **Advanced ML:** Deep learning models for prediction accuracy
- **Portfolio Management:** Track and analyze multiple positions
- **Risk Management:** Volatility analysis and risk scoring
- **Mobile App:** React Native mobile interface
- **API Integration:** Additional data sources (Alpha Vantage, Polygon.io)

---

**Built with ❤️ using FastMCP, Ollama, and modern web technologies**
