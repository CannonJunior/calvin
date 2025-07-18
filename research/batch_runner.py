"""
Batch processing script for S&P 500 earnings research.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from data_processor import EarningsDataProcessor


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('earnings_research.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main batch processing function."""
    parser = argparse.ArgumentParser(description="S&P 500 Earnings Research Batch Processor")
    parser.add_argument("--limit", type=int, help="Limit number of companies to process")
    parser.add_argument("--output-dir", default="earnings_data", help="Output directory for JSON files")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--dry-run", action="store_true", help="Show status without processing")
    parser.add_argument("--resume", action="store_true", help="Resume processing (skip existing files)")
    parser.add_argument("--force", action="store_true", help="Force reprocess existing files")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting S&P 500 Earnings Research Batch Processing")
    logger.info(f"Arguments: {args}")
    
    # Initialize processor
    processor = EarningsDataProcessor(output_dir=args.output_dir)
    
    # Show current status
    status = processor.get_processing_status()
    logger.info(f"Current Status: {status}")
    
    if args.dry_run:
        logger.info("Dry run mode - exiting without processing")
        return
    
    # Check if resume mode and all files exist
    if args.resume and status["remaining"] == 0:
        logger.info("All companies already processed. Use --force to reprocess.")
        return
    
    # Process companies
    start_time = time.time()
    
    try:
        result = processor.process_all_companies(limit=args.limit)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Batch processing completed in {duration:.2f} seconds")
        logger.info(f"Final Results: {result}")
        
        # Calculate success rate
        if result["total"] > 0:
            success_rate = (result["success"] / result["total"]) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        
    except KeyboardInterrupt:
        logger.info("Batch processing interrupted by user")
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()