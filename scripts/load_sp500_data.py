#!/usr/bin/env python3
"""
Script to load S&P 500 company data into the database
"""

import asyncio
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.company import Company, EarningsEvent
from app.db.database import Base


async def get_sp500_list():
    """Get S&P 500 companies list from Wikipedia"""
    
    try:
        # Get S&P 500 list from Wikipedia
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_table = tables[0]
        
        companies = []
        for _, row in sp500_table.iterrows():
            companies.append({
                "symbol": row["Symbol"],
                "name": row["Security"],
                "sector": row["GICS Sector"],
                "industry": row["GICS Sub-Industry"],
                "date_added": row.get("Date added", None),
            })
        
        return companies
    
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        # Fallback to a smaller list for testing
        return [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "industry": "E-commerce"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet Services"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary", "industry": "Electric Vehicles"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Communication Services", "industry": "Social Media"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials", "industry": "Banking"},
            {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Health Care", "industry": "Pharmaceuticals"},
            {"symbol": "V", "name": "Visa Inc.", "sector": "Financials", "industry": "Payment Systems"},
        ]


async def get_company_info(symbol: str):
    """Get detailed company information using yfinance"""
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "market_cap": info.get("marketCap", 0) / 1_000_000 if info.get("marketCap") else None,  # Convert to millions
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "revenue": info.get("totalRevenue", 0) / 1_000_000 if info.get("totalRevenue") else None,  # Convert to millions
            "description": info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else None,
        }
    
    except Exception as e:
        print(f"Error getting info for {symbol}: {e}")
        return {}


async def get_earnings_data(symbol: str):
    """Get recent earnings data for a company"""
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get earnings calendar (upcoming)
        earnings_calendar = ticker.calendar
        
        # Get historical earnings (quarterly)
        quarterly_earnings = ticker.quarterly_earnings
        
        earnings_events = []
        
        # Process historical earnings
        if quarterly_earnings is not None and not quarterly_earnings.empty:
            for date, row in quarterly_earnings.head(8).iterrows():  # Last 8 quarters
                earnings_events.append({
                    "earnings_date": date,
                    "quarter": f"Q{((date.month - 1) // 3) + 1}",
                    "year": date.year,
                    "actual_eps": row.get("Earnings", None),
                    "expected_eps": None,  # Would need analyst estimates
                    "actual_revenue": row.get("Revenue", None),
                })
        
        return earnings_events
    
    except Exception as e:
        print(f"Error getting earnings for {symbol}: {e}")
        return []


async def save_to_json(data, filename: str):
    """Save data to JSON file in assets directory"""
    
    filepath = f"assets/sp500_companies/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Saved data to {filepath}")


async def load_companies_to_db(companies_data: list):
    """Load companies data into the database"""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        for company_data in companies_data:
            try:
                # Check if company already exists
                existing = await session.get(Company, company_data["symbol"])
                
                if not existing:
                    company = Company(
                        symbol=company_data["symbol"],
                        name=company_data["name"],
                        sector=company_data.get("sector"),
                        industry=company_data.get("industry"),
                        market_cap=company_data.get("market_cap"),
                        pe_ratio=company_data.get("pe_ratio"),
                        eps=company_data.get("eps"),
                        revenue=company_data.get("revenue"),
                        description=company_data.get("description"),
                        sp500_constituent=True,
                    )
                    
                    session.add(company)
                    print(f"Added {company_data['symbol']} to database")
                else:
                    print(f"Company {company_data['symbol']} already exists in database")
            
            except Exception as e:
                print(f"Error adding {company_data.get('symbol', 'unknown')}: {e}")
        
        await session.commit()
    
    await engine.dispose()


async def main():
    """Main function to collect and save S&P 500 data"""
    
    print("Starting S&P 500 data collection...")
    
    # Get S&P 500 companies list
    print("Fetching S&P 500 companies list...")
    companies = await get_sp500_list()
    print(f"Found {len(companies)} S&P 500 companies")
    
    # Enhance with detailed company information
    enhanced_companies = []
    
    for i, company in enumerate(companies[:20]):  # Limit to first 20 for demo
        print(f"Processing {company['symbol']} ({i+1}/{min(20, len(companies))})...")
        
        # Get detailed company info
        company_info = await get_company_info(company["symbol"])
        
        # Get earnings data
        earnings_data = await get_earnings_data(company["symbol"])
        
        # Combine data
        enhanced_company = {
            **company,
            **company_info,
            "earnings_history": earnings_data,
            "last_updated": datetime.now().isoformat(),
        }
        
        enhanced_companies.append(enhanced_company)
        
        # Save individual company file
        await save_to_json(enhanced_company, f"{company['symbol']}.json")
        
        # Add small delay to respect rate limits
        await asyncio.sleep(1)
    
    # Save consolidated file
    await save_to_json(enhanced_companies, "sp500_companies.json")
    
    # Load to database
    print("Loading companies to database...")
    await load_companies_to_db(enhanced_companies)
    
    print("S&P 500 data collection completed!")
    print(f"Processed {len(enhanced_companies)} companies")
    print("Data saved to assets/sp500_companies/ directory")
    print("Companies loaded into database")


if __name__ == "__main__":
    asyncio.run(main())