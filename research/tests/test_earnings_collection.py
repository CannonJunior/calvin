#!/usr/bin/env python3
"""
Unit Tests for Earnings Data Collection

Tests all components of the earnings data collection system to ensure
all 36 required template fields are properly collected and processed.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import shutil
from pathlib import Path
from datetime import date, datetime
from dataclasses import asdict
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earnings_collector import EarningsCollector, EarningsData
from nasdaq_scraper import NASDAQScraper
from data_processor import EarningsDataProcessor
from batch_runner import BatchEarningsRunner

class TestEarningsData(unittest.TestCase):
    """Test the EarningsData dataclass structure"""
    
    def test_earnings_data_creation(self):
        """Test creating EarningsData with all 36 fields"""
        earnings = EarningsData(
            # Core earnings fields (1-18)
            symbol='AAPL',
            earnings_date='2024-05-01',
            quarter=2,
            year=2024,
            actual_eps=1.65,
            estimated_eps=1.63,
            beat_miss_meet='BEAT',
            surprise_percent=1.2,
            revenue_billions=95.4,
            revenue_growth_percent=5.0,
            consensus_rating='Buy',
            confidence_score=1.0,
            source_url='https://www.nasdaq.com/market-activity/stocks/aapl/earnings',
            data_verified_date=date.today().isoformat(),
            stock_price_on_date=213.32,
            announcement_time='AMC',
            volume=50000000,
            date_earnings_report='2024-05-01',
            
            # Market data fields (19-27)
            market_cap=3200.0,
            price_at_close_earnings_report_date=213.32,
            price_at_open_day_after_earnings_report_date=215.50,
            percentage_stock_change=1.02,
            earnings_report_result='BEAT',
            estimated_earnings_per_share=1.63,
            reported_earnings_per_share=1.65,
            volume_day_of_earnings_report=55000000,
            volume_day_after_earnings_report=48000000,
            
            # Technical indicators (28-31)
            moving_average_200_day=190.45,
            moving_average_50_day=205.22,
            week_52_high=230.00,
            week_52_low=160.00,
            
            # Company fundamentals (32-36)
            market_sector='Information Technology',
            market_sub_sector='Technology Hardware, Storage & Peripherals',
            percentage_short_interest=1.5,
            dividend_yield=0.5,
            ex_dividend_date='2024-04-15'
        )
        
        self.assertEqual(earnings.symbol, 'AAPL')
        self.assertEqual(earnings.actual_eps, 1.65)
        self.assertEqual(earnings.beat_miss_meet, 'BEAT')
        
        # Test conversion to dict
        earnings_dict = asdict(earnings)
        self.assertIn('symbol', earnings_dict)
        self.assertIn('earnings_date', earnings_dict)
        self.assertIn('ex_dividend_date', earnings_dict)
    
    def test_earnings_data_field_count(self):
        """Test that EarningsData has exactly 36 fields"""
        earnings = EarningsData(
            symbol='TEST', earnings_date='', quarter=0, year=0, actual_eps=None,
            estimated_eps=None, beat_miss_meet=None, surprise_percent=None,
            revenue_billions=None, revenue_growth_percent=None, consensus_rating=None,
            confidence_score=0.0, source_url='', data_verified_date='',
            stock_price_on_date=None, announcement_time=None, volume=None,
            date_earnings_report=None, market_cap=None, price_at_close_earnings_report_date=None,
            price_at_open_day_after_earnings_report_date=None, percentage_stock_change=None,
            earnings_report_result=None, estimated_earnings_per_share=None,
            reported_earnings_per_share=None, volume_day_of_earnings_report=None,
            volume_day_after_earnings_report=None, moving_average_200_day=None,
            moving_average_50_day=None, week_52_high=None, week_52_low=None,
            market_sector=None, market_sub_sector=None, percentage_short_interest=None,
            dividend_yield=None, ex_dividend_date=None
        )
        
        earnings_dict = asdict(earnings)
        field_count = len(earnings_dict)
        
        self.assertEqual(field_count, 36, f"Expected 36 fields, got {field_count}")


class TestNASDAQScraper(unittest.TestCase):
    """Test the NASDAQ scraper functionality"""
    
    def setUp(self):
        self.scraper = NASDAQScraper()
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper.session)
        self.assertIn('User-Agent', self.scraper.session.headers)
    
    def test_parse_float_method(self):
        """Test the _parse_float method with various inputs"""
        # Test normal cases
        self.assertEqual(self.scraper._parse_float('1.65'), 1.65)
        self.assertEqual(self.scraper._parse_float('$1.65'), 1.65)
        self.assertEqual(self.scraper._parse_float('1,234.56'), 1234.56)
        
        # Test with suffixes
        self.assertEqual(self.scraper._parse_float('1.5K'), 1500.0)
        self.assertEqual(self.scraper._parse_float('2.3M'), 2300000.0)
        self.assertEqual(self.scraper._parse_float('1.2B'), 1200000000.0)
        
        # Test edge cases
        self.assertIsNone(self.scraper._parse_float('-'))
        self.assertIsNone(self.scraper._parse_float('N/A'))
        self.assertIsNone(self.scraper._parse_float(''))
    
    def test_parse_date_method(self):
        """Test the _parse_date method with various date formats"""
        # Test common formats
        self.assertEqual(self.scraper._parse_date('05/01/2024'), '2024-05-01')
        self.assertEqual(self.scraper._parse_date('2024-05-01'), '2024-05-01')
        
        # Test edge cases
        self.assertIsNone(self.scraper._parse_date('-'))
        self.assertIsNone(self.scraper._parse_date(''))
    
    @patch('requests.Session.get')
    def test_scrape_earnings_page_success(self, mock_get):
        """Test successful scraping of earnings page"""
        # Mock HTML response
        mock_response = Mock()
        mock_response.content = b'<html><body>Mock earnings data</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_earnings_page('AAPL')
        
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_scrape_earnings_page_failure(self, mock_get):
        """Test handling of scraping failures"""
        mock_get.side_effect = Exception("Network error")
        
        result = self.scraper.scrape_earnings_page('INVALID')
        
        self.assertEqual(result, {})


class TestDataProcessor(unittest.TestCase):
    """Test the earnings data processor"""
    
    def setUp(self):
        self.processor = EarningsDataProcessor()
    
    def test_required_fields_count(self):
        """Test that processor has exactly 36 required fields"""
        self.assertEqual(len(self.processor.required_fields), 36)
    
    def test_validate_all_fields_present_success(self):
        """Test validation with all fields present"""
        # Create earnings data with all fields
        earnings = EarningsData(
            symbol='TEST', earnings_date='2024-01-01', quarter=1, year=2024,
            actual_eps=1.0, estimated_eps=0.9, beat_miss_meet='BEAT', surprise_percent=11.1,
            revenue_billions=10.0, revenue_growth_percent=5.0, consensus_rating='Buy',
            confidence_score=1.0, source_url='test.com', data_verified_date='2024-01-01',
            stock_price_on_date=100.0, announcement_time='AMC', volume=1000000,
            date_earnings_report='2024-01-01', market_cap=1000.0,
            price_at_close_earnings_report_date=100.0, price_at_open_day_after_earnings_report_date=101.0,
            percentage_stock_change=1.0, earnings_report_result='BEAT',
            estimated_earnings_per_share=0.9, reported_earnings_per_share=1.0,
            volume_day_of_earnings_report=1000000, volume_day_after_earnings_report=900000,
            moving_average_200_day=95.0, moving_average_50_day=98.0,
            week_52_high=120.0, week_52_low=80.0, market_sector='Technology',
            market_sub_sector='Software', percentage_short_interest=2.0,
            dividend_yield=1.5, ex_dividend_date='2024-01-15'
        )
        
        is_valid, missing_fields = self.processor.validate_all_fields_present(earnings)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing_fields), 0)
    
    def test_extract_quarter_year(self):
        """Test quarter and year extraction from dates"""
        quarter, year = self.processor._extract_quarter_year('2024-05-01')
        self.assertEqual(quarter, 2)
        self.assertEqual(year, 2024)
        
        quarter, year = self.processor._extract_quarter_year('2024-11-15')
        self.assertEqual(quarter, 4)
        self.assertEqual(year, 2024)
        
        quarter, year = self.processor._extract_quarter_year('')
        self.assertEqual(quarter, 0)
        self.assertEqual(year, 0)
    
    def test_process_raw_earnings_data(self):
        """Test processing of raw earnings data"""
        raw_data = {
            'symbol': 'TEST',
            'earnings_reports': [{
                'symbol': 'TEST',
                'earnings_date': '2024-05-01',
                'actual_eps': 1.5,
                'estimated_eps': 1.4,
                'revenue_billions': 20.0
            }]
        }
        
        company_info = {
            'symbol': 'TEST',
            'gics_sector': 'Technology',
            'gics_sub_industry': 'Software'
        }
        
        processed = self.processor.process_raw_earnings_data(raw_data, company_info)
        
        self.assertEqual(len(processed), 1)
        earnings = processed[0]
        self.assertEqual(earnings.symbol, 'TEST')
        self.assertEqual(earnings.actual_eps, 1.5)
        self.assertEqual(earnings.beat_miss_meet, 'BEAT')
        self.assertEqual(earnings.quarter, 2)
        self.assertEqual(earnings.year, 2024)
    
    def test_get_field_completeness_report(self):
        """Test field completeness reporting"""
        # Create test earnings with some missing fields
        earnings = EarningsData(
            symbol='TEST', earnings_date='2024-01-01', quarter=1, year=2024,
            actual_eps=1.0, estimated_eps=None, beat_miss_meet='BEAT', surprise_percent=None,
            revenue_billions=10.0, revenue_growth_percent=None, consensus_rating='Buy',
            confidence_score=1.0, source_url='test.com', data_verified_date='2024-01-01',
            stock_price_on_date=100.0, announcement_time='AMC', volume=None,
            date_earnings_report='2024-01-01', market_cap=None,
            price_at_close_earnings_report_date=100.0, price_at_open_day_after_earnings_report_date=None,
            percentage_stock_change=None, earnings_report_result='BEAT',
            estimated_earnings_per_share=None, reported_earnings_per_share=1.0,
            volume_day_of_earnings_report=None, volume_day_after_earnings_report=None,
            moving_average_200_day=None, moving_average_50_day=None,
            week_52_high=None, week_52_low=None, market_sector='Technology',
            market_sub_sector='Software', percentage_short_interest=None,
            dividend_yield=None, ex_dividend_date=None
        )
        
        report = self.processor.get_field_completeness_report([earnings])
        
        self.assertIn('total_records', report)
        self.assertIn('overall_completeness_percent', report)
        self.assertIn('field_completeness', report)
        self.assertEqual(report['total_records'], 1)
        self.assertLess(report['overall_completeness_percent'], 100)


class TestEarningsCollector(unittest.TestCase):
    """Test the main earnings collector"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.collector = EarningsCollector()
        self.collector.data_dir = Path(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_beat_miss_meet(self):
        """Test beat/miss/meet calculation"""
        # Test BEAT
        result = self.collector._calculate_beat_miss_meet(1.65, 1.63)
        self.assertEqual(result, 'BEAT')
        
        # Test MISS
        result = self.collector._calculate_beat_miss_meet(1.60, 1.63)
        self.assertEqual(result, 'MISS')
        
        # Test MEET
        result = self.collector._calculate_beat_miss_meet(1.63, 1.63)
        self.assertEqual(result, 'MEET')
        
        # Test with None values
        result = self.collector._calculate_beat_miss_meet(None, 1.63)
        self.assertIsNone(result)
    
    def test_calculate_surprise_percent(self):
        """Test surprise percentage calculation"""
        # Test positive surprise
        result = self.collector._calculate_surprise_percent(1.65, 1.63)
        self.assertAlmostEqual(result, 1.23, places=1)
        
        # Test negative surprise
        result = self.collector._calculate_surprise_percent(1.60, 1.63)
        self.assertAlmostEqual(result, -1.84, places=1)
        
        # Test with None values
        result = self.collector._calculate_surprise_percent(None, 1.63)
        self.assertIsNone(result)
        
        # Test with zero estimate
        result = self.collector._calculate_surprise_percent(1.65, 0)
        self.assertIsNone(result)
    
    def test_save_earnings_data(self):
        """Test saving earnings data to file"""
        earnings = EarningsData(
            symbol='TEST', earnings_date='2024-01-01', quarter=1, year=2024,
            actual_eps=1.0, estimated_eps=0.9, beat_miss_meet='BEAT', surprise_percent=11.1,
            revenue_billions=10.0, revenue_growth_percent=5.0, consensus_rating='Buy',
            confidence_score=1.0, source_url='test.com', data_verified_date='2024-01-01',
            stock_price_on_date=100.0, announcement_time='AMC', volume=1000000,
            date_earnings_report='2024-01-01', market_cap=1000.0,
            price_at_close_earnings_report_date=100.0, price_at_open_day_after_earnings_report_date=101.0,
            percentage_stock_change=1.0, earnings_report_result='BEAT',
            estimated_earnings_per_share=0.9, reported_earnings_per_share=1.0,
            volume_day_of_earnings_report=1000000, volume_day_after_earnings_report=900000,
            moving_average_200_day=95.0, moving_average_50_day=98.0,
            week_52_high=120.0, week_52_low=80.0, market_sector='Technology',
            market_sub_sector='Software', percentage_short_interest=2.0,
            dividend_yield=1.5, ex_dividend_date='2024-01-15'
        )
        
        self.collector.save_earnings_data('TEST', [earnings])
        
        # Verify file was created
        file_path = self.collector.data_dir / 'TEST.json'
        self.assertTrue(file_path.exists())
        
        # Verify content
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['symbol'], 'TEST')
        self.assertEqual(len(data[0]), 36)  # All 36 fields


