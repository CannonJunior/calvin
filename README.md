# S&P 500 Earnings Analysis Dashboard

An interactive web dashboard for analyzing S&P 500 earnings data with real-time market information, AI-powered chat, and portfolio management features.

## Quick Start

```bash
# Start the dashboard (recommended method)
./start_dashboard.sh

# Or manually start services
python3 sp500_api.py &        # S&P 500 data API
python3 -m http.server 8080   # Web server
```

**Access Dashboard**: http://localhost:8080/earnings_dashboard.html

## Features

- =� **Interactive Timeline**: Animated earnings events with hover tooltips
- <� **Real Market Data**: Live prices, market caps, and earnings forecasts  
- > **AI Chat**: Ollama-powered financial analysis (optional)
- =� **Portfolio Tracking**: Sector-based investment management
- = **Dynamic Filtering**: Multiple y-axis modes and data views
- � **Smooth Animations**: D3.js transitions between data modes

## Current Data Status

### Earnings Icons Available
The dashboard currently has curated earnings data for **7 companies**:
- **ABBV** - AbbVie Inc.
- **ABT** - Abbott Laboratories  
- **ACN** - Accenture plc
- **ADBE** - Adobe Inc.
- **AMD** - Advanced Micro Devices
- **AOS** - A. O. Smith Corporation
- **MMM** - 3M Company

### S&P 500 Company Data
- ** Complete**: All 503 S&P 500 companies loaded from Wikipedia
- ** Sectors**: 11 GICS sectors with real allocation data
- ** Real-time**: Market data via external APIs (Alpha Vantage, Finnhub, FMP)

## Prerequisites

### Required
- **Python 3.8+** with standard libraries
- **Internet connection** for real-time market data

### Optional (Enhanced Features)
- **Ollama** running on localhost:11434 (for AI chat)
- **Docker** (for full PostgreSQL setup)
- **API Keys** for enhanced market data:
  - [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
  - [Finnhub](https://finnhub.io/register)  
  - [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs)

## Installation & Setup

### 1. Clone & Navigate
```bash
git clone <repository-url>
cd calvin
```

### 2. Install Dependencies
```bash
# Basic Python setup (built-in modules only)
python3 -c "import json, requests, psycopg2" 2>/dev/null || echo "Install: pip3 install requests psycopg2-binary"
```

### 3. Configuration (Optional)
```bash
# API keys for enhanced data (will auto-create config.json)
cp config.example.json config.json
# Edit config.json with your API keys
```

### 4. Start Dashboard
```bash
./start_dashboard.sh
```

## Architecture

### Core Services
- **S&P 500 API** (port 5001): Company data, sectors, symbols
- **Web Server** (port 8080): Serves dashboard and static files
- **Earnings Data**: Local JSON files in `earnings-icons/` directory

### Data Flow
1. **Company Data**: Wikipedia � sp500_companies.json � S&P 500 API
2. **Earnings Data**: earnings-icons/*.json � Dashboard (automatic fallback)
3. **Market Data**: External APIs � Real-time dashboard updates
4. **AI Chat**: Local Ollama � Natural language financial queries

### Fallback Strategy
-  **No PostgreSQL needed**: Uses local earnings-icons files
-  **No API keys**: Works with demo/cached data
-  **No Ollama**: Chat disabled gracefully
-  **Network issues**: Cached data and mock fallbacks

## Usage Guide

### Dashboard Navigation
1. **Timeline View**: Hover over earnings icons for details
2. **Y-Axis Modes**: Switch between confidence, price change, surprise %, etc.
3. **Filtering**: Use controls to focus on specific time periods or sectors
4. **Portfolio**: Add companies to track performance by sector

### Y-Axis Positioning Modes
- **Confidence**: Future earnings confidence scores vs. past price changes
- **Price Change**: Stock price movement around earnings dates
- **Surprise %**: How much actual earnings beat/missed estimates  
- **EPS Growth**: Earnings per share growth rates
- **Market Cap**: Company size positioning

### AI Chat Commands (if Ollama enabled)
- "Analyze earnings trends for tech sector"
- "What companies have earnings this week?"
- "Compare AAPL vs MSFT earnings performance"
- "Explain the confidence scoring methodology"

## Data Sources & Curation

### Earnings Icons Creation
To add more companies to the earnings-icons dataset:

```bash
# Curate a single company (requires PostgreSQL setup)
python3 simple_curate_stock.py AAPL

# Full S&P 500 curation (advanced users)
# See sp500_curation_progress.md for current status
```

**Note**: Most curation attempts failed due to API rate limits and data availability. The current 7 companies represent successful curations with complete earnings data.

### Adding Your Own Data
Create JSON files in `earnings-icons/` directory:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "earnings_data": [
    {
      "symbol": "AAPL",
      "earnings_date": "2025-10-30",
      "estimated_eps": 1.25,
      "confidence_score": 0.85,
      "consensus_rating": "Buy",
      "announcement_time": "AMC"
    }
  ]
}
```

## Troubleshooting

### Dashboard Shows No Earnings Icons
- **Check**: earnings-icons/ directory has JSON files
- **Verify**: S&P 500 API running on port 5001
- **Console**: Browser dev tools for JavaScript errors

### AI Chat Not Working  
```bash
# Start Ollama
ollama serve

# Install a model
ollama pull llama2
```

### API Rate Limits
- Use demo keys for testing
- Add delays between requests  
- Consider premium API plans for production

### Performance Issues
- Reduce icon count in timeline view
- Disable real-time updates temporarily
- Clear browser cache and reload

## Development

### File Structure
```
calvin/
   earnings_dashboard.html     # Main dashboard interface
   earnings-icons/            # Curated earnings data (JSON)
   sp500_companies.json       # S&P 500 company database  
   sp500_api.py              # Company data API server
   simple_curate_stock.py    # Earnings data curation tool
   start_dashboard.sh        # Unified startup script
   config.json              # API keys and configuration
```

### API Endpoints
- `GET /api/companies` - All S&P 500 companies
- `GET /api/symbols` - Company symbols list
- `GET /api/sectors` - Sector breakdown
- `GET /api/health` - Service status

## Contributing

1. **Fork** the repository
2. **Add features** or fix bugs
3. **Test** with existing earnings data
4. **Submit** pull request with clear description

### Priority Areas
- [ ] Expand earnings-icons dataset (currently 7/503 companies)
- [ ] Improve curation success rate
- [ ] Add more data sources for earnings
- [ ] Enhanced portfolio management features
- [ ] Better mobile responsiveness

## License

MIT License - See LICENSE file for details.

## Support

- **Issues**: Report bugs via GitHub issues
- **Questions**: Use discussions for usage questions  
- **Data**: Current earnings coverage is limited (7 companies)
- **Performance**: Best with modern browsers and good internet connection

---

**Current Status**: Basic functionality working with limited earnings dataset. Full S&P 500 earnings curation remains a work-in-progress due to API limitations and data availability challenges.