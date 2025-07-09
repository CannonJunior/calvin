#!/usr/bin/env python3
"""
MCP Server for Earnings Analysis
Handles earnings calendar, results, sentiment analysis, and historical patterns
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Earnings Analysis Server")

# Base paths for data storage
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
EARNINGS_DIR = ASSETS_DIR / "earnings_data"

def ensure_directories():
    """Ensure required directories exist"""
    EARNINGS_DIR.mkdir(parents=True, exist_ok=True)

@mcp.tool()
async def get_earnings_calendar(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get earnings calendar for specified date range
    
    Args:
        start_date: Start date (YYYY-MM-DD format, defaults to today)
        end_date: End date (YYYY-MM-DD format, defaults to +30 days)
        limit: Maximum number of earnings to return
    
    Returns:
        Dictionary with earnings calendar data
    """
    ensure_directories()
    
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date:
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    earnings_calendar = []
    
    # Read earnings files
    for earnings_file in EARNINGS_DIR.glob("*_earnings.json"):
        try:
            with open(earnings_file, 'r') as f:
                earnings_data = json.load(f)
                
            # Filter by date range
            earnings_date = earnings_data.get('earnings_date')
            if earnings_date and start_date <= earnings_date <= end_date:
                earnings_calendar.append(earnings_data)
                
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Sort by earnings date
    earnings_calendar.sort(key=lambda x: x.get('earnings_date', ''))
    earnings_calendar = earnings_calendar[:limit]
    
    return {
        "earnings_calendar": earnings_calendar,
        "start_date": start_date,
        "end_date": end_date,
        "total": len(earnings_calendar)
    }

@mcp.tool()
async def get_company_earnings_history(
    symbol: str,
    quarters_back: int = 8
) -> Dict[str, Any]:
    """
    Get historical earnings data for a company
    
    Args:
        symbol: Company ticker symbol
        quarters_back: Number of quarters of history to return
    
    Returns:
        Dictionary with historical earnings data
    """
    ensure_directories()
    
    symbol = symbol.upper()
    earnings_file = EARNINGS_DIR / f"{symbol}_history.json"
    
    if not earnings_file.exists():
        return {"error": f"No earnings history found for {symbol}"}
    
    try:
        with open(earnings_file, 'r') as f:
            history_data = json.load(f)
            
        # Get recent quarters
        quarters = history_data.get('quarterly_earnings', [])
        recent_quarters = quarters[-quarters_back:] if quarters else []
        
        return {
            "symbol": symbol,
            "quarterly_earnings": recent_quarters,
            "quarters_returned": len(recent_quarters),
            "total_quarters_available": len(quarters)
        }
        
    except json.JSONDecodeError:
        return {"error": f"Invalid earnings history data for {symbol}"}

@mcp.tool()
async def analyze_earnings_surprise(
    symbol: str,
    actual_eps: float,
    expected_eps: float,
    actual_revenue: Optional[float] = None,
    expected_revenue: Optional[float] = None
) -> Dict[str, Any]:
    """
    Analyze earnings surprise and its implications
    
    Args:
        symbol: Company ticker symbol
        actual_eps: Actual earnings per share
        expected_eps: Expected earnings per share
        actual_revenue: Actual revenue (optional)
        expected_revenue: Expected revenue (optional)
    
    Returns:
        Dictionary with surprise analysis
    """
    eps_surprise = actual_eps - expected_eps
    eps_surprise_percent = (eps_surprise / expected_eps) * 100 if expected_eps != 0 else 0
    
    # Determine surprise category
    if eps_surprise_percent > 5:
        surprise_category = "Strong Beat"
    elif eps_surprise_percent > 0:
        surprise_category = "Beat"
    elif eps_surprise_percent > -5:
        surprise_category = "Meet/Minor Miss"
    else:
        surprise_category = "Miss"
    
    analysis = {
        "symbol": symbol,
        "eps_analysis": {
            "actual": actual_eps,
            "expected": expected_eps,
            "surprise": eps_surprise,
            "surprise_percent": round(eps_surprise_percent, 2),
            "category": surprise_category
        }
    }
    
    # Revenue analysis if provided
    if actual_revenue is not None and expected_revenue is not None:
        revenue_surprise = actual_revenue - expected_revenue
        revenue_surprise_percent = (revenue_surprise / expected_revenue) * 100 if expected_revenue != 0 else 0
        
        analysis["revenue_analysis"] = {
            "actual": actual_revenue,
            "expected": expected_revenue,
            "surprise": revenue_surprise,
            "surprise_percent": round(revenue_surprise_percent, 2)
        }
    
    # Historical context
    history = await get_company_earnings_history(symbol, quarters_back=4)
    if "quarterly_earnings" in history:
        recent_surprises = []
        for quarter in history["quarterly_earnings"]:
            if "eps_surprise_percent" in quarter:
                recent_surprises.append(quarter["eps_surprise_percent"])
        
        if recent_surprises:
            avg_surprise = sum(recent_surprises) / len(recent_surprises)
            analysis["historical_context"] = {
                "average_surprise_4q": round(avg_surprise, 2),
                "current_vs_average": "Above" if eps_surprise_percent > avg_surprise else "Below"
            }
    
    return analysis

