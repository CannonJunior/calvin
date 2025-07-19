# Earnings Data Curator

A comprehensive Python application that curates earnings data from NASDAQ.com and creates JSON files according to the earnings template schema defined in PLANNING.md.

## Features

✅ **Multiple Input Options**:
- Single symbol curation
- Multiple symbols from command line
- Batch processing of all S&P 500 companies  
- Symbols from file

✅ **Complete Data Collection**:
- Historical earnings reports
- Projected earnings reports
- Company fundamentals
- Technical indicators
- Market data

✅ **Template Compliance**:
- Matches exact schema from PLANNING.md
- All required fields present
- Proper data types and formatting

## Installation

```bash
# Install dependencies
uv pip install -r requirements.txt

# Or with regular pip
pip install -r requirements.txt
```

## Usage

### Command Line Interface

```bash
# Curate single symbol
python earnings_curator.py --symbol AAPL

# Curate multiple symbols
python earnings_curator.py --symbols AAPL,MSFT,GOOGL

# Curate all S&P 500 companies
python earnings_curator.py --batch-sp500

# Curate from file (one symbol per line)
python earnings_curator.py --symbols-file my_symbols.txt

# Limit number of symbols (useful for testing)
python earnings_curator.py --batch-sp500 --limit 10

# Specify output directory
python earnings_curator.py --symbol AAPL --output-dir my_earnings_data

# Enable verbose logging
python earnings_curator.py --symbol AAPL --verbose
```

### Alternative Runner

```bash
# Use the simple runner script
python run_curator.py --symbol AAPL
```

## Output Format

The application creates JSON files that match the earnings template schema:

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Information Technology", 
  "sub_sector": "Technology Hardware",
  "historical_reports": [
    {
      "symbol": "AAPL",
      "earnings_date": "2024-07-18",
      "quarter": 3,
      "year": 2024,
      "actual_eps": 1.73,
      "estimated_eps": 1.76,
      "beat_miss_meet": "MISS",
      "surprise_percent": -1.7,
      "revenue_billions": 146.29,
      "revenue_growth_percent": 7.3,
      // ... all other fields ...
    }
  ],
  "projected_reports": [
    {
      "symbol": "AAPL", 
      "earnings_date": "2025-08-17",
      "actual_eps": null,
      "estimated_eps": 2.56,
      "beat_miss_meet": "PROJECTED",
      // ... all other fields ...
    }
  ],
  "last_updated": "2025-07-19T12:00:00.000000",
  "data_source": "nasdaq.com"
}
```

## Data Sources

- **Primary**: NASDAQ.com earnings pages
- **Secondary**: Yahoo Finance (yfinance) for additional market data
- **Company Info**: S&P 500 companies list

## File Structure

```
earnings_curator.py          # Main application
earnings_data_models.py      # Data structures matching template
nasdaq_data_scraper.py       # NASDAQ web scraper  
sp500_processor.py          # S&P 500 company data handler
run_curator.py              # Simple runner script
tests/                      # Comprehensive test suite
  test_earnings_curator.py  # Main test file
requirements.txt            # Dependencies
```

## Examples

### Single Symbol
```bash
python earnings_curator.py --symbol AAPL
```
Output: `curated_earnings/AAPL.json`

### Multiple Symbols
```bash  
python earnings_curator.py --symbols AAPL,MSFT,GOOGL
```
Output: 
- `curated_earnings/AAPL.json`
- `curated_earnings/MSFT.json` 
- `curated_earnings/GOOGL.json`

### Batch S&P 500 (Limited)
```bash
python earnings_curator.py --batch-sp500 --limit 50
```
Output: 50 JSON files in `curated_earnings/` directory

### From File
Create `symbols.txt`:
```
AAPL
MSFT
GOOGL
AMZN
TSLA
```

Run:
```bash
python earnings_curator.py --symbols-file symbols.txt
```

## Testing

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run with coverage
uv run python -m pytest tests/ --cov=. --cov-report=html

# Run specific test file
uv run python -m pytest tests/test_earnings_curator.py -v
```

## Output Files

### Earnings Data Files
- Location: `curated_earnings/` (or specified directory)
- Format: `{SYMBOL}.json`
- Content: Complete earnings data matching template schema

### Summary Report
- File: `curated_earnings/curation_summary.json`
- Contains: Processing statistics, success rates, failed symbols

### Log File
- File: `earnings_curator.log`
- Contains: Detailed processing logs with timestamps

## Error Handling

- Network failures are handled gracefully
- Failed symbols are logged and reported
- Progress is saved and can be resumed
- Rate limiting prevents overwhelming servers

## Rate Limiting

- 2-second delay between requests to NASDAQ
- 1-second delay for yfinance requests
- Configurable in scraper classes

## Dependencies

- `requests`: HTTP requests to NASDAQ
- `beautifulsoup4`: HTML parsing
- `yfinance`: Additional market data
- `pandas`: Data manipulation
- `python-dotenv`: Environment variables
- `pytest`: Testing framework

## Troubleshooting

### No S&P 500 File
If `sp500_companies.json` doesn't exist, the application will create a sample file with major companies.

### Network Issues
The application includes retry logic and graceful error handling for network issues.

### Missing Data
Missing fields are handled gracefully with appropriate defaults or null values.

### Rate Limiting
If you encounter rate limiting, increase the delay in the scraper configuration.

## Configuration

### Environment Variables
Create `.env` file:
```
NASDAQ_DELAY=2
YFINANCE_DELAY=1
LOG_LEVEL=INFO
```

### Custom S&P 500 File
Place your own `sp500_companies.json` in the project directory with the required schema.

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure template schema compliance

## License

MIT License - see LICENSE file for details.