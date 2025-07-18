"""
Unit tests for earnings schema and data structures.
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path

from earnings_schema import EarningsReport, CompanyEarningsData, create_sample_earnings_data


class TestEarningsReport:
    """Test EarningsReport data structure."""
    
    def test_earnings_report_creation(self):
        """Test creating an EarningsReport instance."""
        report = EarningsReport(
            date="2024-01-24",
            market_cap=3400000000000.0,
            close_price=225.37,
            next_open_price=227.53,
            price_change_percent=0.96,
            beat_or_miss="beat",
            estimated_eps=1.60,
            reported_eps=1.64,
            volume_earnings_day=50724800,
            volume_next_day=23486200,
            moving_avg_200=195.42,
            moving_avg_50=220.15,
            week_52_high=237.23,
            week_52_low=164.08,
            short_interest_percent=0.65,
            dividend_yield=0.44,
            ex_dividend_date="2024-02-11"
        )
        
        assert report.date == "2024-01-24"
        assert report.beat_or_miss == "beat"
        assert report.estimated_eps == 1.60
        assert report.reported_eps == 1.64
        assert report.is_historical is True
    
    def test_earnings_report_defaults(self):
        """Test EarningsReport with minimal required fields."""
        report = EarningsReport(
            date="2024-01-24",
            close_price=225.37,
            next_open_price=227.53,
            price_change_percent=0.96,
            beat_or_miss="beat",
            estimated_eps=1.60,
            reported_eps=1.64,
            volume_earnings_day=50724800,
            volume_next_day=23486200,
            moving_avg_200=195.42,
            moving_avg_50=220.15,
            week_52_high=237.23,
            week_52_low=164.08,
            short_interest_percent=0.65,
            dividend_yield=0.44
        )
        
        assert report.is_historical is True
        assert report.market_cap is None
        assert report.ex_dividend_date is None


class TestCompanyEarningsData:
    """Test CompanyEarningsData structure and methods."""
    
    def setup_method(self):
        """Setup test data."""
        self.sample_report = EarningsReport(
            date="2024-01-24",
            market_cap=3400000000000.0,
            close_price=225.37,
            next_open_price=227.53,
            price_change_percent=0.96,
            beat_or_miss="beat",
            estimated_eps=1.60,
            reported_eps=1.64,
            volume_earnings_day=50724800,
            volume_next_day=23486200,
            moving_avg_200=195.42,
            moving_avg_50=220.15,
            week_52_high=237.23,
            week_52_low=164.08,
            short_interest_percent=0.65,
            dividend_yield=0.44,
            ex_dividend_date="2024-02-11"
        )
        
        self.sample_company = CompanyEarningsData(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Information Technology",
            sub_sector="Technology Hardware",
            historical_reports=[self.sample_report],
            projected_reports=[],
            last_updated=datetime.now().isoformat()
        )
    
    def test_company_creation(self):
        """Test creating CompanyEarningsData instance."""
        assert self.sample_company.symbol == "AAPL"
        assert self.sample_company.company_name == "Apple Inc."
        assert len(self.sample_company.historical_reports) == 1
        assert len(self.sample_company.projected_reports) == 0
    
    def test_to_dict_conversion(self):
        """Test converting CompanyEarningsData to dictionary."""
        data_dict = self.sample_company.to_dict()
        
        assert isinstance(data_dict, dict)
        assert data_dict["symbol"] == "AAPL"
        assert data_dict["company_name"] == "Apple Inc."
        assert "historical_reports" in data_dict
        assert isinstance(data_dict["historical_reports"], list)
    
    def test_to_json_conversion(self):
        """Test converting CompanyEarningsData to JSON."""
        json_str = self.sample_company.to_json()
        
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["symbol"] == "AAPL"
        assert parsed["company_name"] == "Apple Inc."
    
    def test_save_and_load_file(self):
        """Test saving to and loading from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Save to file
            self.sample_company.save_to_file(tmp_path)
            
            # Check file exists and has content
            assert Path(tmp_path).exists()
            assert Path(tmp_path).stat().st_size > 0
            
            # Load from file
            loaded_company = CompanyEarningsData.from_json_file(tmp_path)
            
            assert loaded_company.symbol == self.sample_company.symbol
            assert loaded_company.company_name == self.sample_company.company_name
            assert len(loaded_company.historical_reports) == len(self.sample_company.historical_reports)
            
        finally:
            # Cleanup
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
    
    def test_from_dict_creation(self):
        """Test creating CompanyEarningsData from dictionary."""
        data_dict = self.sample_company.to_dict()
        reconstructed = CompanyEarningsData.from_dict(data_dict)
        
        assert reconstructed.symbol == self.sample_company.symbol
        assert reconstructed.company_name == self.sample_company.company_name
        assert len(reconstructed.historical_reports) == len(self.sample_company.historical_reports)


class TestSampleDataCreation:
    """Test sample data creation function."""
    
    def test_create_sample_earnings_data(self):
        """Test creating sample earnings data."""
        sample = create_sample_earnings_data()
        
        assert isinstance(sample, CompanyEarningsData)
        assert sample.symbol == "AAPL"
        assert sample.company_name == "Apple Inc."
        assert len(sample.historical_reports) >= 1
        assert len(sample.projected_reports) >= 1
        
        # Test historical report
        historical = sample.historical_reports[0]
        assert historical.is_historical is True
        assert historical.reported_eps > 0
        
        # Test projected report
        projected = sample.projected_reports[0]
        assert projected.is_historical is False
        assert projected.reported_eps == 0.0
    
    def test_sample_data_json_serialization(self):
        """Test that sample data can be serialized to JSON."""
        sample = create_sample_earnings_data()
        json_str = sample.to_json()
        
        # Should not raise exception
        parsed = json.loads(json_str)
        assert parsed["symbol"] == "AAPL"


class TestDataValidation:
    """Test data validation and edge cases."""
    
    def test_empty_reports_lists(self):
        """Test company data with empty reports lists."""
        company = CompanyEarningsData(
            symbol="TEST",
            company_name="Test Company",
            sector="Technology",
            sub_sector="Software",
            historical_reports=[],
            projected_reports=[],
            last_updated=datetime.now().isoformat()
        )
        
        assert len(company.historical_reports) == 0
        assert len(company.projected_reports) == 0
        
        # Should still be serializable
        json_str = company.to_json()
        parsed = json.loads(json_str)
        assert parsed["symbol"] == "TEST"
    
    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        report = EarningsReport(
            date="2024-01-24",
            market_cap=None,  # Optional field
            close_price=225.37,
            next_open_price=227.53,
            price_change_percent=0.96,
            beat_or_miss="beat",
            estimated_eps=1.60,
            reported_eps=1.64,
            volume_earnings_day=50724800,
            volume_next_day=23486200,
            moving_avg_200=195.42,
            moving_avg_50=220.15,
            week_52_high=237.23,
            week_52_low=164.08,
            short_interest_percent=0.65,
            dividend_yield=0.44,
            ex_dividend_date=None  # Optional field
        )
        
        assert report.market_cap is None
        assert report.ex_dividend_date is None
        assert report.date == "2024-01-24"


if __name__ == "__main__":
    pytest.main([__file__])