#!/usr/bin/env python3
"""
Earnings Data Curator

Curates earnings data from NASDAQ for individual stocks, lists of symbols,
or batch processing of all S&P 500 companies according to the earnings template schema.

Usage:
    python earnings_curator.py --symbol AAPL
    python earnings_curator.py --symbols AAPL,MSFT,GOOGL
    python earnings_curator.py --batch-sp500
    python earnings_curator.py --symbols-file symbols.txt
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import time

from improved_nasdaq_scraper import ImprovedNASDAQScraper
from earnings_data_models import CompanyEarningsData, EarningsReport
from sp500_processor import SP500Processor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('earnings_curator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EarningsCurator:
    """Main earnings data curator application"""
    
    def __init__(self, output_dir: str = "curated_earnings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.scraper = ImprovedNASDAQScraper()
        self.sp500_processor = SP500Processor()
        
        self.processed_count = 0
        self.failed_count = 0
        self.failed_symbols = []
    
    def curate_single_symbol(self, symbol: str) -> bool:
        """Curate earnings data for a single symbol"""
        logger.info(f"Curating earnings data for {symbol}")
        
        try:
            # Get company info if available
            company_info = self.sp500_processor.get_company_info(symbol)
            
            # Scrape earnings data from NASDAQ
            earnings_data = self.scraper.scrape_symbol_earnings(symbol)
            
            if not earnings_data:
                logger.warning(f"No earnings data found for {symbol}")
                return False
            
            # Create company earnings data structure
            company_earnings = self._create_company_earnings_data(symbol, earnings_data, company_info)
            
            # Save to JSON file
            self._save_earnings_data(symbol, company_earnings)
            
            self.processed_count += 1
            logger.info(f"Successfully curated {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error curating {symbol}: {e}")
            self.failed_count += 1
            self.failed_symbols.append(symbol)
            return False
    
    def curate_symbol_list(self, symbols: List[str]) -> Dict[str, bool]:
        """Curate earnings data for a list of symbols"""
        results = {}
        total_symbols = len(symbols)
        
        logger.info(f"Curating earnings data for {total_symbols} symbols")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {i}/{total_symbols}: {symbol}")
            
            success = self.curate_single_symbol(symbol)
            results[symbol] = success
            
            # Rate limiting between requests
            if i < total_symbols:
                time.sleep(2)
        
        return results
    
    def curate_sp500_batch(self, limit: Optional[int] = None) -> Dict[str, bool]:
        """Curate earnings data for all S&P 500 companies"""
        logger.info("Starting S&P 500 batch curation")
        
        # Load S&P 500 companies
        sp500_companies = self.sp500_processor.load_sp500_companies()
        
        if limit:
            sp500_companies = sp500_companies[:limit]
            logger.info(f"Limited to first {limit} companies")
        
        symbols = [company['symbol'] for company in sp500_companies]
        
        return self.curate_symbol_list(symbols)
    
    def curate_from_file(self, file_path: str) -> Dict[str, bool]:
        """Curate earnings data from a file containing symbols"""
        try:
            with open(file_path, 'r') as f:
                symbols = [line.strip().upper() for line in f if line.strip()]
            
            logger.info(f"Loaded {len(symbols)} symbols from {file_path}")
            return self.curate_symbol_list(symbols)
            
        except Exception as e:
            logger.error(f"Error reading symbols file {file_path}: {e}")
            return {}
    
    def _create_company_earnings_data(self, symbol: str, earnings_data: Dict[str, Any], 
                                    company_info: Optional[Dict[str, Any]]) -> CompanyEarningsData:
        """Create CompanyEarningsData structure from scraped data"""
        
        # Extract company information from multiple sources
        scraped_company_info = earnings_data.get('company_info', {})
        
        # Prioritize scraped data, fallback to S&P 500 data
        company_name = (scraped_company_info.get('company_name') or 
                       (company_info.get('company_name', '') if company_info else ''))
        sector = (scraped_company_info.get('sector') or 
                 (company_info.get('gics_sector', '') if company_info else ''))
        sub_sector = (scraped_company_info.get('sub_sector') or 
                     (company_info.get('gics_sub_industry', '') if company_info else ''))
        
        # Separate historical and projected reports
        historical_reports = []
        projected_reports = []
        
        for report_data in earnings_data.get('earnings_reports', []):
            report = EarningsReport(
                symbol=symbol,
                earnings_date=report_data.get('earnings_date', ''),
                quarter=report_data.get('quarter', 0),
                year=report_data.get('year', 0),
                actual_eps=report_data.get('actual_eps'),
                estimated_eps=report_data.get('estimated_eps'),
                beat_miss_meet=report_data.get('beat_miss_meet', ''),
                surprise_percent=report_data.get('surprise_percent'),
                revenue_billions=report_data.get('revenue_billions'),
                revenue_growth_percent=report_data.get('revenue_growth_percent'),
                consensus_rating=report_data.get('consensus_rating', ''),
                confidence_score=report_data.get('confidence_score', 0.7),
                source_url=f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings",
                data_verified_date=date.today().isoformat(),
                stock_price_on_date=report_data.get('stock_price_on_date'),
                announcement_time=report_data.get('announcement_time', ''),
                volume=report_data.get('volume'),
                date_earnings_report=report_data.get('earnings_date', ''),
                market_cap=report_data.get('market_cap'),
                price_at_close_earnings_report_date=report_data.get('price_at_close_earnings_report_date'),
                price_at_open_day_after_earnings_report_date=report_data.get('price_at_open_day_after_earnings_report_date'),
                percentage_stock_change=report_data.get('percentage_stock_change'),
                earnings_report_result=report_data.get('beat_miss_meet', ''),
                estimated_earnings_per_share=report_data.get('estimated_eps'),
                reported_earnings_per_share=report_data.get('actual_eps'),
                volume_day_of_earnings_report=report_data.get('volume_day_of_earnings_report'),
                volume_day_after_earnings_report=report_data.get('volume_day_after_earnings_report'),
                moving_avg_200_day=report_data.get('moving_avg_200_day'),
                moving_avg_50_day=report_data.get('moving_avg_50_day'),
                week_52_high=report_data.get('week_52_high'),
                week_52_low=report_data.get('week_52_low'),
                market_sector=sector,
                market_sub_sector=sub_sector,
                percentage_short_interest=report_data.get('percentage_short_interest'),
                dividend_yield=report_data.get('dividend_yield'),
                ex_dividend_date=report_data.get('ex_dividend_date', '')
            )
            
            # Determine if historical or projected based on actual_eps
            if report.actual_eps is not None:
                historical_reports.append(report)
            else:
                projected_reports.append(report)
        
        return CompanyEarningsData(
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            sub_sector=sub_sector,
            historical_reports=historical_reports,
            projected_reports=projected_reports,
            last_updated=datetime.now().isoformat(),
            data_source="nasdaq.com"
        )
    
    def _save_earnings_data(self, symbol: str, company_earnings: CompanyEarningsData):
        """Save company earnings data to JSON file"""
        filename = self.output_dir / f"{symbol}.json"
        
        try:
            # Convert to dictionary
            data_dict = company_earnings.to_dict()
            
            # Save to file with proper formatting
            with open(filename, 'w') as f:
                json.dump(data_dict, f, indent=2, default=str)
            
            logger.info(f"Saved earnings data for {symbol} to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving earnings data for {symbol}: {e}")
            raise
    
    def generate_summary_report(self):
        """Generate a summary report of the curation process"""
        summary = {
            'curation_summary': {
                'total_processed': self.processed_count,
                'successful': self.processed_count,
                'failed': self.failed_count,
                'success_rate': round((self.processed_count / max(1, self.processed_count + self.failed_count)) * 100, 2)
            },
            'failed_symbols': self.failed_symbols,
            'output_directory': str(self.output_dir),
            'generated_at': datetime.now().isoformat()
        }
        
        summary_file = self.output_dir / 'curation_summary.json'
        
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Summary report saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error saving summary report: {e}")
        
        # Log summary to console
        logger.info("="*50)
        logger.info("CURATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total Processed: {summary['curation_summary']['total_processed']}")
        logger.info(f"Success Rate: {summary['curation_summary']['success_rate']}%")
        if self.failed_symbols:
            logger.info(f"Failed Symbols: {', '.join(self.failed_symbols)}")
        logger.info("="*50)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Curate earnings data from NASDAQ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Curate single symbol
    python earnings_curator.py --symbol AAPL
    
    # Curate multiple symbols
    python earnings_curator.py --symbols AAPL,MSFT,GOOGL
    
    # Curate all S&P 500 companies
    python earnings_curator.py --batch-sp500
    
    # Curate from file
    python earnings_curator.py --symbols-file my_symbols.txt
    
    # Limit batch processing
    python earnings_curator.py --batch-sp500 --limit 50
        """
    )
    
    # Mutually exclusive group for input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument(
        '--symbol',
        type=str,
        help='Single stock symbol to curate (e.g., AAPL)'
    )
    
    input_group.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of symbols to curate (e.g., AAPL,MSFT,GOOGL)'
    )
    
    input_group.add_argument(
        '--batch-sp500',
        action='store_true',
        help='Curate all S&P 500 companies'
    )
    
    input_group.add_argument(
        '--symbols-file',
        type=str,
        help='File containing symbols (one per line) to curate'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='curated_earnings',
        help='Output directory for JSON files (default: curated_earnings)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of symbols to process (useful for testing)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create curator
    curator = EarningsCurator(output_dir=args.output_dir)
    
    try:
        # Process based on input type
        if args.symbol:
            # Single symbol
            success = curator.curate_single_symbol(args.symbol.upper())
            if not success:
                sys.exit(1)
        
        elif args.symbols:
            # Multiple symbols
            symbols = [s.strip().upper() for s in args.symbols.split(',')]
            if args.limit:
                symbols = symbols[:args.limit]
            
            results = curator.curate_symbol_list(symbols)
            
            # Check if any failed
            if not all(results.values()):
                logger.warning("Some symbols failed to process")
        
        elif args.batch_sp500:
            # Batch S&P 500
            results = curator.curate_sp500_batch(limit=args.limit)
            
            # Log results
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            logger.info(f"Batch processing complete: {successful}/{total} successful")
        
        elif args.symbols_file:
            # From file
            results = curator.curate_from_file(args.symbols_file)
            if args.limit:
                # Apply limit to file results
                limited_results = {}
                for i, (symbol, result) in enumerate(results.items()):
                    if i >= args.limit:
                        break
                    limited_results[symbol] = result
                results = limited_results
            
            if not results:
                logger.error("No symbols processed from file")
                sys.exit(1)
        
        # Generate summary report
        curator.generate_summary_report()
        
        logger.info("Curation completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Curation interrupted by user")
        curator.generate_summary_report()
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        curator.generate_summary_report()
        sys.exit(1)


if __name__ == "__main__":
    main()