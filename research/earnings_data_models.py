#!/usr/bin/env python3
"""
Earnings Data Models

Data structures that match the earnings template schema from PLANNING.md
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, date


@dataclass
class EarningsReport:
    """Individual earnings report matching the template schema"""
    
    # Core earnings information
    symbol: str
    earnings_date: str
    quarter: int
    year: int
    actual_eps: Optional[float]
    estimated_eps: Optional[float]
    beat_miss_meet: str  # "BEAT", "MISS", "MEET", "PROJECTED"
    surprise_percent: Optional[float]
    revenue_billions: Optional[float]
    revenue_growth_percent: Optional[float]
    
    # Metadata
    consensus_rating: str
    confidence_score: float
    source_url: str
    data_verified_date: str
    
    # Stock price and volume data
    stock_price_on_date: Optional[float]
    announcement_time: str  # "BMO", "AMC"
    volume: Optional[int]
    date_earnings_report: str
    
    # Market data
    market_cap: Optional[float]
    price_at_close_earnings_report_date: Optional[float]
    price_at_open_day_after_earnings_report_date: Optional[float]
    percentage_stock_change: Optional[float]
    earnings_report_result: str  # Same as beat_miss_meet
    
    # EPS data (duplicated for template compatibility)
    estimated_earnings_per_share: Optional[float]
    reported_earnings_per_share: Optional[float]
    
    # Volume data
    volume_day_of_earnings_report: Optional[int]
    volume_day_after_earnings_report: Optional[int]
    
    # Technical indicators
    moving_avg_200_day: Optional[float]
    moving_avg_50_day: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    
    # Company fundamentals
    market_sector: str
    market_sub_sector: str
    percentage_short_interest: Optional[float]
    dividend_yield: Optional[float]
    ex_dividend_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def is_projected(self) -> bool:
        """Check if this is a projected earnings report"""
        return self.actual_eps is None or self.beat_miss_meet == "PROJECTED"
    
    def calculate_surprise_percent(self) -> Optional[float]:
        """Calculate earnings surprise percentage"""
        if self.actual_eps is None or self.estimated_eps is None or self.estimated_eps == 0:
            return None
        
        return round(((self.actual_eps - self.estimated_eps) / self.estimated_eps) * 100, 2)
    
    def determine_beat_miss_meet(self) -> str:
        """Determine if earnings beat, missed, or met estimates"""
        if self.actual_eps is None:
            return "PROJECTED"
        
        if self.estimated_eps is None:
            return "UNKNOWN"
        
        if self.actual_eps > self.estimated_eps:
            return "BEAT"
        elif self.actual_eps < self.estimated_eps:
            return "MISS"
        else:
            return "MEET"


@dataclass
class CompanyEarningsData:
    """Complete company earnings data structure matching the template schema"""
    
    symbol: str
    company_name: str
    sector: str
    sub_sector: str
    historical_reports: List[EarningsReport]
    projected_reports: List[EarningsReport]
    last_updated: str
    data_source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "sub_sector": self.sub_sector,
            "historical_reports": [report.to_dict() for report in self.historical_reports],
            "projected_reports": [report.to_dict() for report in self.projected_reports],
            "last_updated": self.last_updated,
            "data_source": self.data_source
        }
    
    def get_latest_historical_report(self) -> Optional[EarningsReport]:
        """Get the most recent historical earnings report"""
        if not self.historical_reports:
            return None
        
        # Sort by earnings_date and return the latest
        sorted_reports = sorted(
            self.historical_reports,
            key=lambda r: r.earnings_date,
            reverse=True
        )
        return sorted_reports[0]
    
    def get_next_projected_report(self) -> Optional[EarningsReport]:
        """Get the next projected earnings report"""
        if not self.projected_reports:
            return None
        
        # Sort by earnings_date and return the earliest future date
        today = date.today().isoformat()
        future_reports = [r for r in self.projected_reports if r.earnings_date > today]
        
        if not future_reports:
            return None
        
        sorted_reports = sorted(future_reports, key=lambda r: r.earnings_date)
        return sorted_reports[0]
    
    def get_total_reports_count(self) -> int:
        """Get total number of reports (historical + projected)"""
        return len(self.historical_reports) + len(self.projected_reports)
    
    def get_earnings_history_years(self) -> int:
        """Get number of years of earnings history"""
        if not self.historical_reports:
            return 0
        
        years = set(report.year for report in self.historical_reports)
        return len(years)
    
    def calculate_average_surprise_percent(self) -> Optional[float]:
        """Calculate average earnings surprise percentage for historical reports"""
        surprises = [
            report.surprise_percent 
            for report in self.historical_reports 
            if report.surprise_percent is not None
        ]
        
        if not surprises:
            return None
        
        return round(sum(surprises) / len(surprises), 2)
    
    def get_beat_miss_meet_summary(self) -> Dict[str, int]:
        """Get summary of beat/miss/meet results"""
        summary = {"BEAT": 0, "MISS": 0, "MEET": 0, "UNKNOWN": 0}
        
        for report in self.historical_reports:
            result = report.beat_miss_meet.upper()
            if result in summary:
                summary[result] += 1
            else:
                summary["UNKNOWN"] += 1
        
        return summary


class EarningsReportBuilder:
    """Builder class for creating EarningsReport objects"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data = {
            'symbol': symbol,
            'earnings_date': '',
            'quarter': 0,
            'year': 0,
            'actual_eps': None,
            'estimated_eps': None,
            'beat_miss_meet': '',
            'surprise_percent': None,
            'revenue_billions': None,
            'revenue_growth_percent': None,
            'consensus_rating': '',
            'confidence_score': 0.7,
            'source_url': f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings",
            'data_verified_date': date.today().isoformat(),
            'stock_price_on_date': None,
            'announcement_time': '',
            'volume': None,
            'date_earnings_report': '',
            'market_cap': None,
            'price_at_close_earnings_report_date': None,
            'price_at_open_day_after_earnings_report_date': None,
            'percentage_stock_change': None,
            'earnings_report_result': '',
            'estimated_earnings_per_share': None,
            'reported_earnings_per_share': None,
            'volume_day_of_earnings_report': None,
            'volume_day_after_earnings_report': None,
            'moving_avg_200_day': None,
            'moving_avg_50_day': None,
            'week_52_high': None,
            'week_52_low': None,
            'market_sector': '',
            'market_sub_sector': '',
            'percentage_short_interest': None,
            'dividend_yield': None,
            'ex_dividend_date': ''
        }
    
    def set_earnings_date(self, earnings_date: str) -> 'EarningsReportBuilder':
        """Set earnings date and derive quarter/year"""
        self.data['earnings_date'] = earnings_date
        self.data['date_earnings_report'] = earnings_date
        
        # Extract quarter and year from date
        try:
            dt = datetime.fromisoformat(earnings_date)
            self.data['quarter'] = (dt.month - 1) // 3 + 1
            self.data['year'] = dt.year
        except:
            pass
        
        return self
    
    def set_eps_data(self, actual_eps: Optional[float], estimated_eps: Optional[float]) -> 'EarningsReportBuilder':
        """Set EPS data and calculate derived fields"""
        self.data['actual_eps'] = actual_eps
        self.data['estimated_eps'] = estimated_eps
        self.data['estimated_earnings_per_share'] = estimated_eps
        self.data['reported_earnings_per_share'] = actual_eps
        
        # Calculate beat/miss/meet and surprise
        if actual_eps is not None and estimated_eps is not None:
            if actual_eps > estimated_eps:
                result = "BEAT"
            elif actual_eps < estimated_eps:
                result = "MISS"
            else:
                result = "MEET"
            
            self.data['beat_miss_meet'] = result
            self.data['earnings_report_result'] = result
            
            # Calculate surprise percentage
            if estimated_eps != 0:
                surprise = round(((actual_eps - estimated_eps) / estimated_eps) * 100, 2)
                self.data['surprise_percent'] = surprise
        
        elif actual_eps is None:
            self.data['beat_miss_meet'] = "PROJECTED"
            self.data['earnings_report_result'] = "PROJECTED"
        
        return self
    
    def set_revenue_data(self, revenue_billions: Optional[float], growth_percent: Optional[float]) -> 'EarningsReportBuilder':
        """Set revenue data"""
        self.data['revenue_billions'] = revenue_billions
        self.data['revenue_growth_percent'] = growth_percent
        return self
    
    def set_price_data(self, stock_price: Optional[float], close_price: Optional[float], 
                      next_open: Optional[float]) -> 'EarningsReportBuilder':
        """Set stock price data"""
        self.data['stock_price_on_date'] = stock_price
        self.data['price_at_close_earnings_report_date'] = close_price
        self.data['price_at_open_day_after_earnings_report_date'] = next_open
        
        # Calculate percentage change
        if close_price is not None and next_open is not None and close_price != 0:
            change_percent = round(((next_open - close_price) / close_price) * 100, 2)
            self.data['percentage_stock_change'] = change_percent
        
        return self
    
    def set_volume_data(self, volume: Optional[int], earnings_volume: Optional[int], 
                       after_volume: Optional[int]) -> 'EarningsReportBuilder':
        """Set volume data"""
        self.data['volume'] = volume
        self.data['volume_day_of_earnings_report'] = earnings_volume
        self.data['volume_day_after_earnings_report'] = after_volume
        return self
    
    def set_technical_indicators(self, ma_50: Optional[float], ma_200: Optional[float],
                               week_52_high: Optional[float], week_52_low: Optional[float]) -> 'EarningsReportBuilder':
        """Set technical indicators"""
        self.data['moving_avg_50_day'] = ma_50
        self.data['moving_avg_200_day'] = ma_200
        self.data['week_52_high'] = week_52_high
        self.data['week_52_low'] = week_52_low
        return self
    
    def set_company_data(self, market_cap: Optional[float], sector: str, sub_sector: str,
                        short_interest: Optional[float], dividend_yield: Optional[float],
                        ex_dividend_date: str) -> 'EarningsReportBuilder':
        """Set company fundamental data"""
        self.data['market_cap'] = market_cap
        self.data['market_sector'] = sector
        self.data['market_sub_sector'] = sub_sector
        self.data['percentage_short_interest'] = short_interest
        self.data['dividend_yield'] = dividend_yield
        self.data['ex_dividend_date'] = ex_dividend_date
        return self
    
    def set_metadata(self, consensus_rating: str, confidence_score: float,
                    announcement_time: str) -> 'EarningsReportBuilder':
        """Set metadata"""
        self.data['consensus_rating'] = consensus_rating
        self.data['confidence_score'] = confidence_score
        self.data['announcement_time'] = announcement_time
        return self
    
    def build(self) -> EarningsReport:
        """Build the EarningsReport object"""
        return EarningsReport(**self.data)


