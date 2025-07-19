#!/usr/bin/env python3
"""
Tests for the Earnings Curator Application

Tests all components of the new earnings curator that creates JSON files
according to the earnings template schema.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, date
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earnings_curator import EarningsCurator
from earnings_data_models import EarningsReport, CompanyEarningsData, EarningsReportBuilder
from nasdaq_data_scraper import NASDAQDataScraper
from sp500_processor import SP500Processor


class TestEarningsDataModels(unittest.TestCase):
    """Test the earnings data models"""
    
    def test_earnings_report_creation(self):
        """Test creating an EarningsReport with all fields"""
        report = EarningsReport(
            symbol="AAPL",
            earnings_date="2024-07-18",
            quarter=3,
            year=2024,
            actual_eps=1.73,
            estimated_eps=1.76,
            beat_miss_meet="MISS",
            surprise_percent=-1.7,
            revenue_billions=146.29,
            revenue_growth_percent=7.3,
            consensus_rating="Buy",
            confidence_score=1.0,
            source_url="https://www.nasdaq.com/market-activity/stocks/aapl/earnings",
            data_verified_date="2025-07-18",
            stock_price_on_date=153.42,
            announcement_time="BMO",
            volume=37563589,
            date_earnings_report="2024-07-18",
            market_cap=995967199.98,
            price_at_close_earnings_report_date=153.42,
            price_at_open_day_after_earnings_report_date=143.91,
            percentage_stock_change=-6.2,
            earnings_report_result="MISS",
            estimated_earnings_per_share=1.76,
            reported_earnings_per_share=1.73,
            volume_day_of_earnings_report=37563589,
            volume_day_after_earnings_report=36227374,
            moving_avg_200_day=132.33,
            moving_avg_50_day=160.84,
            week_52_high=175.32,
            week_52_low=116.97,
            market_sector="Information Technology",
            market_sub_sector="Technology Hardware",
            percentage_short_interest=3.55,
            dividend_yield=3.57,
            ex_dividend_date="2024-08-06"
        )
        
        self.assertEqual(report.symbol, "AAPL")
        self.assertEqual(report.beat_miss_meet, "MISS")
        self.assertFalse(report.is_projected())
        
        # Test dictionary conversion
        report_dict = report.to_dict()
        self.assertIn('symbol', report_dict)
        self.assertIn('earnings_date', report_dict)
        self.assertEqual(len(report_dict), 35)  # All fields should be present
    
    def test_earnings_report_projected(self):
        """Test projected earnings report"""
        report = EarningsReport(
            symbol="AAPL",
            earnings_date="2025-08-17",
            quarter=3,
            year=2025,
            actual_eps=None,
            estimated_eps=2.56,
            beat_miss_meet="PROJECTED",
            surprise_percent=None,
            revenue_billions=None,
            revenue_growth_percent=None,
            consensus_rating="Hold",
            confidence_score=0.7,
            source_url="https://www.nasdaq.com/market-activity/stocks/aapl/earnings",
            data_verified_date="2025-07-18",
            stock_price_on_date=68.23,
            announcement_time="BMO",
            volume=25680309,
            date_earnings_report="2025-08-17",
            market_cap=322576361.17,
            price_at_close_earnings_report_date=None,
            price_at_open_day_after_earnings_report_date=None,
            percentage_stock_change=None,
            earnings_report_result="PROJECTED",
            estimated_earnings_per_share=2.56,
            reported_earnings_per_share=None,
            volume_day_of_earnings_report=None,
            volume_day_after_earnings_report=None,
            moving_avg_200_day=59.39,
            moving_avg_50_day=70.9,
            week_52_high=78.07,
            week_52_low=49.77,
            market_sector="Information Technology",
            market_sub_sector="Technology Hardware",
            percentage_short_interest=2.57,
            dividend_yield=3.63,
            ex_dividend_date="2025-09-01"
        )
        
        self.assertTrue(report.is_projected())
        self.assertEqual(report.beat_miss_meet, "PROJECTED")
    
    def test_earnings_report_calculations(self):
        """Test earnings report calculations"""
        # Test beat calculation
        self.assertEqual(
            EarningsReport(symbol="TEST", earnings_date="", quarter=0, year=0,
                         actual_eps=1.5, estimated_eps=1.4, beat_miss_meet="", surprise_percent=None,
                         revenue_billions=None, revenue_growth_percent=None, consensus_rating="",
                         confidence_score=0.0, source_url="", data_verified_date="",
                         stock_price_on_date=None, announcement_time="", volume=None,
                         date_earnings_report="", market_cap=None, price_at_close_earnings_report_date=None,
                         price_at_open_day_after_earnings_report_date=None, percentage_stock_change=None,
                         earnings_report_result="", estimated_earnings_per_share=None,
                         reported_earnings_per_share=None, volume_day_of_earnings_report=None,
                         volume_day_after_earnings_report=None, moving_avg_200_day=None,
                         moving_avg_50_day=None, week_52_high=None, week_52_low=None,
                         market_sector="", market_sub_sector="", percentage_short_interest=None,
                         dividend_yield=None, ex_dividend_date="").determine_beat_miss_meet(),
            "BEAT"
        )
        
        # Test surprise calculation
        surprise = EarningsReport(symbol="TEST", earnings_date="", quarter=0, year=0,
                                actual_eps=1.5, estimated_eps=1.4, beat_miss_meet="", surprise_percent=None,
                                revenue_billions=None, revenue_growth_percent=None, consensus_rating="",
                                confidence_score=0.0, source_url="", data_verified_date="",
                                stock_price_on_date=None, announcement_time="", volume=None,
                                date_earnings_report="", market_cap=None, price_at_close_earnings_report_date=None,
                                price_at_open_day_after_earnings_report_date=None, percentage_stock_change=None,
                                earnings_report_result="", estimated_earnings_per_share=None,
                                reported_earnings_per_share=None, volume_day_of_earnings_report=None,
                                volume_day_after_earnings_report=None, moving_avg_200_day=None,
                                moving_avg_50_day=None, week_52_high=None, week_52_low=None,
                                market_sector="", market_sub_sector="", percentage_short_interest=None,
                                dividend_yield=None, ex_dividend_date="").calculate_surprise_percent()
        
        self.assertAlmostEqual(surprise, 7.14, places=1)
    
    def test_company_earnings_data(self):
        """Test CompanyEarningsData structure"""
        historical_reports = [
            EarningsReport(
                symbol="AAPL", earnings_date="2024-07-18", quarter=3, year=2024,
                actual_eps=1.73, estimated_eps=1.76, beat_miss_meet="MISS", surprise_percent=-1.7,
                revenue_billions=146.29, revenue_growth_percent=7.3, consensus_rating="Buy",
                confidence_score=1.0, source_url="test.com", data_verified_date="2025-07-18",
                stock_price_on_date=153.42, announcement_time="BMO", volume=37563589,
                date_earnings_report="2024-07-18", market_cap=995967199.98,
                price_at_close_earnings_report_date=153.42, price_at_open_day_after_earnings_report_date=143.91,
                percentage_stock_change=-6.2, earnings_report_result="MISS",
                estimated_earnings_per_share=1.76, reported_earnings_per_share=1.73,
                volume_day_of_earnings_report=37563589, volume_day_after_earnings_report=36227374,
                moving_avg_200_day=132.33, moving_avg_50_day=160.84,
                week_52_high=175.32, week_52_low=116.97, market_sector="Information Technology",
                market_sub_sector="Technology Hardware", percentage_short_interest=3.55,
                dividend_yield=3.57, ex_dividend_date="2024-08-06"
            )
        ]
        
        projected_reports = [
            EarningsReport(
                symbol="AAPL", earnings_date="2025-08-17", quarter=3, year=2025,
                actual_eps=None, estimated_eps=2.56, beat_miss_meet="PROJECTED", surprise_percent=None,
                revenue_billions=None, revenue_growth_percent=None, consensus_rating="Hold",
                confidence_score=0.7, source_url="test.com", data_verified_date="2025-07-18",
                stock_price_on_date=68.23, announcement_time="BMO", volume=25680309,
                date_earnings_report="2025-08-17", market_cap=322576361.17,
                price_at_close_earnings_report_date=None, price_at_open_day_after_earnings_report_date=None,
                percentage_stock_change=None, earnings_report_result="PROJECTED",
                estimated_earnings_per_share=2.56, reported_earnings_per_share=None,
                volume_day_of_earnings_report=None, volume_day_after_earnings_report=None,
                moving_avg_200_day=59.39, moving_avg_50_day=70.9,
                week_52_high=78.07, week_52_low=49.77, market_sector="Information Technology",
                market_sub_sector="Technology Hardware", percentage_short_interest=2.57,
                dividend_yield=3.63, ex_dividend_date="2025-09-01"
            )
        ]
        
        company_data = CompanyEarningsData(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Information Technology",
            sub_sector="Technology Hardware",
            historical_reports=historical_reports,
            projected_reports=projected_reports,
            last_updated=datetime.now().isoformat(),
            data_source="nasdaq.com"
        )
        
        self.assertEqual(company_data.symbol, "AAPL")
        self.assertEqual(len(company_data.historical_reports), 1)
        self.assertEqual(len(company_data.projected_reports), 1)
        self.assertEqual(company_data.get_total_reports_count(), 2)
        
        # Test dictionary conversion
        data_dict = company_data.to_dict()
        self.assertIn('symbol', data_dict)
        self.assertIn('historical_reports', data_dict)
        self.assertIn('projected_reports', data_dict)
        
        # Verify structure matches template
        expected_keys = {
            'symbol', 'company_name', 'sector', 'sub_sector',
            'historical_reports', 'projected_reports', 'last_updated', 'data_source'
        }
        self.assertEqual(set(data_dict.keys()), expected_keys)
    
    def test_earnings_report_builder(self):
        """Test the EarningsReportBuilder"""
        builder = EarningsReportBuilder("AAPL")
        
        report = (builder
                 .set_earnings_date("2024-07-18")
                 .set_eps_data(1.73, 1.76)
                 .set_revenue_data(146.29, 7.3)
                 .set_price_data(153.42, 153.42, 143.91)
                 .set_volume_data(37563589, 37563589, 36227374)
                 .set_technical_indicators(160.84, 132.33, 175.32, 116.97)
                 .set_company_data(995967199.98, "Information Technology", "Technology Hardware", 3.55, 3.57, "2024-08-06")
                 .set_metadata("Buy", 1.0, "BMO")
                 .build())
        
        self.assertEqual(report.symbol, "AAPL")
        self.assertEqual(report.quarter, 3)
        self.assertEqual(report.year, 2024)
        self.assertEqual(report.beat_miss_meet, "MISS")
        self.assertAlmostEqual(report.surprise_percent, -1.7, places=1)


class TestNASDAQDataScraper(unittest.TestCase):
    """Test the NASDAQ data scraper"""
    
    def setUp(self):
        self.scraper = NASDAQDataScraper()
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper.session)
        self.assertIn('User-Agent', self.scraper.session.headers)
        self.assertEqual(self.scraper.yf_cache, {})
    
    def test_parse_float_method(self):
        """Test the _parse_float method with various inputs"""
        # Test normal cases
        self.assertEqual(self.scraper._parse_float('1.73'), 1.73)
        self.assertEqual(self.scraper._parse_float('$153.42'), 153.42)
        self.assertEqual(self.scraper._parse_float('1,234.56'), 1234.56)
        
        # Test with suffixes
        self.assertEqual(self.scraper._parse_float('1.5K'), 1500.0)
        self.assertEqual(self.scraper._parse_float('2.3M'), 2300000.0)
        self.assertEqual(self.scraper._parse_float('1.2B'), 1200000000.0)
        self.assertEqual(self.scraper._parse_float('1.5T'), 1500000000000.0)
        
        # Test negative values
        self.assertEqual(self.scraper._parse_float('(1.5)'), -1.5)
        
        # Test edge cases
        self.assertIsNone(self.scraper._parse_float('-'))
        self.assertIsNone(self.scraper._parse_float('N/A'))
        self.assertIsNone(self.scraper._parse_float(''))
        self.assertIsNone(self.scraper._parse_float('--'))
    
    def test_parse_date_method(self):
        """Test the _parse_date method with various date formats"""
        # Test common formats
        self.assertEqual(self.scraper._parse_date('07/18/2024'), '2024-07-18')
        self.assertEqual(self.scraper._parse_date('2024-07-18'), '2024-07-18')
        self.assertEqual(self.scraper._parse_date('Jul 18, 2024'), '2024-07-18')
        self.assertEqual(self.scraper._parse_date('18 Jul 2024'), '2024-07-18')
        
        # Test edge cases
        self.assertIsNone(self.scraper._parse_date('-'))
        self.assertIsNone(self.scraper._parse_date(''))
        self.assertIsNone(self.scraper._parse_date('N/A'))
    
    def test_parse_revenue_method(self):
        """Test the _parse_revenue method"""
        # Test values in millions (should convert to billions)
        self.assertEqual(self.scraper._parse_revenue('146,290M'), 146.29)
        
        # Test values already in billions
        self.assertEqual(self.scraper._parse_revenue('146.29B'), 146.29)
        
        # Test edge cases
        self.assertIsNone(self.scraper._parse_revenue('-'))
        self.assertIsNone(self.scraper._parse_revenue('N/A'))
    
    def test_looks_like_date_method(self):
        """Test the _looks_like_date method"""
        self.assertTrue(self.scraper._looks_like_date('07/18/2024'))
        self.assertTrue(self.scraper._looks_like_date('2024-07-18'))
        self.assertTrue(self.scraper._looks_like_date('Jul 18, 2024'))
        self.assertTrue(self.scraper._looks_like_date('18 Jul 2024'))
        
        self.assertFalse(self.scraper._looks_like_date('1.73'))
        self.assertFalse(self.scraper._looks_like_date('AAPL'))
        self.assertFalse(self.scraper._looks_like_date('-'))
    
    @patch('requests.Session.get')
    def test_scrape_earnings_page_success(self, mock_get):
        """Test successful scraping of earnings page"""
        # Mock HTML response with earnings table
        mock_html = """
        <html>
            <body>
                <table class="earnings-table">
                    <tr>
                        <th>Date</th>
                        <th>Actual EPS</th>
                        <th>Estimate EPS</th>
                        <th>Revenue</th>
                    </tr>
                    <tr>
                        <td>07/18/2024</td>
                        <td>1.73</td>
                        <td>1.76</td>
                        <td>146.29B</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper._scrape_earnings_page('AAPL')
        
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        self.assertIn('earnings_reports', result)
        self.assertEqual(result['symbol'], 'AAPL')
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_scrape_earnings_page_failure(self, mock_get):
        """Test handling of scraping failures"""
        mock_get.side_effect = Exception("Network error")
        
        result = self.scraper._scrape_earnings_page('INVALID')
        
        self.assertEqual(result['symbol'], 'INVALID')
        self.assertEqual(result['earnings_reports'], [])


