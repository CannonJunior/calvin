"""
Unit tests for data processor functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from data_processor import EarningsDataProcessor
from earnings_schema import CompanyEarningsData, EarningsReport


class TestEarningsDataProcessor:
    """Test EarningsDataProcessor class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = EarningsDataProcessor(output_dir=self.temp_dir)
        
        # Sample company data
        self.sample_company = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "gics_sector": "Information Technology",
            "gics_sub_industry": "Technology Hardware, Storage & Peripherals",
            "headquarters": "Cupertino, California",
            "date_added": "1980-12-12",
            "cik": "320193",
            "founded": "1976"
        }
        
        # Sample scraped data
        self.sample_scraped_data = {
            "symbol": "AAPL",
            "company_info": {"name": "Apple Inc."},
            "historical_earnings": [
                {
                    "date": "2024-01-24",
                    "estimated_eps": 1.60,
                    "reported_eps": 1.64,
                    "beat_or_miss": "beat"
                }
            ],
            "projected_earnings": [
                {
                    "date": "2025-01-30",
                    "estimated_eps": 2.35,
                    "reported_eps": 0.0,
                    "beat_or_miss": "projected"
                }
            ],
            "current_metrics": {
                "current_price": 225.37,
                "market_cap": 3400000000000.0,
                "volume": 50724800,
                "52_week_high": 237.23,
                "52_week_low": 164.08
            },
            "scrape_timestamp": "2024-01-24T10:30:00",
            "source_url": "https://www.nasdaq.com/market-activity/stocks/aapl/earnings"
        }
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        assert self.processor.output_dir == Path(self.temp_dir)
        assert self.processor.output_dir.exists()
        assert hasattr(self.processor, 'scraper')
    
    def test_load_sp500_companies_success(self):
        """Test loading S&P 500 companies successfully."""
        # Create test companies file
        test_companies = [
            {"symbol": "AAPL", "company_name": "Apple Inc."},
            {"symbol": "MSFT", "company_name": "Microsoft Corporation"}
        ]
        
        test_file = Path(self.temp_dir) / "test_companies.json"
        with open(test_file, 'w') as f:
            json.dump(test_companies, f)
        
        companies = self.processor.load_sp500_companies(str(test_file))
        
        assert len(companies) == 2
        assert companies[0]["symbol"] == "AAPL"
        assert companies[1]["symbol"] == "MSFT"
    
    def test_load_sp500_companies_file_not_found(self):
        """Test loading companies when file doesn't exist."""
        companies = self.processor.load_sp500_companies("nonexistent.json")
        assert companies == []
    
    def test_load_sp500_companies_invalid_json(self):
        """Test loading companies with invalid JSON."""
        test_file = Path(self.temp_dir) / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("invalid json content")
        
        companies = self.processor.load_sp500_companies(str(test_file))
        assert companies == []
    
    def test_process_scraped_data_success(self):
        """Test processing scraped data successfully."""
        result = self.processor.process_scraped_data(self.sample_scraped_data, self.sample_company)
        
        assert isinstance(result, CompanyEarningsData)
        assert result.symbol == "AAPL"
        assert result.company_name == "Apple Inc."
        assert result.sector == "Information Technology"
        assert len(result.historical_reports) == 1
        assert len(result.projected_reports) == 1
        
        # Check historical report
        historical = result.historical_reports[0]
        assert historical.date == "2024-01-24"
        assert historical.estimated_eps == 1.60
        assert historical.reported_eps == 1.64
        assert historical.beat_or_miss == "beat"
        assert historical.is_historical is True
        
        # Check projected report
        projected = result.projected_reports[0]
        assert projected.date == "2025-01-30"
        assert projected.estimated_eps == 2.35
        assert projected.is_historical is False
    
    def test_process_scraped_data_missing_info(self):
        """Test processing scraped data with missing information."""
        incomplete_data = {
            "symbol": "TEST",
            "historical_earnings": [],
            "projected_earnings": [],
            "current_metrics": {}
        }
        
        incomplete_company = {
            "symbol": "TEST",
            "company_name": "Test Company"
        }
        
        result = self.processor.process_scraped_data(incomplete_data, incomplete_company)
        
        assert isinstance(result, CompanyEarningsData)
        assert result.symbol == "TEST"
        assert result.sector == "Unknown"  # Default value
        assert len(result.historical_reports) == 0
        assert len(result.projected_reports) == 0
    
    def test_create_earnings_report_historical(self):
        """Test creating historical earnings report."""
        earnings_data = {
            "date": "2024-01-24",
            "estimated_eps": 1.60,
            "reported_eps": 1.64,
            "beat_or_miss": "beat"
        }
        
        report = self.processor._create_earnings_report(
            earnings_data, self.sample_scraped_data, is_historical=True
        )
        
        assert isinstance(report, EarningsReport)
        assert report.date == "2024-01-24"
        assert report.estimated_eps == 1.60
        assert report.reported_eps == 1.64
        assert report.beat_or_miss == "beat"
        assert report.is_historical is True
        assert report.close_price > 0  # Should have current price
    
    def test_create_earnings_report_projected(self):
        """Test creating projected earnings report."""
        earnings_data = {
            "date": "2025-01-30",
            "estimated_eps": 2.35,
            "reported_eps": 0.0,
            "beat_or_miss": "projected"
        }
        
        report = self.processor._create_earnings_report(
            earnings_data, self.sample_scraped_data, is_historical=False
        )
        
        assert isinstance(report, EarningsReport)
        assert report.date == "2025-01-30"
        assert report.estimated_eps == 2.35
        assert report.reported_eps == 0.0
        assert report.is_historical is False
        assert report.close_price == 0.0  # Projected - no current price
        assert report.market_cap is None
    
    def test_estimate_ex_dividend_date(self):
        """Test ex-dividend date estimation."""
        # Valid date
        ex_div = self.processor._estimate_ex_dividend_date("2024-01-24")
        assert ex_div is not None
        assert len(ex_div) == 10  # YYYY-MM-DD format
        
        # Invalid date
        ex_div_invalid = self.processor._estimate_ex_dividend_date("invalid-date")
        assert ex_div_invalid is None
        
        # Empty date
        ex_div_empty = self.processor._estimate_ex_dividend_date("")
        assert ex_div_empty is None
    
    @patch('data_processor.EarningsDataProcessor.load_sp500_companies')
    def test_get_processing_status(self, mock_load):
        """Test getting processing status."""
        # Mock companies list
        mock_load.return_value = [
            {"symbol": "AAPL"}, {"symbol": "MSFT"}, {"symbol": "GOOGL"}
        ]
        
        # Create some existing files
        (Path(self.temp_dir) / "AAPL.json").touch()
        (Path(self.temp_dir) / "MSFT.json").touch()
        
        status = self.processor.get_processing_status()
        
        assert status["total_companies"] == 3
        assert status["processed"] == 2
        assert status["remaining"] == 1
        assert status["percentage_complete"] == pytest.approx(66.67, rel=1e-2)
    
    @patch('data_processor.EarningsDataProcessor.load_sp500_companies')
    def test_get_processing_status_empty(self, mock_load):
        """Test processing status with no companies."""
        mock_load.return_value = []
        
        status = self.processor.get_processing_status()
        
        assert status["total_companies"] == 0
        assert status["processed"] == 0
        assert status["remaining"] == 0
        assert status["percentage_complete"] == 0


