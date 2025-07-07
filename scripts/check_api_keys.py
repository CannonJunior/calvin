#!/usr/bin/env python3
"""
API Key Validation Script for Calvin Stock Prediction Tool
This script validates API keys and tests their functionality
"""

import os
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime
import requests

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="INFO"):
    color = Colors.BLUE
    if status == "SUCCESS":
        color = Colors.GREEN
    elif status == "ERROR":
        color = Colors.RED
    elif status == "WARNING":
        color = Colors.YELLOW
    
    print(f"{color}[{status}]{Colors.ENDC} {message}")

async def test_polygon_api(api_key: str) -> bool:
    """Test Polygon.io API"""
    if not api_key or api_key == "your_polygon_api_key_here":
        print_status("Polygon API key not configured", "WARNING")
        return False
    
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-01/2023-01-02"
        params = {"apikey": api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "OK":
                        print_status("Polygon API: Valid key, API working", "SUCCESS")
                        return True
                elif response.status == 401:
                    print_status("Polygon API: Invalid API key", "ERROR")
                elif response.status == 429:
                    print_status("Polygon API: Rate limit exceeded", "WARNING")
                else:
                    print_status(f"Polygon API: Unexpected status {response.status}", "WARNING")
    except Exception as e:
        print_status(f"Polygon API: Connection error - {e}", "ERROR")
    
    return False

async def test_alpha_vantage_api(api_key: str) -> bool:
    """Test Alpha Vantage API"""
    if not api_key or api_key == "your_alpha_vantage_api_key_here":
        print_status("Alpha Vantage API key not configured", "WARNING")
        return False
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": "AAPL",
            "apikey": api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "Global Quote" in data:
                        print_status("Alpha Vantage API: Valid key, API working", "SUCCESS")
                        return True
                    elif "Error Message" in data:
                        print_status(f"Alpha Vantage API: {data['Error Message']}", "ERROR")
                    elif "Note" in data:
                        print_status("Alpha Vantage API: Rate limit exceeded", "WARNING")
                    else:
                        print_status("Alpha Vantage API: Unexpected response format", "WARNING")
                else:
                    print_status(f"Alpha Vantage API: HTTP status {response.status}", "ERROR")
    except Exception as e:
        print_status(f"Alpha Vantage API: Connection error - {e}", "ERROR")
    
    return False

async def test_tavily_api(api_key: str) -> bool:
    """Test Tavily API"""
    if not api_key or api_key == "your_tavily_api_key_here":
        print_status("Tavily API key not configured", "WARNING")
        return False
    
    try:
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": api_key,
            "query": "Apple stock earnings",
            "max_results": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "results" in data:
                        print_status("Tavily API: Valid key, API working", "SUCCESS")
                        return True
                elif response.status == 401:
                    print_status("Tavily API: Invalid API key", "ERROR")
                elif response.status == 429:
                    print_status("Tavily API: Rate limit exceeded", "WARNING")
                else:
                    print_status(f"Tavily API: HTTP status {response.status}", "WARNING")
    except Exception as e:
        print_status(f"Tavily API: Connection error - {e}", "ERROR")
    
    return False

async def test_fmp_api(api_key: str) -> bool:
    """Test Financial Modeling Prep API"""
    if not api_key or api_key == "your_fmp_api_key_here":
        print_status("Financial Modeling Prep API key not configured", "WARNING")
        return False
    
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/AAPL"
        params = {"apikey": api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0 and "symbol" in data[0]:
                        print_status("Financial Modeling Prep API: Valid key, API working", "SUCCESS")
                        return True
                    elif isinstance(data, dict) and "Error Message" in data:
                        print_status(f"FMP API: {data['Error Message']}", "ERROR")
                elif response.status == 401:
                    print_status("Financial Modeling Prep API: Invalid API key", "ERROR")
                elif response.status == 429:
                    print_status("Financial Modeling Prep API: Rate limit exceeded", "WARNING")
                else:
                    print_status(f"Financial Modeling Prep API: HTTP status {response.status}", "WARNING")
    except Exception as e:
        print_status(f"Financial Modeling Prep API: Connection error - {e}", "ERROR")
    
    return False

def test_yfinance() -> bool:
    """Test yfinance (no API key required)"""
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if info and "symbol" in info:
            print_status("yfinance: Working (no API key required)", "SUCCESS")
            return True
    except Exception as e:
        print_status(f"yfinance: Error - {e}", "ERROR")
    
    return False

async def main():
    """Main function to test all APIs"""
    print(f"{Colors.BOLD}🔑 Calvin Stock Prediction Tool - API Key Validation{Colors.ENDC}")
    print("=" * 60)
    print()
    
    # Get API keys from environment
    api_keys = {
        "POLYGON_API_KEY": os.getenv("POLYGON_API_KEY", ""),
        "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", ""),
        "FINANCIAL_MODELING_PREP_API_KEY": os.getenv("FINANCIAL_MODELING_PREP_API_KEY", ""),
    }
    
    print_status("Testing API connections...", "INFO")
    print()
    
    # Test each API
    results = []
    
    # Test Polygon
    polygon_result = await test_polygon_api(api_keys["POLYGON_API_KEY"])
    results.append(("Polygon.io", polygon_result))
    
    # Test Alpha Vantage
    av_result = await test_alpha_vantage_api(api_keys["ALPHA_VANTAGE_API_KEY"])
    results.append(("Alpha Vantage", av_result))
    
    # Test Tavily
    tavily_result = await test_tavily_api(api_keys["TAVILY_API_KEY"])
    results.append(("Tavily", tavily_result))
    
    # Test Financial Modeling Prep
    fmp_result = await test_fmp_api(api_keys["FINANCIAL_MODELING_PREP_API_KEY"])
    results.append(("Financial Modeling Prep", fmp_result))
    
    # Test yfinance
    yf_result = test_yfinance()
    results.append(("yfinance", yf_result))
    
    print()
    print("=" * 60)
    print(f"{Colors.BOLD}📊 API Test Results Summary{Colors.ENDC}")
    print("=" * 60)
    
    working_apis = 0
    total_apis = len(results)
    
    for api_name, status in results:
        status_text = f"{Colors.GREEN}✅ Working{Colors.ENDC}" if status else f"{Colors.RED}❌ Not Working{Colors.ENDC}"
        print(f"{api_name:25} {status_text}")
        if status:
            working_apis += 1
    
    print()
    print(f"Working APIs: {working_apis}/{total_apis}")
    
    if working_apis == 0:
        print_status("No APIs are working. The system will have limited functionality.", "ERROR")
        print_status("At minimum, yfinance should work for basic functionality.", "WARNING")
    elif working_apis < 3:
        print_status("Some APIs are not working. Consider adding more API keys for full functionality.", "WARNING")
    else:
        print_status("Good! Multiple APIs are working. The system should function well.", "SUCCESS")
    
    print()
    print(f"{Colors.BOLD}💡 Tips:{Colors.ENDC}")
    print("- Get free API keys from the respective websites")
    print("- yfinance works without API keys but may have rate limits")
    print("- At least one working API is recommended for data collection")
    print("- Multiple APIs provide redundancy and more data sources")
    
    return working_apis > 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)