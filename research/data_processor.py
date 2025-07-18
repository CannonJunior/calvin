"""
Data processor to convert scraped earnings data to structured JSON files.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
from pathlib import Path

from earnings_schema import CompanyEarningsData, EarningsReport
from nasdaq_scraper import NasdaqEarningsScraper


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EarningsDataProcessor:
    """Process and structure earnings data from web scraping."""
    
    def __init__(self, output_dir: str = "earnings_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.scraper = NasdaqEarningsScraper()
        
    def load_sp500_companies(self, filepath: str = "sp500_companies.json") -> List[Dict]:
        """Load S&P 500 companies list."""
        try:
            with open(filepath, 'r') as f:
                companies = json.load(f)
            logger.info(f"Loaded {len(companies)} S&P 500 companies")
            return companies
        except FileNotFoundError:
            logger.error(f"SP500 companies file not found: {filepath}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing SP500 companies JSON: {e}")
            return []
    
    def process_scraped_data(self, scraped_data: Dict, company_info: Dict) -> Optional[CompanyEarningsData]:
        """Convert scraped data to structured earnings data."""
        try:
            # Extract company information
            symbol = scraped_data.get('symbol', company_info.get('symbol', '')).upper()
            company_name = scraped_data.get('company_info', {}).get('name') or company_info.get('company_name', '')
            sector = company_info.get('gics_sector', 'Unknown')
            sub_sector = company_info.get('gics_sub_industry', 'Unknown')
            
            # Process historical earnings
            historical_reports = []
            for earnings in scraped_data.get('historical_earnings', []):
                report = self._create_earnings_report(earnings, scraped_data, is_historical=True)
                if report:
                    historical_reports.append(report)
            
            # Process projected earnings
            projected_reports = []
            for earnings in scraped_data.get('projected_earnings', []):
                report = self._create_earnings_report(earnings, scraped_data, is_historical=False)
                if report:
                    projected_reports.append(report)
            
            # Create company earnings data
            company_data = CompanyEarningsData(
                symbol=symbol,
                company_name=company_name,
                sector=sector,
                sub_sector=sub_sector,
                historical_reports=historical_reports,
                projected_reports=projected_reports,
                last_updated=datetime.now().isoformat()
            )
            
            return company_data
            
        except Exception as e:
            logger.error(f"Error processing scraped data for {symbol}: {e}")
            return None
    
    def _create_earnings_report(self, earnings_data: Dict, scraped_data: Dict, is_historical: bool) -> Optional[EarningsReport]:
        """Create an EarningsReport from scraped data."""
        try:
            current_metrics = scraped_data.get('current_metrics', {})
            
            # Extract basic earnings data
            date = earnings_data.get('date', '')
            estimated_eps = earnings_data.get('estimated_eps', 0.0)
            reported_eps = earnings_data.get('reported_eps', 0.0) if is_historical else 0.0
            beat_or_miss = earnings_data.get('beat_or_miss', 'projected' if not is_historical else 'unknown')
            
            # For historical data, use current metrics or defaults
            # For projected data, use zeros/None for unknown future values
            if is_historical:
                market_cap = current_metrics.get('market_cap', 0.0)
                close_price = current_metrics.get('current_price', 0.0)
                next_open_price = close_price * 1.01  # Estimated 1% change for demo
                price_change_percent = 1.0
                volume_earnings_day = int(current_metrics.get('volume', 0))
                volume_next_day = volume_earnings_day
                moving_avg_200 = close_price * 0.95  # Estimated values for demo
                moving_avg_50 = close_price * 0.98
                week_52_high = current_metrics.get('52_week_high', close_price * 1.2)
                week_52_low = current_metrics.get('52_week_low', close_price * 0.8)
                short_interest_percent = 1.5  # Default estimate
                dividend_yield = 1.2  # Default estimate
                ex_dividend_date = self._estimate_ex_dividend_date(date)
            else:
                # Projected earnings - most values unknown
                market_cap = None
                close_price = 0.0
                next_open_price = 0.0
                price_change_percent = 0.0
                volume_earnings_day = 0
                volume_next_day = 0
                moving_avg_200 = 0.0
                moving_avg_50 = 0.0
                week_52_high = 0.0
                week_52_low = 0.0
                short_interest_percent = 0.0
                dividend_yield = 0.0
                ex_dividend_date = None
            
            return EarningsReport(
                date=date,
                market_cap=market_cap,
                close_price=close_price,
                next_open_price=next_open_price,
                price_change_percent=price_change_percent,
                beat_or_miss=beat_or_miss,
                estimated_eps=estimated_eps,
                reported_eps=reported_eps,
                volume_earnings_day=volume_earnings_day,
                volume_next_day=volume_next_day,
                moving_avg_200=moving_avg_200,
                moving_avg_50=moving_avg_50,
                week_52_high=week_52_high,
                week_52_low=week_52_low,
                short_interest_percent=short_interest_percent,
                dividend_yield=dividend_yield,
                ex_dividend_date=ex_dividend_date,
                is_historical=is_historical
            )
            
        except Exception as e:
            logger.warning(f"Error creating earnings report: {e}")
            return None
    
    def _estimate_ex_dividend_date(self, earnings_date: str) -> Optional[str]:
        """Estimate ex-dividend date near earnings date."""
        try:
            if not earnings_date:
                return None
            
            # Simple estimation: add 2 weeks to earnings date
            earnings_dt = datetime.strptime(earnings_date, '%Y-%m-%d')
            ex_div_dt = earnings_dt.replace(day=min(earnings_dt.day + 14, 28))
            return ex_div_dt.strftime('%Y-%m-%d')
        except:
            return None
    
    def process_company(self, company_info: Dict) -> bool:
        """Process a single company's earnings data."""
        symbol = company_info.get('symbol', '').upper()
        if not symbol:
            logger.warning("Company missing symbol, skipping")
            return False
        
        logger.info(f"Processing {symbol} - {company_info.get('company_name', 'Unknown')}")
        
        # Check if file already exists
        output_file = self.output_dir / f"{symbol}.json"
        if output_file.exists():
            logger.info(f"Earnings data for {symbol} already exists, skipping")
            return True
        
        try:
            # Scrape earnings data
            scraped_data = self.scraper.scrape_company_earnings(symbol)
            if not scraped_data:
                logger.warning(f"Failed to scrape data for {symbol}")
                return False
            
            # Process and structure the data
            company_earnings = self.process_scraped_data(scraped_data, company_info)
            if not company_earnings:
                logger.warning(f"Failed to process data for {symbol}")
                return False
            
            # Save to JSON file
            company_earnings.save_to_file(str(output_file))
            logger.info(f"Saved earnings data for {symbol} to {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing company {symbol}: {e}")
            return False
    
    def process_all_companies(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Process all S&P 500 companies."""
        companies = self.load_sp500_companies()
        if not companies:
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
        
        # Limit processing for testing
        if limit:
            companies = companies[:limit]
            logger.info(f"Processing limited to first {limit} companies")
        
        stats = {"total": len(companies), "success": 0, "failed": 0, "skipped": 0}
        
        for i, company in enumerate(companies, 1):
            symbol = company.get('symbol', 'Unknown')
            logger.info(f"Processing {i}/{len(companies)}: {symbol}")
            
            try:
                success = self.process_company(company)
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    
            except KeyboardInterrupt:
                logger.info("Processing interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error processing {symbol}: {e}")
                stats["failed"] += 1
        
        # Log final statistics
        logger.info(f"Processing complete: {stats}")
        return stats
    
    def get_processing_status(self) -> Dict[str, int]:
        """Get current processing status."""
        companies = self.load_sp500_companies()
        total_companies = len(companies)
        
        # Count existing files
        processed_files = list(self.output_dir.glob("*.json"))
        processed_count = len(processed_files)
        
        return {
            "total_companies": total_companies,
            "processed": processed_count,
            "remaining": total_companies - processed_count,
            "percentage_complete": (processed_count / total_companies * 100) if total_companies > 0 else 0
        }


if __name__ == "__main__":
    # Demo usage
    processor = EarningsDataProcessor()
    
    # Show current status
    status = processor.get_processing_status()
    print(f"Processing Status: {status}")
    
    # Process a few companies for testing
    print("\nProcessing first 3 companies as test...")
    result = processor.process_all_companies(limit=3)
    print(f"Test processing result: {result}")