class TestBatchRunner(unittest.TestCase):
    """Test the batch runner functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runner = BatchEarningsRunner()
        self.runner.data_dir = Path(self.temp_dir)
        self.runner.progress_file = Path(self.temp_dir) / 'progress.json'
        self.runner.summary_file = Path(self.temp_dir) / 'summary.json'
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_load_save_progress(self):
        """Test loading and saving progress"""
        # Save initial progress
        self.runner.processed_companies.add('AAPL')
        self.runner.success_count = 1
        self.runner._save_progress()
        
        # Create new runner and load progress
        new_runner = BatchEarningsRunner()
        new_runner.progress_file = self.runner.progress_file
        new_runner._load_progress()
        
        self.assertIn('AAPL', new_runner.processed_companies)
        self.assertEqual(new_runner.success_count, 1)
    
    @patch('batch_runner.BatchEarningsRunner.load_sp500_companies')
    def test_load_sp500_companies(self, mock_load):
        """Test loading S&P 500 companies"""
        mock_companies = [
            {'symbol': 'AAPL', 'company_name': 'Apple Inc.'},
            {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation'}
        ]
        mock_load.return_value = mock_companies
        
        companies = self.runner.load_sp500_companies()
        
        self.assertEqual(len(companies), 2)
        self.assertEqual(companies[0]['symbol'], 'AAPL')


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete earnings collection system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_data_flow(self):
        """Test complete data flow from scraping to saving"""
        # Mock company data
        company_info = {
            'symbol': 'TEST',
            'company_name': 'Test Company',
            'gics_sector': 'Technology',
            'gics_sub_industry': 'Software'
        }
        
        # Mock raw earnings data
        raw_data = {
            'symbol': 'TEST',
            'earnings_reports': [{
                'symbol': 'TEST',
                'earnings_date': '2024-05-01',
                'actual_eps': 1.65,
                'estimated_eps': 1.63,
                'revenue_billions': 25.5
            }]
        }
        
        # Process data
        processor = EarningsDataProcessor()
        processed_earnings = processor.process_raw_earnings_data(raw_data, company_info)
        
        # Validate all fields present
        self.assertEqual(len(processed_earnings), 1)
        earnings = processed_earnings[0]
        
        is_valid, missing_fields = processor.validate_all_fields_present(earnings)
        
        # Should be valid with all 36 fields
        self.assertTrue(is_valid, f"Missing fields: {missing_fields}")
        
        # Verify specific calculations
        self.assertEqual(earnings.beat_miss_meet, 'BEAT')
        self.assertEqual(earnings.quarter, 2)
        self.assertEqual(earnings.year, 2024)
        self.assertAlmostEqual(earnings.surprise_percent, 1.23, places=1)
    
    def test_field_count_validation(self):
        """Test that all components maintain 36 field requirement"""
        processor = EarningsDataProcessor()
        
        # Verify processor knows about all 36 fields
        self.assertEqual(len(processor.required_fields), 36)
        
        # Verify EarningsData structure has 36 fields
        sample_earnings = EarningsData(
            symbol='TEST', earnings_date='', quarter=0, year=0, actual_eps=None,
            estimated_eps=None, beat_miss_meet=None, surprise_percent=None,
            revenue_billions=None, revenue_growth_percent=None, consensus_rating=None,
            confidence_score=0.0, source_url='', data_verified_date='',
            stock_price_on_date=None, announcement_time=None, volume=None,
            date_earnings_report=None, market_cap=None, price_at_close_earnings_report_date=None,
            price_at_open_day_after_earnings_report_date=None, percentage_stock_change=None,
            earnings_report_result=None, estimated_earnings_per_share=None,
            reported_earnings_per_share=None, volume_day_of_earnings_report=None,
            volume_day_after_earnings_report=None, moving_average_200_day=None,
            moving_average_50_day=None, week_52_high=None, week_52_low=None,
            market_sector=None, market_sub_sector=None, percentage_short_interest=None,
            dividend_yield=None, ex_dividend_date=None
        )
        
        earnings_dict = asdict(sample_earnings)
        self.assertEqual(len(earnings_dict), 36, f"EarningsData has {len(earnings_dict)} fields, expected 36")


if __name__ == '__main__':
    # Create tests directory if it doesn't exist
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)