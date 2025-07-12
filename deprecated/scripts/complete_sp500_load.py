#!/usr/bin/env python3
"""
Enhanced script to load complete S&P 500 company data with comprehensive enrichment
"""

import asyncio
import json
import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Dict, List, Optional


class SP500DataCollector:
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.tavily_key = os.getenv("TAVILY_API_KEY")
        self.polygon_key = os.getenv("POLYGON_API_KEY")
        self.assets_dir = Path("assets/sp500_companies")
        self.assets_dir.mkdir(exist_ok=True)
        
    async def get_complete_sp500_list(self) -> List[Dict]:
        """Get complete S&P 500 companies list from Wikipedia"""
        try:
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
                    "date_added": str(row.get("Date added", "")),
                    "headquarters": row.get("Headquarters Location", ""),
                    "founded": row.get("Founded", ""),
                })
            
            print(f"✅ Found {len(companies)} S&P 500 companies from Wikipedia")
            return companies
            
        except Exception as e:
            print(f"❌ Error fetching S&P 500 list: {e}")
            return []

    async def get_enhanced_company_info(self, symbol: str) -> Dict:
        """Get comprehensive company information using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get stock price history for trends
            hist = ticker.history(period="1y")
            current_price = hist['Close'].iloc[-1] if not hist.empty else None
            year_high = hist['High'].max() if not hist.empty else None
            year_low = hist['Low'].min() if not hist.empty else None
            
            # Calculate price performance
            price_change_1d = None
            price_change_1w = None
            price_change_1m = None
            
            if len(hist) >= 1:
                price_change_1d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) >= 2 else None
            if len(hist) >= 5:
                price_change_1w = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100)
            if len(hist) >= 22:
                price_change_1m = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-23]) / hist['Close'].iloc[-23] * 100)
            
            enhanced_info = {
                # Financial metrics
                "market_cap": info.get("marketCap", 0) / 1_000_000 if info.get("marketCap") else None,
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue", 0) / 1_000_000 if info.get("totalRevenue") else None,
                "profit_margin": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "return_on_equity": info.get("returnOnEquity"),
                "dividend_yield": info.get("dividendYield"),
                
                # Price information
                "current_price": current_price,
                "year_high": year_high,
                "year_low": year_low,
                "price_change_1d": price_change_1d,
                "price_change_1w": price_change_1w,
                "price_change_1m": price_change_1m,
                
                # Company details
                "description": info.get("longBusinessSummary", "")[:750] if info.get("longBusinessSummary") else "",
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency", "USD"),
                
                # Analyst data
                "analyst_target_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationMean"),
                "number_of_analysts": info.get("numberOfAnalystOpinions"),
            }
            
            return enhanced_info
            
        except Exception as e:
            print(f"⚠️  Error getting enhanced info for {symbol}: {e}")
            return {}

    async def get_earnings_calendar_data(self, symbol: str) -> List[Dict]:
        """Get comprehensive earnings data including upcoming and historical"""
        try:
            ticker = yf.Ticker(symbol)
            earnings_events = []
            
            # Get quarterly earnings
            try:
                quarterly_earnings = ticker.quarterly_earnings
                if quarterly_earnings is not None and not quarterly_earnings.empty:
                    for date, row in quarterly_earnings.head(12).iterrows():  # Last 12 quarters
                        earnings_events.append({
                            "type": "historical",
                            "earnings_date": date.isoformat() if pd.notna(date) else None,
                            "quarter": f"Q{((date.month - 1) // 3) + 1}",
                            "year": date.year,
                            "actual_eps": float(row.get("Earnings", 0)) if pd.notna(row.get("Earnings")) else None,
                            "actual_revenue": float(row.get("Revenue", 0)) / 1_000_000 if pd.notna(row.get("Revenue")) else None,
                        })
            except:
                pass
            
            # Get earnings calendar (upcoming earnings)
            try:
                calendar = ticker.calendar
                if calendar is not None and not calendar.empty:
                    for _, row in calendar.iterrows():
                        earnings_events.append({
                            "type": "upcoming",
                            "earnings_date": row.get("Earnings Date").isoformat() if pd.notna(row.get("Earnings Date")) else None,
                            "eps_estimate": row.get("EPS Estimate"),
                            "reported_eps": row.get("Reported EPS"),
                            "surprise": row.get("Surprise(%)"),
                        })
            except:
                pass
            
            return earnings_events
            
        except Exception as e:
            print(f"⚠️  Error getting earnings for {symbol}: {e}")
            return []

    async def get_analyst_data(self, symbol: str) -> Dict:
        """Get analyst recommendations and price targets"""
        try:
            ticker = yf.Ticker(symbol)
            analyst_data = {}
            
            # Get recommendations
            try:
                recommendations = ticker.recommendations
                if recommendations is not None and not recommendations.empty:
                    latest_rec = recommendations.iloc[-1] if not recommendations.empty else None
                    if latest_rec is not None:
                        analyst_data.update({
                            "strong_buy": int(latest_rec.get("strongBuy", 0)),
                            "buy": int(latest_rec.get("buy", 0)),
                            "hold": int(latest_rec.get("hold", 0)),
                            "sell": int(latest_rec.get("sell", 0)),
                            "strong_sell": int(latest_rec.get("strongSell", 0)),
                            "recommendation_date": latest_rec.name.isoformat() if pd.notna(latest_rec.name) else None,
                        })
            except:
                pass
            
            # Get analyst price targets
            try:
                info = ticker.info
                analyst_data.update({
                    "target_high": info.get("targetHighPrice"),
                    "target_low": info.get("targetLowPrice"),
                    "target_mean": info.get("targetMeanPrice"),
                    "target_median": info.get("targetMedianPrice"),
                })
            except:
                pass
            
            return analyst_data
            
        except Exception as e:
            print(f"⚠️  Error getting analyst data for {symbol}: {e}")
            return {}

    async def save_company_data(self, company_data: Dict, symbol: str):
        """Save individual company data to JSON file"""
        filepath = self.assets_dir / f"{symbol}.json"
        
        with open(filepath, 'w') as f:
            json.dump(company_data, f, indent=2, default=str)
        
        print(f"💾 Saved {symbol} data to {filepath}")

    async def save_consolidated_data(self, all_companies: List[Dict]):
        """Save consolidated S&P 500 data"""
        filepath = self.assets_dir / "sp500_companies.json"
        
        with open(filepath, 'w') as f:
            json.dump(all_companies, f, indent=2, default=str)
        
        print(f"💾 Saved consolidated data to {filepath}")
        
        # Also save summary statistics
        summary = {
            "total_companies": len(all_companies),
            "sectors": {},
            "last_updated": datetime.now().isoformat(),
            "data_sources": ["yfinance", "wikipedia"],
            "avg_market_cap": sum([c.get("market_cap", 0) or 0 for c in all_companies]) / len(all_companies),
            "total_market_cap": sum([c.get("market_cap", 0) or 0 for c in all_companies]),
        }
        
        # Count companies by sector
        for company in all_companies:
            sector = company.get("sector", "Unknown")
            summary["sectors"][sector] = summary["sectors"].get(sector, 0) + 1
        
        summary_filepath = self.assets_dir / "sp500_summary.json"
        with open(summary_filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"📊 Saved summary statistics to {summary_filepath}")

    async def process_company(self, company: Dict, index: int, total: int) -> Dict:
        """Process a single company with all data enrichment"""
        symbol = company["symbol"]
        print(f"🔄 Processing {symbol} ({index+1}/{total})...")
        
        # Get enhanced company info
        enhanced_info = await self.get_enhanced_company_info(symbol)
        
        # Get earnings data
        earnings_data = await self.get_earnings_calendar_data(symbol)
        
        # Get analyst data
        analyst_data = await self.get_analyst_data(symbol)
        
        # Combine all data
        complete_company_data = {
            **company,  # Base Wikipedia data
            **enhanced_info,  # Enhanced financial data
            "earnings_history": earnings_data,
            "analyst_data": analyst_data,
            "last_updated": datetime.now().isoformat(),
            "data_quality": {
                "has_financial_data": bool(enhanced_info.get("market_cap")),
                "has_earnings_data": len(earnings_data) > 0,
                "has_analyst_data": len(analyst_data) > 0,
                "completeness_score": (
                    int(bool(enhanced_info.get("market_cap"))) +
                    int(len(earnings_data) > 0) +
                    int(len(analyst_data) > 0)
                ) / 3
            }
        }
        
        # Save individual company file
        await self.save_company_data(complete_company_data, symbol)
        
        # Add delay to respect rate limits
        await asyncio.sleep(1.2)  # Slightly longer delay for comprehensive data
        
        return complete_company_data

    async def collect_all_data(self, limit: Optional[int] = None):
        """Main method to collect all S&P 500 data"""
        print("🚀 Starting comprehensive S&P 500 data collection...")
        
        # Get complete company list
        companies = await self.get_complete_sp500_list()
        if not companies:
            print("❌ Failed to fetch company list")
            return
        
        # Apply limit if specified
        if limit:
            companies = companies[:limit]
            print(f"📊 Processing first {limit} companies for testing")
        
        # Process all companies
        all_enhanced_companies = []
        failed_companies = []
        
        for i, company in enumerate(companies):
            try:
                enhanced_company = await self.process_company(company, i, len(companies))
                all_enhanced_companies.append(enhanced_company)
            except Exception as e:
                print(f"❌ Failed to process {company.get('symbol', 'Unknown')}: {e}")
                failed_companies.append(company)
        
        # Save consolidated data
        await self.save_consolidated_data(all_enhanced_companies)
        
        # Print summary
        print("\n" + "="*60)
        print("📈 S&P 500 Data Collection Complete!")
        print("="*60)
        print(f"✅ Successfully processed: {len(all_enhanced_companies)} companies")
        print(f"❌ Failed to process: {len(failed_companies)} companies")
        
        if failed_companies:
            print(f"⚠️  Failed companies: {', '.join([c.get('symbol', 'Unknown') for c in failed_companies])}")
        
        # Data quality summary
        high_quality = sum(1 for c in all_enhanced_companies if c.get('data_quality', {}).get('completeness_score', 0) >= 0.8)
        medium_quality = sum(1 for c in all_enhanced_companies if 0.5 <= c.get('data_quality', {}).get('completeness_score', 0) < 0.8)
        low_quality = sum(1 for c in all_enhanced_companies if c.get('data_quality', {}).get('completeness_score', 0) < 0.5)
        
        print(f"📊 Data Quality:")
        print(f"   🟢 High quality (80%+): {high_quality} companies")
        print(f"   🟡 Medium quality (50-79%): {medium_quality} companies")
        print(f"   🔴 Low quality (<50%): {low_quality} companies")
        
        print(f"\n💾 All data saved to: {self.assets_dir}")
        print("🎯 Ready for earnings prediction analysis!")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect comprehensive S&P 500 data")
    parser.add_argument("--limit", type=int, help="Limit number of companies to process (for testing)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing data")
    
    args = parser.parse_args()
    
    collector = SP500DataCollector()
    await collector.collect_all_data(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())