def create_sample_earnings_data() -> CompanyEarningsData:
    """Create sample earnings data for testing"""
    
    # Historical reports
    historical = [
        EarningsReportBuilder("AAPL")
        .set_earnings_date("2024-07-18")
        .set_eps_data(1.73, 1.76)
        .set_revenue_data(146.29, 7.3)
        .set_price_data(153.42, 153.42, 143.91)
        .set_volume_data(37563589, 37563589, 36227374)
        .set_technical_indicators(160.84, 132.33, 175.32, 116.97)
        .set_company_data(995967199.98, "Information Technology", "Technology Hardware", 3.55, 3.57, "2024-08-06")
        .set_metadata("Buy", 1.0, "BMO")
        .build()
    ]
    
    # Projected reports
    projected = [
        EarningsReportBuilder("AAPL")
        .set_earnings_date("2025-08-17")
        .set_eps_data(None, 2.56)
        .set_price_data(68.23, None, None)
        .set_technical_indicators(70.9, 59.39, 78.07, 49.77)
        .set_company_data(322576361.17, "Information Technology", "Technology Hardware", 2.57, 3.63, "2025-09-01")
        .set_metadata("Hold", 0.7, "BMO")
        .build()
    ]
    
    return CompanyEarningsData(
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Information Technology",
        sub_sector="Technology Hardware",
        historical_reports=historical,
        projected_reports=projected,
        last_updated=datetime.now().isoformat(),
        data_source="nasdaq.com"
    )


if __name__ == "__main__":
    # Test the data models
    sample_data = create_sample_earnings_data()
    print("Sample earnings data created successfully")
    print(f"Symbol: {sample_data.symbol}")
    print(f"Historical reports: {len(sample_data.historical_reports)}")
    print(f"Projected reports: {len(sample_data.projected_reports)}")
    
    # Test JSON serialization
    import json
    json_data = sample_data.to_dict()
    print("\nJSON serialization successful")
    print(f"Keys: {list(json_data.keys())}")