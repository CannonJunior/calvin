# Copyright 2025 CannonJunior
  
# This file is part of mcp_experiments, and is released under the "MIT License Agreement".
# Please see the LICENSE.md file that should have been included as part of this package.
# Enhanced MCP Finance Server with comprehensive financial data tools
# Usage: uv run finance_server.py

from fastmcp import FastMCP
import yfinance as yf
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

mcp = FastMCP("Finance Server")

@mcp.tool()
async def get_stock_price(symbol: str) -> Dict[str, Any]:
    """Get current stock price and key metrics for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="2d")
        
        if hist.empty:
            return {"error": f"No data available for {symbol}"}
            
        current_price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close != 0 else 0
        
        return {
            "symbol": symbol.upper(),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to get stock price for {symbol}: {str(e)}"}

@mcp.tool()
async def get_market_data(symbol: str, period: str = "1mo", interval: str = "1d") -> Dict[str, Any]:
    """Get historical market data with flexible periods and intervals"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": f"No historical data available for {symbol}"}
        
        # Convert to records for JSON serialization
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "data": data,
            "total_records": len(data)
        }
    except Exception as e:
        return {"error": f"Failed to get market data for {symbol}: {str(e)}"}

@mcp.tool()
async def get_company_info(symbol: str) -> Dict[str, Any]:
    """Get comprehensive company information"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "symbol": symbol.upper(),
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "description": info.get("longBusinessSummary", ""),
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees", 0),
            "headquarters": {
                "city": info.get("city", ""),
                "state": info.get("state", ""),
                "country": info.get("country", "")
            },
            "financial_metrics": {
                "market_cap": info.get("marketCap", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "peg_ratio": info.get("pegRatio", 0),
                "price_to_book": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0)
            }
        }
    except Exception as e:
        return {"error": f"Failed to get company info for {symbol}: {str(e)}"}

@mcp.tool()
async def get_earnings_calendar(symbol: str) -> Dict[str, Any]:
    """Get earnings calendar and estimates for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        calendar = ticker.calendar
        
        result = {"symbol": symbol.upper()}
        
        if calendar is not None and not calendar.empty:
            earnings_date = calendar.index[0]
            result.update({
                "earnings_date": earnings_date.strftime("%Y-%m-%d"),
                "eps_estimate": float(calendar.iloc[0, 0]) if len(calendar.columns) > 0 else None,
                "revenue_estimate": float(calendar.iloc[0, 1]) if len(calendar.columns) > 1 else None
            })
        else:
            result.update({
                "earnings_date": None,
                "eps_estimate": None,
                "revenue_estimate": None
            })
            
        return result
    except Exception as e:
        return {"error": f"Failed to get earnings calendar for {symbol}: {str(e)}"}

@mcp.tool()
async def get_market_indices() -> Dict[str, Any]:
    """Get major market indices data"""
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones Industrial Average",
        "^IXIC": "NASDAQ Composite",
        "^VIX": "CBOE Volatility Index",
        "^TNX": "10-Year Treasury Yield"
    }
    
    results = {}
    
    for symbol, name in indices.items():
        try:
            price_data = await get_stock_price(symbol)
            if "error" not in price_data:
                results[symbol] = {
                    "name": name,
                    "price": price_data["price"],
                    "change": price_data["change"],
                    "change_percent": price_data["change_percent"]
                }
            else:
                results[symbol] = {"name": name, "error": "Data unavailable"}
                
        except Exception:
            results[symbol] = {"name": name, "error": "Data unavailable"}
    
    return {
        "indices": results,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def search_stocks(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search for stocks by company name or symbol"""
    # Simple implementation - in production would use a proper search API
    common_stocks = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation", 
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "META": "Meta Platforms Inc.",
        "NVDA": "NVIDIA Corporation",
        "JPM": "JPMorgan Chase & Co.",
        "JNJ": "Johnson & Johnson",
        "PG": "Procter & Gamble Co."
    }
    
    query_lower = query.lower()
    matches = []
    
    for symbol, name in common_stocks.items():
        if (query_lower in symbol.lower() or 
            query_lower in name.lower()):
            matches.append({
                "symbol": symbol,
                "name": name
            })
    
    return {
        "query": query,
        "matches": matches[:limit],
        "total_matches": len(matches)
    }

@mcp.resource("finance://market-status")
async def market_status_resource() -> str:
    """Resource providing current market status and indices"""
    indices_data = await get_market_indices()
    return json.dumps(indices_data, indent=2)

@mcp.resource("finance://sp500")
async def sp500_resource() -> str:
    """Resource providing S&P 500 index data"""
    sp500_data = await get_stock_price("^GSPC")
    return json.dumps(sp500_data, indent=2)

@mcp.prompt("stock-analysis")
async def stock_analysis_prompt(symbol: str = "AAPL") -> str:
    """Generate comprehensive stock analysis prompt"""
    return f"""Analyze the stock {symbol} and provide:
1. Current market sentiment (bullish/bearish/neutral)
2. Key technical indicators assessment
3. Recent news impact analysis
4. Short-term price direction prediction
5. Risk factors to consider
6. Overall recommendation (buy/hold/sell)

Provide a sentiment score from -10 (very bearish) to +10 (very bullish).
Keep analysis concise but thorough."""

if __name__ == "__main__":
    mcp.run()
