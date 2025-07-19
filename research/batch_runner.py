#!/usr/bin/env python3
"""
Batch Runner for S&P 500 Earnings Data Collection

Processes all S&P 500 companies to collect earnings data with all 36 required fields.
Includes progress tracking, error handling, and resumption capabilities.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import sys
import signal
from dataclasses import asdict

from earnings_collector import EarningsCollector, EarningsData
from nasdaq_scraper import NASDAQScraper
from data_processor import EarningsDataProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('earnings_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BatchEarningsRunner:
    """Batch processor for collecting earnings data from all S&P 500 companies"""
    
    def __init__(self):
        self.collector = EarningsCollector()
        self.scraper = NASDAQScraper()
        self.processor = EarningsDataProcessor()
        
        self.data_dir = Path("earnings_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.progress_file = Path("batch_progress.json")
        self.summary_file = Path("collection_summary.json")
        
        self.processed_companies = set()
        self.failed_companies = []
        self.success_count = 0
        self.error_count = 0
        
        # Load existing progress
        self._load_progress()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.should_stop = False
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.should_stop = True
        self._save_progress()
    
    def _load_progress(self):
        """Load previous progress from file"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                
                self.processed_companies = set(progress.get('processed_companies', []))
                self.failed_companies = progress.get('failed_companies', [])
                self.success_count = progress.get('success_count', 0)
                self.error_count = progress.get('error_count', 0)
                
                logger.info(f"Loaded progress: {len(self.processed_companies)} processed, "
                           f"{self.success_count} successful, {self.error_count} failed")
                
            except Exception as e:
                logger.error(f"Error loading progress: {e}")
    
    def _save_progress(self):
        """Save current progress to file"""
        progress = {
            'processed_companies': list(self.processed_companies),
            'failed_companies': self.failed_companies,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            logger.info("Progress saved")
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def load_sp500_companies(self) -> List[Dict[str, Any]]:
        """Load S&P 500 companies from JSON file"""
        try:
            with open("sp500_companies.json", "r") as f:
                companies = json.load(f)
            logger.info(f"Loaded {len(companies)} S&P 500 companies")
            return companies
        except Exception as e:
            logger.error(f"Error loading S&P 500 companies: {e}")
            return []
    
    def process_single_company(self, company_info: Dict[str, Any]) -> bool:
        """Process earnings data for a single company"""
        symbol = company_info['symbol']
        
        if symbol in self.processed_companies:
            logger.info(f"Skipping {symbol} - already processed")
            return True
        
        logger.info(f"Processing {symbol} - {company_info.get('company_name', 'Unknown')}")
        
        try:
            # Step 1: Scrape NASDAQ data
            raw_data = self.scraper.scrape_earnings_page(symbol)
            
            if not raw_data or not raw_data.get('earnings_reports'):
                logger.warning(f"No earnings data found for {symbol}")
                # Create minimal record to avoid re-processing
                raw_data = {
                    'symbol': symbol,
                    'earnings_reports': []
                }
            
            # Step 2: Process and validate data
            processed_earnings = self.processor.process_raw_earnings_data(raw_data, company_info)
            
            # Step 3: Validate all records have 36 fields
            all_valid = True
            for earnings in processed_earnings:
                is_valid, missing_fields = self.processor.validate_all_fields_present(earnings)
                if not is_valid:
                    logger.error(f"CRITICAL: {symbol} missing fields: {missing_fields}")
                    all_valid = False
            
            if not all_valid:
                logger.error(f"VALIDATION FAILED for {symbol} - not all 36 fields present")
                self.failed_companies.append({
                    'symbol': symbol,
                    'error': 'Missing required fields',
                    'timestamp': datetime.now().isoformat()
                })
                self.error_count += 1
                return False
            
            # Step 4: Save earnings data
            self._save_company_earnings(symbol, processed_earnings)
            
            # Step 5: Generate completeness report
            if processed_earnings:
                completeness_report = self.processor.get_field_completeness_report(processed_earnings)
                logger.info(f"{symbol} completeness: {completeness_report['overall_completeness_percent']}%")
            
            self.processed_companies.add(symbol)
            self.success_count += 1
            
            logger.info(f"Successfully processed {symbol} with {len(processed_earnings)} earnings records")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            self.failed_companies.append({
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.error_count += 1
            return False
    
    def _save_company_earnings(self, symbol: str, earnings_list: List[EarningsData]):
        """Save earnings data for a company to JSON file"""
        filename = self.data_dir / f"{symbol}.json"
        
        # Convert EarningsData objects to dictionaries
        data = []
        for earnings in earnings_list:
            earnings_dict = asdict(earnings)
            # Ensure all 36 fields are present
            for field in self.processor.required_fields:
                if field not in earnings_dict:
                    earnings_dict[field] = None
            data.append(earnings_dict)
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(data)} earnings records for {symbol}")
        except Exception as e:
            logger.error(f"Error saving earnings data for {symbol}: {e}")
            raise
    
    def run_batch_processing(self, limit: Optional[int] = None, 
                           start_from: Optional[str] = None):
        """Run batch processing for all S&P 500 companies"""
        companies = self.load_sp500_companies()
        
        if not companies:
            logger.error("No companies to process")
            return
        
        # Filter companies if start_from is specified
        if start_from:
            start_idx = next((i for i, c in enumerate(companies) if c['symbol'] == start_from), 0)
            companies = companies[start_idx:]
            logger.info(f"Starting from {start_from} (index {start_idx})")
        
        # Apply limit if specified
        if limit:
            companies = companies[:limit]
            logger.info(f"Processing limited to {limit} companies")
        
        total_companies = len(companies)
        logger.info(f"Starting batch processing of {total_companies} companies")
        
        start_time = datetime.now()
        
        for i, company in enumerate(companies, 1):
            if self.should_stop:
                logger.info("Stopping due to shutdown signal")
                break
            
            symbol = company['symbol']
            logger.info(f"Progress: {i}/{total_companies} ({(i/total_companies)*100:.1f}%) - {symbol}")
            
            success = self.process_single_company(company)
            
            # Save progress every 10 companies
            if i % 10 == 0:
                self._save_progress()
            
            # Rate limiting - pause between requests
            time.sleep(2)
        
        # Final save
        self._save_progress()
        
        # Generate summary report
        self._generate_summary_report(start_time)
        
        logger.info(f"Batch processing completed. Success: {self.success_count}, "
                   f"Errors: {self.error_count}")
    
    def _generate_summary_report(self, start_time: datetime):
        """Generate summary report of the batch processing"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Count total earnings records
        total_earnings_records = 0
        companies_with_data = 0
        
        for earnings_file in self.data_dir.glob("*.json"):
            try:
                with open(earnings_file, 'r') as f:
                    data = json.load(f)
                    if data:
                        total_earnings_records += len(data)
                        companies_with_data += 1
            except Exception as e:
                logger.error(f"Error reading {earnings_file}: {e}")
        
        summary = {
            'batch_run_info': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'duration_hours': round(duration.total_seconds() / 3600, 2)
            },
            'processing_stats': {
                'total_companies_attempted': len(self.processed_companies) + len(self.failed_companies),
                'successful_companies': self.success_count,
                'failed_companies': self.error_count,
                'success_rate_percent': round((self.success_count / max(1, self.success_count + self.error_count)) * 100, 1)
            },
            'data_stats': {
                'companies_with_earnings_data': companies_with_data,
                'total_earnings_records': total_earnings_records,
                'avg_records_per_company': round(total_earnings_records / max(1, companies_with_data), 1)
            },
            'field_validation': {
                'required_fields_count': len(self.processor.required_fields),
                'required_fields': self.processor.required_fields
            },
            'failed_companies': self.failed_companies
        }
        
        try:
            with open(self.summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            logger.info(f"Summary report saved to {self.summary_file}")
        except Exception as e:
            logger.error(f"Error saving summary report: {e}")
        
        # Log key metrics
        logger.info("="*50)
        logger.info("BATCH PROCESSING SUMMARY")
        logger.info("="*50)
        logger.info(f"Duration: {summary['batch_run_info']['duration_hours']} hours")
        logger.info(f"Success Rate: {summary['processing_stats']['success_rate_percent']}%")
        logger.info(f"Companies Processed: {summary['processing_stats']['successful_companies']}")
        logger.info(f"Total Earnings Records: {summary['data_stats']['total_earnings_records']}")
        logger.info(f"Avg Records/Company: {summary['data_stats']['avg_records_per_company']}")
        logger.info("="*50)
    
    def validate_all_data(self):
        """Validate that all saved data contains the required 36 fields"""
        logger.info("Validating all saved earnings data...")
        
        validation_errors = []
        companies_validated = 0
        records_validated = 0
        
        for earnings_file in self.data_dir.glob("*.json"):
            symbol = earnings_file.stem
            companies_validated += 1
            
            try:
                with open(earnings_file, 'r') as f:
                    data = json.load(f)
                
                for i, record in enumerate(data):
                    records_validated += 1
                    missing_fields = []
                    
                    for required_field in self.processor.required_fields:
                        if required_field not in record:
                            missing_fields.append(required_field)
                    
                    if missing_fields:
                        validation_errors.append({
                            'symbol': symbol,
                            'record_index': i,
                            'missing_fields': missing_fields
                        })
                        logger.error(f"VALIDATION ERROR: {symbol} record {i} missing: {missing_fields}")
            
            except Exception as e:
                validation_errors.append({
                    'symbol': symbol,
                    'error': f"File read error: {e}"
                })
                logger.error(f"Error validating {symbol}: {e}")
        
        logger.info(f"Validation complete: {companies_validated} companies, "
                   f"{records_validated} records, {len(validation_errors)} errors")
        
        if validation_errors:
            logger.error(f"CRITICAL: {len(validation_errors)} validation errors found!")
            return False
        else:
            logger.info("SUCCESS: All data contains required 36 fields!")
            return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process S&P 500 earnings data')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    parser.add_argument('--start-from', type=str, help='Start processing from this symbol')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing data')
    
    args = parser.parse_args()
    
    runner = BatchEarningsRunner()
    
    if args.validate_only:
        runner.validate_all_data()
    else:
        runner.run_batch_processing(limit=args.limit, start_from=args.start_from)

if __name__ == "__main__":
    main()