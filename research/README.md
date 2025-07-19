# S&P 500 Earnings Research System

A comprehensive research system to collect and analyze historical earnings data for all S&P 500 companies using NASDAQ earnings pages.

## Project Overview

This system automatically scrapes earnings data from NASDAQ.com for all companies in the S&P 500 index, collecting 20+ data points per earnings report including:

- **Earnings Performance**: EPS estimates vs. actual, beat/miss status
- **Stock Metrics**: Price movements, volume, market cap
- **Technical Indicators**: Moving averages, 52-week highs/lows
- **Financial Data**: Dividend yield, short interest, ex-dividend dates

## Features

- ✅ **Robust Web Scraping**: NASDAQ earnings data extraction with retry logic
- ✅ **Rate Limiting**: Respects server resources with configurable delays
- ✅ **Error Handling**: Comprehensive error classification and recovery
- ✅ **Data Validation**: Structured JSON schema with type checking
- ✅ **Batch Processing**: Process all 503 S&P 500 companies automatically
- ✅ **Resume Support**: Skip already processed companies
- ✅ **Comprehensive Testing**: Unit tests for all major components

## Installation

1. **Install Dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Verify Setup**:
   ```bash
   uv run python earnings_schema.py
   ```

## Usage

### Quick Start

```bash
# Test with a single company
uv run python nasdaq_scraper.py

# Process first 5 companies (testing)
uv run python batch_runner.py --limit 5

# Process all S&P 500 companies
uv run python batch_runner.py
```

### Command Line Options

```bash
# Basic batch processing
uv run python batch_runner.py [OPTIONS]

Options:
  --limit N               Process only first N companies
  --output-dir DIR        Output directory for JSON files (default: earnings_data)
  --log-level LEVEL       Logging level (DEBUG, INFO, WARNING, ERROR)
  --dry-run              Show status without processing
  --resume               Skip existing files (default behavior)
  --force                Reprocess existing files

Examples:
  uv run python batch_runner.py --limit 10 --log-level DEBUG
  uv run python batch_runner.py --dry-run
  uv run python batch_runner.py --force --limit 50
```

### Individual Components

**Data Schema Testing**:
```bash
uv run python earnings_schema.py
```

**Scraper Testing**:
```bash
uv run python nasdaq_scraper.py
```

**Data Processing**:
```bash
uv run python data_processor.py
```

## Data Structure

Each company generates a JSON file with this structure:

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Information Technology",
  "sub_sector": "Technology Hardware, Storage & Peripherals",
  "historical_reports": [
    {
      "date": "2024-01-24",
      "market_cap": 3400000000000.0,
      "close_price": 225.37,
      "next_open_price": 227.53,
      "price_change_percent": 0.96,
      "beat_or_miss": "beat",
      "estimated_eps": 1.60,
      "reported_eps": 1.64,
      "volume_earnings_day": 50724800,
      "volume_next_day": 23486200,
      "moving_avg_200": 195.42,
      "moving_avg_50": 220.15,
      "week_52_high": 237.23,
      "week_52_low": 164.08,
      "short_interest_percent": 0.65,
      "dividend_yield": 0.44,
      "ex_dividend_date": "2024-02-11",
      "is_historical": true
    }
  ],
  "projected_reports": [...],
  "last_updated": "2025-07-17T...",
  "data_source": "nasdaq.com"
}
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_earnings_schema.py -v
uv run pytest tests/test_data_processor.py -v
uv run pytest tests/test_error_handler.py -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html
```

## Configuration

### Rate Limiting

The scraper includes built-in rate limiting:
- **Default**: 30 requests per minute
- **Minimum delay**: 2 seconds between requests
- **Backoff**: Exponential backoff on failures
- **Server respect**: Honors 429 rate limit responses

### Error Handling

- **Network errors**: Automatic retry with exponential backoff
- **Parsing errors**: Graceful degradation with logging
- **File errors**: Clear error messages and recovery
- **Circuit breaker**: Stops processing on consecutive failures

## Output

Processed data is saved to `earnings_data/` directory:
```
earnings_data/
├── AAPL.json
├── MSFT.json
├── GOOGL.json
└── ...
```

Each file contains complete earnings history and projected reports for one company.

## Monitoring

### Logging

All operations are logged to:
- **Console**: Real-time progress updates
- **File**: `earnings_research.log` for detailed history

### Progress Tracking

```bash
# Check processing status
uv run python -c "
from data_processor import EarningsDataProcessor
processor = EarningsDataProcessor()
print(processor.get_processing_status())
"
```

## Architecture

```
├── earnings_schema.py      # Data structures and validation
├── nasdaq_scraper.py       # Web scraping with rate limiting
├── data_processor.py       # Data transformation and file I/O
├── batch_runner.py         # Main batch processing script
├── error_handler.py        # Comprehensive error handling
├── requirements.txt        # Python dependencies
├── tests/                  # Unit tests
│   ├── test_earnings_schema.py
│   ├── test_data_processor.py
│   └── test_error_handler.py
└── earnings_data/          # Output JSON files (created)
```

## Performance

- **Processing Speed**: ~2 companies per minute (rate limited)
- **Total Runtime**: ~4-5 hours for all 503 companies
- **Memory Usage**: <100MB during processing
- **Disk Usage**: ~50MB for all company data files

## Troubleshooting

### Common Issues

1. **Rate Limiting**: Increase delays in `ScrapingConfig`
2. **Network Errors**: Check internet connection and NASDAQ availability
3. **Parsing Errors**: Some companies may have non-standard page formats
4. **File Permissions**: Ensure write access to output directory

### Error Recovery

The system automatically handles:
- Network timeouts with retry logic
- Server rate limiting with backoff
- Malformed data with graceful degradation
- File I/O errors with clear messaging

### Debug Mode

```bash
uv run python batch_runner.py --log-level DEBUG --limit 1
```

## Contributing

This is a research tool following these principles:
- **Defensive**: Respect server resources with rate limiting
- **Robust**: Handle errors gracefully without crashing
- **Testable**: Comprehensive unit test coverage
- **Maintainable**: Clear code structure and documentation

## Legal Compliance

- **Rate Limiting**: Respects NASDAQ server resources
- **Public Data**: Only accesses publicly available earnings information
- **No Authentication**: Does not bypass any security measures
- **Educational Use**: Designed for research and analysis purposes