class TestProcessCompanyIntegration:
    """Integration tests for processing individual companies."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = EarningsDataProcessor(output_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('nasdaq_scraper.NasdaqEarningsScraper.scrape_company_earnings')
    def test_process_company_success(self, mock_scrape):
        """Test successful company processing."""
        # Mock scraper response
        mock_scrape.return_value = {
            "symbol": "AAPL",
            "company_info": {"name": "Apple Inc."},
            "historical_earnings": [
                {
                    "date": "2024-01-24",
                    "estimated_eps": 1.60,
                    "reported_eps": 1.64,
                    "beat_or_miss": "beat"
                }
            ],
            "projected_earnings": [],
            "current_metrics": {"current_price": 225.37}
        }
        
        company_info = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "gics_sector": "Technology",
            "gics_sub_industry": "Hardware"
        }
        
        result = self.processor.process_company(company_info)
        
        assert result is True
        
        # Check output file was created
        output_file = Path(self.temp_dir) / "AAPL.json"
        assert output_file.exists()
        
        # Verify file contents
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["symbol"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
        assert len(data["historical_reports"]) == 1
    
    @patch('nasdaq_scraper.NasdaqEarningsScraper.scrape_company_earnings')
    def test_process_company_scraping_failure(self, mock_scrape):
        """Test company processing when scraping fails."""
        mock_scrape.return_value = None
        
        company_info = {"symbol": "FAIL", "company_name": "Fail Corp"}
        result = self.processor.process_company(company_info)
        
        assert result is False
        
        # No output file should be created
        output_file = Path(self.temp_dir) / "FAIL.json"
        assert not output_file.exists()
    
    def test_process_company_missing_symbol(self):
        """Test processing company with missing symbol."""
        company_info = {"company_name": "No Symbol Corp"}
        result = self.processor.process_company(company_info)
        
        assert result is False
    
    @patch('nasdaq_scraper.NasdaqEarningsScraper.scrape_company_earnings')
    def test_process_company_existing_file(self, mock_scrape):
        """Test processing company when output file already exists."""
        # Create existing file
        output_file = Path(self.temp_dir) / "EXISTS.json"
        output_file.write_text('{"symbol": "EXISTS"}')
        
        company_info = {"symbol": "EXISTS", "company_name": "Exists Corp"}
        result = self.processor.process_company(company_info)
        
        assert result is True
        # Scraper should not be called
        mock_scrape.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])