class TestSP500Processor(unittest.TestCase):
    """Test the S&P 500 processor"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sp500_file = Path(self.temp_dir) / 'test_sp500.json'
        self.processor = SP500Processor(str(self.sp500_file))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_sample_sp500_file(self):
        """Test creating sample S&P 500 file"""
        self.processor.create_sample_sp500_file()
        
        self.assertTrue(self.sp500_file.exists())
        
        # Verify content
        with open(self.sp500_file, 'r') as f:
            companies = json.load(f)
        
        self.assertIsInstance(companies, list)
        self.assertGreater(len(companies), 0)
        
        # Check first company structure
        first_company = companies[0]
        expected_keys = {'symbol', 'company_name', 'gics_sector', 'gics_sub_industry'}
        self.assertTrue(expected_keys.issubset(set(first_company.keys())))
    
    def test_load_sp500_companies(self):
        """Test loading S&P 500 companies"""
        # Create sample file first
        self.processor.create_sample_sp500_file()
        
        companies = self.processor.load_sp500_companies()
        
        self.assertIsInstance(companies, list)
        self.assertGreater(len(companies), 0)
        
        # Test caching
        companies2 = self.processor.load_sp500_companies()
        self.assertEqual(companies, companies2)
    
    def test_get_company_info(self):
        """Test getting company information"""
        self.processor.create_sample_sp500_file()
        
        company_info = self.processor.get_company_info('AAPL')
        
        self.assertIsNotNone(company_info)
        self.assertEqual(company_info['symbol'], 'AAPL')
        self.assertIn('company_name', company_info)
        
        # Test non-existent symbol
        non_existent = self.processor.get_company_info('INVALID')
        self.assertIsNone(non_existent)
    
    def test_get_symbols_by_sector(self):
        """Test getting symbols by sector"""
        self.processor.create_sample_sp500_file()
        
        tech_symbols = self.processor.get_symbols_by_sector('Information Technology')
        
        self.assertIsInstance(tech_symbols, list)
        self.assertIn('AAPL', tech_symbols)
        self.assertIn('MSFT', tech_symbols)
    
    def test_get_all_symbols(self):
        """Test getting all symbols"""
        self.processor.create_sample_sp500_file()
        
        all_symbols = self.processor.get_all_symbols()
        
        self.assertIsInstance(all_symbols, list)
        self.assertIn('AAPL', all_symbols)
        self.assertIn('MSFT', all_symbols)
    
    def test_validate_symbol(self):
        """Test symbol validation"""
        self.processor.create_sample_sp500_file()
        
        self.assertTrue(self.processor.validate_symbol('AAPL'))
        self.assertTrue(self.processor.validate_symbol('aapl'))  # Case insensitive
        self.assertFalse(self.processor.validate_symbol('INVALID'))
    
    def test_get_company_summary(self):
        """Test getting company summary"""
        self.processor.create_sample_sp500_file()
        
        summary = self.processor.get_company_summary()
        
        self.assertIn('total_companies', summary)
        self.assertIn('sectors', summary)
        self.assertIn('industries', summary)
        self.assertGreater(summary['total_companies'], 0)


class TestEarningsCurator(unittest.TestCase):
    """Test the main earnings curator"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.curator = EarningsCurator(output_dir=self.temp_dir)
        
        # Create mock SP500 processor with sample data
        self.curator.sp500_processor = SP500Processor()
        self.curator.sp500_processor._companies_cache = [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'gics_sector': 'Information Technology',
                'gics_sub_industry': 'Technology Hardware, Storage & Peripherals'
            }
        ]
        self.curator.sp500_processor._companies_by_symbol = {
            'AAPL': {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'gics_sector': 'Information Technology',
                'gics_sub_industry': 'Technology Hardware, Storage & Peripherals'
            }
        }
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('nasdaq_data_scraper.NASDAQDataScraper.scrape_symbol_earnings')
    def test_curate_single_symbol_success(self, mock_scrape):
        """Test successful curation of a single symbol"""
        # Mock earnings data
        mock_earnings_data = {
            'earnings_reports': [{
                'symbol': 'AAPL',
                'earnings_date': '2024-07-18',
                'quarter': 3,
                'year': 2024,
                'actual_eps': 1.73,
                'estimated_eps': 1.76,
                'beat_miss_meet': 'MISS',
                'revenue_billions': 146.29
            }]
        }
        mock_scrape.return_value = mock_earnings_data
        
        success = self.curator.curate_single_symbol('AAPL')
        
        self.assertTrue(success)
        self.assertEqual(self.curator.processed_count, 1)
        self.assertEqual(self.curator.failed_count, 0)
        
        # Check that file was created
        output_file = self.curator.output_dir / 'AAPL.json'
        self.assertTrue(output_file.exists())
        
        # Verify file content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertIn('historical_reports', data)
        self.assertIn('projected_reports', data)
        self.assertEqual(len(data['historical_reports']), 1)
    
    @patch('nasdaq_data_scraper.NASDAQDataScraper.scrape_symbol_earnings')
    def test_curate_single_symbol_failure(self, mock_scrape):
        """Test handling of curation failure"""
        mock_scrape.side_effect = Exception("Scraping error")
        
        success = self.curator.curate_single_symbol('INVALID')
        
        self.assertFalse(success)
        self.assertEqual(self.curator.processed_count, 0)
        self.assertEqual(self.curator.failed_count, 1)
        self.assertIn('INVALID', self.curator.failed_symbols)
    
    @patch('nasdaq_data_scraper.NASDAQDataScraper.scrape_symbol_earnings')
    def test_curate_symbol_list(self, mock_scrape):
        """Test curating a list of symbols"""
        mock_earnings_data = {
            'earnings_reports': [{
                'symbol': 'AAPL',
                'earnings_date': '2024-07-18',
                'actual_eps': 1.73,
                'estimated_eps': 1.76
            }]
        }
        mock_scrape.return_value = mock_earnings_data
        
        results = self.curator.curate_symbol_list(['AAPL'])
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results['AAPL'])
    
    def test_create_company_earnings_data(self):
        """Test creating CompanyEarningsData structure"""
        earnings_data = {
            'earnings_reports': [{
                'symbol': 'AAPL',
                'earnings_date': '2024-07-18',
                'quarter': 3,
                'year': 2024,
                'actual_eps': 1.73,
                'estimated_eps': 1.76,
                'revenue_billions': 146.29
            }]
        }
        
        company_info = {
            'company_name': 'Apple Inc.',
            'gics_sector': 'Information Technology',
            'gics_sub_industry': 'Technology Hardware, Storage & Peripherals'
        }
        
        company_earnings = self.curator._create_company_earnings_data('AAPL', earnings_data, company_info)
        
        self.assertEqual(company_earnings.symbol, 'AAPL')
        self.assertEqual(company_earnings.company_name, 'Apple Inc.')
        self.assertEqual(company_earnings.sector, 'Information Technology')
        self.assertEqual(len(company_earnings.historical_reports), 1)
        self.assertEqual(len(company_earnings.projected_reports), 0)
    
    def test_save_earnings_data(self):
        """Test saving earnings data"""
        company_earnings = CompanyEarningsData(
            symbol='AAPL',
            company_name='Apple Inc.',
            sector='Information Technology',
            sub_sector='Technology Hardware',
            historical_reports=[],
            projected_reports=[],
            last_updated=datetime.now().isoformat(),
            data_source='nasdaq.com'
        )
        
        self.curator._save_earnings_data('AAPL', company_earnings)
        
        # Check file was created
        output_file = self.curator.output_dir / 'AAPL.json'
        self.assertTrue(output_file.exists())
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertEqual(data['company_name'], 'Apple Inc.')
    
    def test_generate_summary_report(self):
        """Test generating summary report"""
        self.curator.processed_count = 5
        self.curator.failed_count = 1
        self.curator.failed_symbols = ['INVALID']
        
        self.curator.generate_summary_report()
        
        # Check summary file was created
        summary_file = self.curator.output_dir / 'curation_summary.json'
        self.assertTrue(summary_file.exists())
        
        # Verify content
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary['curation_summary']['total_processed'], 5)
        self.assertEqual(summary['curation_summary']['failed'], 1)
        self.assertIn('INVALID', summary['failed_symbols'])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete earnings curator system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_template_schema_compliance(self):
        """Test that generated JSON matches the template schema"""
        # Create sample earnings data
        historical_reports = [
            EarningsReport(
                symbol="AAPL", earnings_date="2024-07-18", quarter=3, year=2024,
                actual_eps=1.73, estimated_eps=1.76, beat_miss_meet="MISS", surprise_percent=-1.7,
                revenue_billions=146.29, revenue_growth_percent=7.3, consensus_rating="Buy",
                confidence_score=1.0, source_url="https://www.nasdaq.com/market-activity/stocks/aapl/earnings",
                data_verified_date="2025-07-18", stock_price_on_date=153.42, announcement_time="BMO",
                volume=37563589, date_earnings_report="2024-07-18", market_cap=995967199.98,
                price_at_close_earnings_report_date=153.42, price_at_open_day_after_earnings_report_date=143.91,
                percentage_stock_change=-6.2, earnings_report_result="MISS",
                estimated_earnings_per_share=1.76, reported_earnings_per_share=1.73,
                volume_day_of_earnings_report=37563589, volume_day_after_earnings_report=36227374,
                moving_avg_200_day=132.33, moving_avg_50_day=160.84,
                week_52_high=175.32, week_52_low=116.97, market_sector="Information Technology",
                market_sub_sector="Technology Hardware", percentage_short_interest=3.55,
                dividend_yield=3.57, ex_dividend_date="2024-08-06"
            )
        ]
        
        projected_reports = [
            EarningsReport(
                symbol="AAPL", earnings_date="2025-08-17", quarter=3, year=2025,
                actual_eps=None, estimated_eps=2.56, beat_miss_meet="PROJECTED", surprise_percent=None,
                revenue_billions=None, revenue_growth_percent=None, consensus_rating="Hold",
                confidence_score=0.7, source_url="https://www.nasdaq.com/market-activity/stocks/aapl/earnings",
                data_verified_date="2025-07-18", stock_price_on_date=68.23, announcement_time="BMO",
                volume=25680309, date_earnings_report="2025-08-17", market_cap=322576361.17,
                price_at_close_earnings_report_date=None, price_at_open_day_after_earnings_report_date=None,
                percentage_stock_change=None, earnings_report_result="PROJECTED",
                estimated_earnings_per_share=2.56, reported_earnings_per_share=None,
                volume_day_of_earnings_report=None, volume_day_after_earnings_report=None,
                moving_avg_200_day=59.39, moving_avg_50_day=70.9,
                week_52_high=78.07, week_52_low=49.77, market_sector="Information Technology",
                market_sub_sector="Technology Hardware", percentage_short_interest=2.57,
                dividend_yield=3.63, ex_dividend_date="2025-09-01"
            )
        ]
        
        company_data = CompanyEarningsData(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Information Technology",
            sub_sector="Technology Hardware",
            historical_reports=historical_reports,
            projected_reports=projected_reports,
            last_updated=datetime.now().isoformat(),
            data_source="nasdaq.com"
        )
        
        # Convert to dictionary (JSON format)
        data_dict = company_data.to_dict()
        
        # Verify top-level structure matches template
        expected_top_level_keys = {
            'symbol', 'company_name', 'sector', 'sub_sector',
            'historical_reports', 'projected_reports', 'last_updated', 'data_source'
        }
        self.assertEqual(set(data_dict.keys()), expected_top_level_keys)
        
        # Verify historical report structure
        if data_dict['historical_reports']:
            historical_report = data_dict['historical_reports'][0]
            # Check that all required fields are present
            required_report_fields = {
                'symbol', 'earnings_date', 'quarter', 'year', 'actual_eps', 'estimated_eps',
                'beat_miss_meet', 'surprise_percent', 'revenue_billions', 'revenue_growth_percent',
                'consensus_rating', 'confidence_score', 'source_url', 'data_verified_date',
                'stock_price_on_date', 'announcement_time', 'volume', 'date_earnings_report',
                'market_cap', 'price_at_close_earnings_report_date', 'price_at_open_day_after_earnings_report_date',
                'percentage_stock_change', 'earnings_report_result', 'estimated_earnings_per_share',
                'reported_earnings_per_share', 'volume_day_of_earnings_report', 'volume_day_after_earnings_report',
                'moving_avg_200_day', 'moving_avg_50_day', 'week_52_high', 'week_52_low',
                'market_sector', 'market_sub_sector', 'percentage_short_interest', 'dividend_yield',
                'ex_dividend_date'
            }
            self.assertTrue(required_report_fields.issubset(set(historical_report.keys())))
        
        # Verify projected report structure
        if data_dict['projected_reports']:
            projected_report = data_dict['projected_reports'][0]
            # Should have same fields as historical reports
            required_report_fields = {
                'symbol', 'earnings_date', 'quarter', 'year', 'actual_eps', 'estimated_eps',
                'beat_miss_meet', 'surprise_percent', 'revenue_billions', 'revenue_growth_percent',
                'consensus_rating', 'confidence_score', 'source_url', 'data_verified_date',
                'stock_price_on_date', 'announcement_time', 'volume', 'date_earnings_report',
                'market_cap', 'price_at_close_earnings_report_date', 'price_at_open_day_after_earnings_report_date',
                'percentage_stock_change', 'earnings_report_result', 'estimated_earnings_per_share',
                'reported_earnings_per_share', 'volume_day_of_earnings_report', 'volume_day_after_earnings_report',
                'moving_avg_200_day', 'moving_avg_50_day', 'week_52_high', 'week_52_low',
                'market_sector', 'market_sub_sector', 'percentage_short_interest', 'dividend_yield',
                'ex_dividend_date'
            }
            self.assertTrue(required_report_fields.issubset(set(projected_report.keys())))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)