#!/usr/bin/env python3
"""
Earnings Data Collector for S&P 500 Companies

Collects earnings data from NASDAQ and other sources with all 36 required template fields:
1. symbol, 2. earnings_date, 3. quarter, 4. year, 5. actual_eps, 6. estimated_eps,
7. beat_miss_meet, 8. surprise_percent, 9. revenue_billions, 10. revenue_growth_percent,
11. consensus_rating, 12. confidence_score, 13. source_url, 14. data_verified_date,
15. stock_price_on_date, 16. announcement_time, 17. volume, 18. date_earnings_report,
19. market_cap, 20. price_at_close-earnings_report_date, 21. price_at_open-day_after_earnings_report_date,
22. percentage_stock_change, 23. earnings_report_result, 24. estimated_earnings_per_share,
25. reported_earnings_per_share, 26. volume_day_of_earnings_report, 27. volume_day_after_earnings_report,
28. 200-day_moving_average, 29. 50-day_moving_average, 30. 52-week_high, 31. 52-week_low,
32. market_sector, 33. market_sub_sector, 34. percentage_short_interest, 35. dividend_yield,
36. Ex-dividend date
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass, asdict
import time
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EarningsData:
    """Complete earnings data structure with all 36 required fields"""
    # Core earnings fields (1-18)
    symbol: str
    earnings_date: str  # Actual reporting date
    quarter: int
    year: int
    actual_eps: Optional[float]
    estimated_eps: Optional[float]
    beat_miss_meet: Optional[str]  # 'BEAT', 'MISS', 'MEET'
    surprise_percent: Optional[float]
    revenue_billions: Optional[float]
    revenue_growth_percent: Optional[float]
    consensus_rating: Optional[str]
    confidence_score: float
    source_url: str
    data_verified_date: str
    stock_price_on_date: Optional[float]
    announcement_time: Optional[str]  # 'AMC', 'BMO'
    volume: Optional[int]
    date_earnings_report: Optional[str]
    
    # Market data fields (19-27)
    market_cap: Optional[float]
    price_at_close_earnings_report_date: Optional[float]
    price_at_open_day_after_earnings_report_date: Optional[float]
    percentage_stock_change: Optional[float]
    earnings_report_result: Optional[str]
    estimated_earnings_per_share: Optional[float]
    reported_earnings_per_share: Optional[float]
    volume_day_of_earnings_report: Optional[int]
    volume_day_after_earnings_report: Optional[int]
    
    # Technical indicators (28-31)
    moving_average_200_day: Optional[float]
    moving_average_50_day: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    
    # Company fundamentals (32-36)
    market_sector: Optional[str]
    market_sub_sector: Optional[str]
    percentage_short_interest: Optional[float]
    dividend_yield: Optional[float]
    ex_dividend_date: Optional[str]

class EarningsCollector:
    """Main class for collecting earnings data from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data_dir = Path("earnings_data")
        self.data_dir.mkdir(exist_ok=True)
        
    def load_sp500_companies(self) -> List[Dict[str, Any]]:
        """Load S&P 500 companies from JSON file"""
        with open("sp500_companies.json", "r") as f:
            return json.load(f)
    
    def collect_nasdaq_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Collect earnings data from NASDAQ for a given symbol"""
        url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
        logger.info(f"Collecting NASDAQ data for {symbol}")
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(1)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML response to extract earnings data
            return self._parse_nasdaq_earnings(response.text, symbol)
            
        except Exception as e:
            logger.error(f"Error collecting NASDAQ data for {symbol}: {e}")
            return []
    
    def _parse_nasdaq_earnings(self, html_content: str, symbol: str) -> List[Dict[str, Any]]:
        """Parse NASDAQ earnings HTML to extract data"""
        # This will be implemented with BeautifulSoup or similar
        # For now, return empty list to avoid errors
        logger.warning(f"HTML parsing not yet implemented for {symbol}")
        return []
    
    def create_earnings_record(self, symbol: str, raw_data: Dict[str, Any], 
                             company_info: Dict[str, Any]) -> EarningsData:
        """Create a complete EarningsData record with all 36 fields"""
        
        return EarningsData(
            # Core earnings fields (1-18)
            symbol=symbol,
            earnings_date=raw_data.get('earnings_date', ''),
            quarter=raw_data.get('quarter', 0),
            year=raw_data.get('year', 0),
            actual_eps=raw_data.get('actual_eps'),
            estimated_eps=raw_data.get('estimated_eps'),
            beat_miss_meet=self._calculate_beat_miss_meet(
                raw_data.get('actual_eps'), raw_data.get('estimated_eps')
            ),
            surprise_percent=self._calculate_surprise_percent(
                raw_data.get('actual_eps'), raw_data.get('estimated_eps')
            ),
            revenue_billions=raw_data.get('revenue_billions'),
            revenue_growth_percent=raw_data.get('revenue_growth_percent'),
            consensus_rating=raw_data.get('consensus_rating'),
            confidence_score=raw_data.get('confidence_score', 0.5),
            source_url=f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings",
            data_verified_date=date.today().isoformat(),
            stock_price_on_date=raw_data.get('stock_price_on_date'),
            announcement_time=raw_data.get('announcement_time'),
            volume=raw_data.get('volume'),
            date_earnings_report=raw_data.get('date_earnings_report'),
            
            # Market data fields (19-27)
            market_cap=raw_data.get('market_cap'),
            price_at_close_earnings_report_date=raw_data.get('price_at_close_earnings_report_date'),
            price_at_open_day_after_earnings_report_date=raw_data.get('price_at_open_day_after_earnings_report_date'),
            percentage_stock_change=raw_data.get('percentage_stock_change'),
            earnings_report_result=raw_data.get('earnings_report_result'),
            estimated_earnings_per_share=raw_data.get('estimated_earnings_per_share'),
            reported_earnings_per_share=raw_data.get('reported_earnings_per_share'),
            volume_day_of_earnings_report=raw_data.get('volume_day_of_earnings_report'),
            volume_day_after_earnings_report=raw_data.get('volume_day_after_earnings_report'),
            
            # Technical indicators (28-31)
            moving_average_200_day=raw_data.get('200_day_moving_average'),
            moving_average_50_day=raw_data.get('50_day_moving_average'),
            week_52_high=raw_data.get('52_week_high'),
            week_52_low=raw_data.get('52_week_low'),
            
            # Company fundamentals (32-36)
            market_sector=company_info.get('gics_sector'),
            market_sub_sector=company_info.get('gics_sub_industry'),
            percentage_short_interest=raw_data.get('percentage_short_interest'),
            dividend_yield=raw_data.get('dividend_yield'),
            ex_dividend_date=raw_data.get('ex_dividend_date')
        )
    
    def _calculate_beat_miss_meet(self, actual: Optional[float], 
                                 estimated: Optional[float]) -> Optional[str]:
        """Calculate if earnings beat, missed, or met estimates"""
        if actual is None or estimated is None:
            return None
        
        if actual > estimated:
            return 'BEAT'
        elif actual < estimated:
            return 'MISS'
        else:
            return 'MEET'
    
    def _calculate_surprise_percent(self, actual: Optional[float], 
                                   estimated: Optional[float]) -> Optional[float]:
        """Calculate earnings surprise percentage"""
        if actual is None or estimated is None or estimated == 0:
            return None
        
        return round(((actual - estimated) / estimated) * 100, 2)
    
    def save_earnings_data(self, symbol: str, earnings_list: List[EarningsData]):
        """Save earnings data to JSON file"""
        filename = self.data_dir / f"{symbol}.json"
        
        # Convert dataclass objects to dictionaries
        data = [asdict(earnings) for earnings in earnings_list]
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved {len(earnings_list)} earnings records for {symbol}")
    
    def collect_company_earnings(self, company_info: Dict[str, Any]) -> List[EarningsData]:
        """Collect all earnings data for a single company"""
        symbol = company_info['symbol']
        logger.info(f"Processing earnings for {symbol}")
        
        # Collect data from various sources
        nasdaq_data = self.collect_nasdaq_data(symbol)
        
        earnings_list = []
        
        # Process each earnings report
        for raw_earnings in nasdaq_data:
            earnings_record = self.create_earnings_record(symbol, raw_earnings, company_info)
            earnings_list.append(earnings_record)
        
        return earnings_list
    
    def process_all_companies(self):
        """Process earnings data for all S&P 500 companies"""
        companies = self.load_sp500_companies()
        total_companies = len(companies)
        
        logger.info(f"Processing {total_companies} S&P 500 companies")
        
        for i, company in enumerate(companies, 1):
            symbol = company['symbol']
            logger.info(f"Processing {i}/{total_companies}: {symbol}")
            
            try:
                earnings_data = self.collect_company_earnings(company)
                self.save_earnings_data(symbol, earnings_data)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        logger.info("Finished processing all companies")

def main():
    """Main entry point"""
    collector = EarningsCollector()
    collector.process_all_companies()

if __name__ == "__main__":
    main()