@mcp.tool()
async def save_earnings_result(earnings_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save earnings result data
    
    Args:
        earnings_data: Dictionary containing earnings information
    
    Returns:
        Success/error message
    """
    ensure_directories()
    
    if 'symbol' not in earnings_data:
        return {"error": "Symbol is required"}
    
    symbol = earnings_data['symbol'].upper()
    earnings_file = EARNINGS_DIR / f"{symbol}_earnings.json"
    
    # Add timestamp
    earnings_data['recorded_at'] = datetime.now().isoformat()
    earnings_data['symbol'] = symbol
    
    try:
        with open(earnings_file, 'w') as f:
            json.dump(earnings_data, f, indent=2)
        
        return {
            "success": True,
            "message": f"Earnings data for {symbol} saved successfully",
            "symbol": symbol
        }
    except Exception as e:
        return {"error": f"Failed to save earnings data: {str(e)}"}

@mcp.tool()
async def find_similar_earnings_patterns(
    target_company: str,
    surprise_type: str,
    lookback_days: int = 365
) -> Dict[str, Any]:
    """
    Find historical earnings with similar patterns for comparison
    
    Args:
        target_company: Company to find patterns for
        surprise_type: Type of surprise ("beat", "miss", "meet")
        lookback_days: How far back to search
    
    Returns:
        Dictionary with similar patterns
    """
    ensure_directories()
    
    similar_patterns = []
    cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    
    # Search through earnings files
    for earnings_file in EARNINGS_DIR.glob("*_earnings.json"):
        try:
            with open(earnings_file, 'r') as f:
                earnings_data = json.load(f)
            
            # Skip if too old
            earnings_date = earnings_data.get('earnings_date', '')
            if earnings_date < cutoff_date:
                continue
            
            # Check surprise type match
            surprise_category = earnings_data.get('surprise_category', '').lower()
            if surprise_type.lower() in surprise_category:
                similar_patterns.append({
                    "symbol": earnings_data.get('symbol'),
                    "earnings_date": earnings_date,
                    "surprise_category": earnings_data.get('surprise_category'),
                    "eps_surprise_percent": earnings_data.get('eps_surprise_percent'),
                    "next_day_return": earnings_data.get('next_day_return'),
                    "week_return": earnings_data.get('week_return')
                })
                
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Sort by similarity score (could be enhanced with more sophisticated matching)
    similar_patterns.sort(key=lambda x: x.get('earnings_date', ''), reverse=True)
    
    return {
        "target_company": target_company,
        "surprise_type": surprise_type,
        "similar_patterns": similar_patterns[:10],  # Top 10 matches
        "total_found": len(similar_patterns)
    }

@mcp.resource("earnings://calendar")
async def earnings_calendar_resource() -> str:
    """Resource providing current earnings calendar"""
    calendar_data = await get_earnings_calendar()
    return json.dumps(calendar_data, indent=2)

@mcp.resource("earnings://recent")
async def recent_earnings_resource() -> str:
    """Resource providing recent earnings results"""
    # Get earnings from last 7 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    recent_data = await get_earnings_calendar(start_date, end_date, limit=20)
    return json.dumps(recent_data, indent=2)

# Initialize sample earnings data
async def initialize_sample_data():
    """Initialize with sample earnings data if none exists"""
    ensure_directories()
    
    if not list(EARNINGS_DIR.glob("*.json")):
        sample_earnings = [
            {
                "symbol": "AAPL",
                "earnings_date": "2024-01-25",
                "actual_eps": 2.18,
                "expected_eps": 2.10,
                "eps_surprise_percent": 3.8,
                "surprise_category": "Beat",
                "next_day_return": 1.2,
                "week_return": 3.5
            },
            {
                "symbol": "MSFT",
                "earnings_date": "2024-01-24",
                "actual_eps": 2.93,
                "expected_eps": 2.78,
                "eps_surprise_percent": 5.4,
                "surprise_category": "Strong Beat",
                "next_day_return": 2.1,
                "week_return": 4.2
            }
        ]
        
        for earnings in sample_earnings:
            await save_earnings_result(earnings)

if __name__ == "__main__":
    import asyncio
    
    # Initialize sample data
    asyncio.run(initialize_sample_data())
    
    # Run the MCP server
    mcp.run()