"""
Earnings data schema and validation for S&P 500 companies research.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class EarningsReport:
    """Individual earnings report data structure."""
    
    # Core earnings data
    date: str                           # Date of the earnings report
    market_cap: Optional[float]         # Market cap on earnings day
    close_price: float                  # Stock price at close on earnings day
    next_open_price: float              # Stock price at open next day
    price_change_percent: float         # % change between close and next open
    
    # Earnings performance
    beat_or_miss: str                   # "beat" or "miss"
    estimated_eps: float                # Estimated earnings per share
    reported_eps: float                 # Reported earnings per share
    
    # Volume data
    volume_earnings_day: int            # Volume on earnings day
    volume_next_day: int                # Volume on day after earnings
    
    # Technical indicators
    moving_avg_200: float               # 200-day moving average
    moving_avg_50: float                # 50-day moving average
    week_52_high: float                 # 52-week high
    week_52_low: float                  # 52-week low
    
    # Additional metrics
    short_interest_percent: float       # Percentage short interest
    dividend_yield: float               # Dividend yield
    ex_dividend_date: Optional[str]     # Ex-dividend date closest to earnings
    
    # Report type
    is_historical: bool = True          # True for historical, False for projected


@dataclass
class CompanyEarningsData:
    """Complete earnings data for a single company."""
    
    # Company identification
    symbol: str
    company_name: str
    sector: str
    sub_sector: str
    
    # Earnings reports
    historical_reports: List[EarningsReport]
    projected_reports: List[EarningsReport]
    
    # Metadata
    last_updated: str
    data_source: str = "nasdaq.com"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save_to_file(self, filepath: str) -> None:
        """Save earnings data to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyEarningsData':
        """Create instance from dictionary."""
        historical = [EarningsReport(**report) for report in data.get('historical_reports', [])]
        projected = [EarningsReport(**report) for report in data.get('projected_reports', [])]
        
        return cls(
            symbol=data['symbol'],
            company_name=data['company_name'],
            sector=data['sector'],
            sub_sector=data['sub_sector'],
            historical_reports=historical,
            projected_reports=projected,
            last_updated=data['last_updated'],
            data_source=data.get('data_source', 'nasdaq.com')
        )
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'CompanyEarningsData':
        """Load earnings data from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_sample_earnings_data() -> CompanyEarningsData:
    """Create sample earnings data for testing."""
    sample_historical = EarningsReport(
        date="2024-10-24",
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
        ex_dividend_date="2024-11-11",
        is_historical=True
    )
    
    sample_projected = EarningsReport(
        date="2025-01-30",
        market_cap=None,
        close_price=0.0,
        next_open_price=0.0,
        price_change_percent=0.0,
        beat_or_miss="projected",
        estimated_eps=2.35,
        reported_eps=0.0,
        volume_earnings_day=0,
        volume_next_day=0,
        moving_avg_200=0.0,
        moving_avg_50=0.0,
        week_52_high=0.0,
        week_52_low=0.0,
        short_interest_percent=0.0,
        dividend_yield=0.0,
        ex_dividend_date=None,
        is_historical=False
    )
    
    return CompanyEarningsData(
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Information Technology",
        sub_sector="Technology Hardware, Storage & Peripherals",
        historical_reports=[sample_historical],
        projected_reports=[sample_projected],
        last_updated=datetime.now().isoformat()
    )


if __name__ == "__main__":
    # Demo usage
    sample = create_sample_earnings_data()
    print("Sample earnings data structure:")
    print(sample.to_json())