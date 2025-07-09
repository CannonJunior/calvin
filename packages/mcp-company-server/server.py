#!/usr/bin/env python3
"""
MCP Server for Company Data Management
Handles S&P 500 company information, sectors, and metadata
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Company Data Server")

# Base paths for data storage
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
COMPANIES_DIR = ASSETS_DIR / "sp500_companies"

def ensure_directories():
    """Ensure required directories exist"""
    COMPANIES_DIR.mkdir(parents=True, exist_ok=True)

@mcp.tool()
async def get_companies(
    limit: int = 100, 
    sector: Optional[str] = None,
    sp500_only: bool = True
) -> Dict[str, Any]:
    """
    Get list of companies with optional filtering
    
    Args:
        limit: Maximum number of companies to return
        sector: Filter by sector (optional)
        sp500_only: Only include S&P 500 companies
    
    Returns:
        Dictionary with companies list and metadata
    """
    ensure_directories()
    
    companies = []
    
    # Read company files from assets directory
    for company_file in COMPANIES_DIR.glob("*.json"):
        try:
            with open(company_file, 'r') as f:
                company_data = json.load(f)
                
            # Apply filters
            if sector and company_data.get('sector') != sector:
                continue
                
            if sp500_only and not company_data.get('sp500_constituent', True):
                continue
                
            companies.append(company_data)
            
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Sort by symbol and apply limit
    companies.sort(key=lambda x: x.get('symbol', ''))
    companies = companies[:limit]
    
    return {
        "companies": companies,
        "total": len(companies),
        "filtered_by_sector": sector,
        "sp500_only": sp500_only
    }

@mcp.tool()
async def get_company_by_symbol(symbol: str) -> Dict[str, Any]:
    """
    Get detailed company information by symbol
    
    Args:
        symbol: Company ticker symbol (e.g., 'AAPL')
    
    Returns:
        Company data dictionary or error message
    """
    ensure_directories()
    
    symbol = symbol.upper()
    company_file = COMPANIES_DIR / f"{symbol}.json"
    
    if not company_file.exists():
        return {"error": f"Company {symbol} not found"}
    
    try:
        with open(company_file, 'r') as f:
            company_data = json.load(f)
        return company_data
    except json.JSONDecodeError:
        return {"error": f"Invalid data for company {symbol}"}

@mcp.tool()
async def add_company(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add or update company information
    
    Args:
        company_data: Dictionary containing company information
    
    Returns:
        Success/error message
    """
    ensure_directories()
    
    if 'symbol' not in company_data:
        return {"error": "Company symbol is required"}
    
    symbol = company_data['symbol'].upper()
    company_file = COMPANIES_DIR / f"{symbol}.json"
    
    # Add metadata
    company_data['symbol'] = symbol
    company_data.setdefault('sp500_constituent', True)
    company_data.setdefault('last_updated', None)
    
    try:
        with open(company_file, 'w') as f:
            json.dump(company_data, f, indent=2)
        
        return {
            "success": True,
            "message": f"Company {symbol} saved successfully",
            "symbol": symbol
        }
    except Exception as e:
        return {"error": f"Failed to save company {symbol}: {str(e)}"}

@mcp.tool()
async def get_sectors() -> Dict[str, Any]:
    """
    Get list of all unique sectors from companies
    
    Returns:
        Dictionary with sectors list and counts
    """
    ensure_directories()
    
    sectors = {}
    
    for company_file in COMPANIES_DIR.glob("*.json"):
        try:
            with open(company_file, 'r') as f:
                company_data = json.load(f)
                
            sector = company_data.get('sector')
            if sector:
                sectors[sector] = sectors.get(sector, 0) + 1
                
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    return {
        "sectors": list(sectors.keys()),
        "sector_counts": sectors,
        "total_sectors": len(sectors)
    }

@mcp.tool()
async def search_companies(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search companies by name or symbol
    
    Args:
        query: Search query (name or symbol)
        limit: Maximum results to return
    
    Returns:
        Dictionary with matching companies
    """
    ensure_directories()
    
    query = query.lower()
    matches = []
    
    for company_file in COMPANIES_DIR.glob("*.json"):
        try:
            with open(company_file, 'r') as f:
                company_data = json.load(f)
                
            symbol = company_data.get('symbol', '').lower()
            name = company_data.get('name', '').lower()
            
            if query in symbol or query in name:
                matches.append(company_data)
                
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Sort by relevance (exact symbol match first, then name matches)
    matches.sort(key=lambda x: (
        query != x.get('symbol', '').lower(),  # Exact symbol match first
        query not in x.get('symbol', '').lower(),  # Symbol contains query
        x.get('symbol', '')  # Alphabetical
    ))
    
    return {
        "matches": matches[:limit],
        "total_matches": len(matches),
        "query": query
    }

@mcp.resource("companies://list")
async def companies_resource() -> str:
    """Resource providing current companies list"""
    companies_data = await get_companies(limit=1000)
    return json.dumps(companies_data, indent=2)

@mcp.resource("companies://sectors")
async def sectors_resource() -> str:
    """Resource providing sectors information"""
    sectors_data = await get_sectors()
    return json.dumps(sectors_data, indent=2)

# Create sample data if none exists
async def initialize_sample_data():
    """Initialize with sample S&P 500 companies if no data exists"""
    ensure_directories()
    
    if not list(COMPANIES_DIR.glob("*.json")):
        sample_companies = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "market_cap": 3000000000000,
                "sp500_constituent": True
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "sector": "Technology",
                "industry": "Software",
                "market_cap": 2800000000000,
                "sp500_constituent": True
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "sector": "Technology",
                "industry": "Internet",
                "market_cap": 1700000000000,
                "sp500_constituent": True
            },
            {
                "symbol": "AMZN",
                "name": "Amazon.com Inc.",
                "sector": "Consumer Discretionary",
                "industry": "E-commerce",
                "market_cap": 1500000000000,
                "sp500_constituent": True
            },
            {
                "symbol": "TSLA",
                "name": "Tesla Inc.",
                "sector": "Consumer Discretionary",
                "industry": "Electric Vehicles",
                "market_cap": 800000000000,
                "sp500_constituent": True
            }
        ]
        
        for company in sample_companies:
            await add_company(company)

if __name__ == "__main__":
    import asyncio
    
    # Initialize sample data
    asyncio.run(initialize_sample_data())
    
    # Run the MCP server
    mcp.run()