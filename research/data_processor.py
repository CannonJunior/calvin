#!/usr/bin/env python3
"""
Earnings Data Processor

Processes raw earnings data to ensure all 36 required template fields are present
and correctly formatted for each company's earnings reports.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import json
import logging
import yfinance as yf
import requests
from dataclasses import asdict
import re

from earnings_collector import EarningsData

logger = logging.getLogger(__name__)

class EarningsDataProcessor:
    """Processes and enriches earnings data with all required fields"""
    
    def __init__(self):
        self.required_fields = [
            # Core earnings fields (1-18)
            'symbol', 'earnings_date', 'quarter', 'year', 'actual_eps', 'estimated_eps',
            'beat_miss_meet', 'surprise_percent', 'revenue_billions', 'revenue_growth_percent',
            'consensus_rating', 'confidence_score', 'source_url', 'data_verified_date',
            'stock_price_on_date', 'announcement_time', 'volume', 'date_earnings_report',
            # Market data fields (19-27)
            'market_cap', 'price_at_close_earnings_report_date', 'price_at_open_day_after_earnings_report_date',
            'percentage_stock_change', 'earnings_report_result', 'estimated_earnings_per_share',
            'reported_earnings_per_share', 'volume_day_of_earnings_report', 'volume_day_after_earnings_report',
            # Technical indicators (28-31)
            'moving_average_200_day', 'moving_average_50_day', 'week_52_high', 'week_52_low',
            # Company fundamentals (32-36)
            'market_sector', 'market_sub_sector', 'percentage_short_interest', 'dividend_yield',
            'ex_dividend_date'
        ]
        
        self.yfinance_cache = {}
    
    def validate_all_fields_present(self, earnings_data: EarningsData) -> Tuple[bool, List[str]]:
        """Validate that all 36 required fields are present in the earnings data"""
        data_dict = asdict(earnings_data)
        missing_fields = []
        
        for field in self.required_fields:
            if field not in data_dict:
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields
    
    def process_raw_earnings_data(self, raw_data: Dict[str, Any], 
                                 company_info: Dict[str, Any]) -> List[EarningsData]:
        """Process raw earnings data and ensure all 36 fields are present"""
        symbol = raw_data.get('symbol', company_info.get('symbol', ''))
        earnings_reports = raw_data.get('earnings_reports', [])
        
        processed_earnings = []
        
        for report in earnings_reports:
            # Create base earnings data
            earnings = self._create_base_earnings_data(report, company_info)
            
            # Enrich with missing data
            enriched_earnings = self._enrich_earnings_data(earnings, report)
            
            # Validate all fields are present
            is_valid, missing_fields = self.validate_all_fields_present(enriched_earnings)
            
            if not is_valid:
                logger.warning(f"Missing fields for {symbol}: {missing_fields}")
                # Fill missing fields with defaults
                enriched_earnings = self._fill_missing_fields(enriched_earnings, missing_fields)
            
            processed_earnings.append(enriched_earnings)
        
        return processed_earnings
    
    def _create_base_earnings_data(self, report: Dict[str, Any], 
                                  company_info: Dict[str, Any]) -> EarningsData:
        """Create base EarningsData structure from report"""
        symbol = report.get('symbol', company_info.get('symbol', ''))
        
        # Parse earnings date and extract quarter/year
        earnings_date = report.get('earnings_date') or report.get('date_earnings_report')
        quarter, year = self._extract_quarter_year(earnings_date)
        
        return EarningsData(
            # Core earnings fields (1-18)
            symbol=symbol,
            earnings_date=earnings_date or '',
            quarter=quarter,
            year=year,
            actual_eps=report.get('actual_eps') or report.get('reported_earnings_per_share'),
            estimated_eps=report.get('estimated_eps') or report.get('estimated_earnings_per_share'),
            beat_miss_meet=report.get('beat_miss_meet') or report.get('earnings_report_result'),
            surprise_percent=report.get('surprise_percent'),
            revenue_billions=report.get('revenue_billions'),
            revenue_growth_percent=report.get('revenue_growth_percent'),
            consensus_rating=report.get('consensus_rating'),
            confidence_score=report.get('confidence_score', 0.5),
            source_url=report.get('source_url', f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"),
            data_verified_date=report.get('data_verified_date', date.today().isoformat()),
            stock_price_on_date=report.get('stock_price_on_date'),
            announcement_time=report.get('announcement_time'),
            volume=report.get('volume'),
            date_earnings_report=earnings_date or report.get('date_earnings_report'),
            
            # Market data fields (19-27)
            market_cap=report.get('market_cap'),
            price_at_close_earnings_report_date=report.get('price_at_close_earnings_report_date'),
            price_at_open_day_after_earnings_report_date=report.get('price_at_open_day_after_earnings_report_date'),
            percentage_stock_change=report.get('percentage_stock_change'),
            earnings_report_result=report.get('earnings_report_result') or report.get('beat_miss_meet'),
            estimated_earnings_per_share=report.get('estimated_earnings_per_share') or report.get('estimated_eps'),
            reported_earnings_per_share=report.get('reported_earnings_per_share') or report.get('actual_eps'),
            volume_day_of_earnings_report=report.get('volume_day_of_earnings_report'),
            volume_day_after_earnings_report=report.get('volume_day_after_earnings_report'),
            
            # Technical indicators (28-31)
            moving_average_200_day=report.get('200_day_moving_average') or report.get('moving_average_200_day'),
            moving_average_50_day=report.get('50_day_moving_average') or report.get('moving_average_50_day'),
            week_52_high=report.get('52_week_high') or report.get('week_52_high'),
            week_52_low=report.get('52_week_low') or report.get('week_52_low'),
            
            # Company fundamentals (32-36)
            market_sector=company_info.get('gics_sector'),
            market_sub_sector=company_info.get('gics_sub_industry'),
            percentage_short_interest=report.get('percentage_short_interest'),
            dividend_yield=report.get('dividend_yield'),
            ex_dividend_date=report.get('ex_dividend_date')
        )
    
    def _enrich_earnings_data(self, earnings: EarningsData, report: Dict[str, Any]) -> EarningsData:
        """Enrich earnings data with additional calculated and fetched data"""
        
        # Calculate missing beat/miss/meet and surprise data
        if earnings.actual_eps is not None and earnings.estimated_eps is not None:
            if not earnings.beat_miss_meet:
                if earnings.actual_eps > earnings.estimated_eps:
                    earnings.beat_miss_meet = 'BEAT'
                    earnings.earnings_report_result = 'BEAT'
                elif earnings.actual_eps < earnings.estimated_eps:
                    earnings.beat_miss_meet = 'MISS'
                    earnings.earnings_report_result = 'MISS'
                else:
                    earnings.beat_miss_meet = 'MEET'
                    earnings.earnings_report_result = 'MEET'
            
            if earnings.surprise_percent is None and earnings.estimated_eps != 0:
                earnings.surprise_percent = round(
                    ((earnings.actual_eps - earnings.estimated_eps) / earnings.estimated_eps) * 100, 2
                )
        
        # Fetch additional data from yfinance if earnings date is available
        if earnings.earnings_date and earnings.earnings_date != '':
            yf_data = self._get_yfinance_data(earnings.symbol, earnings.earnings_date)
            earnings = self._merge_yfinance_data(earnings, yf_data)
        
        # Calculate quarter and year if missing
        if earnings.quarter == 0 or earnings.year == 0:
            if earnings.earnings_date:
                quarter, year = self._extract_quarter_year(earnings.earnings_date)
                if quarter and year:
                    earnings.quarter = quarter
                    earnings.year = year
        
        # Set default announcement time if not present
        if not earnings.announcement_time:
            earnings.announcement_time = 'AMC'  # Default to After Market Close
        
        return earnings
    
    def _get_yfinance_data(self, symbol: str, earnings_date: str) -> Dict[str, Any]:
        """Fetch data from yfinance for the earnings date"""
        if symbol in self.yfinance_cache:
            return self.yfinance_cache[symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data around earnings date
            earnings_dt = datetime.fromisoformat(earnings_date)
            start_date = earnings_dt - timedelta(days=5)
            end_date = earnings_dt + timedelta(days=5)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            # Get dividends
            dividends = ticker.dividends
            
            yf_data = {
                'info': info,
                'history': hist,
                'dividends': dividends
            }
            
            self.yfinance_cache[symbol] = yf_data
            return yf_data
            
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            return {}
    
    def _merge_yfinance_data(self, earnings: EarningsData, yf_data: Dict[str, Any]) -> EarningsData:
        """Merge yfinance data into earnings record"""
        if not yf_data:
            return earnings
        
        info = yf_data.get('info', {})
        hist = yf_data.get('history')
        dividends = yf_data.get('dividends')
        
        # Fill missing company data from yfinance info
        if not earnings.market_cap and 'marketCap' in info:
            earnings.market_cap = info['marketCap'] / 1e9  # Convert to billions
        
        if not earnings.week_52_high and 'fiftyTwoWeekHigh' in info:
            earnings.week_52_high = info['fiftyTwoWeekHigh']
        
        if not earnings.week_52_low and 'fiftyTwoWeekLow' in info:
            earnings.week_52_low = info['fiftyTwoWeekLow']
        
        if not earnings.dividend_yield and 'dividendYield' in info:
            earnings.dividend_yield = info['dividendYield'] * 100  # Convert to percentage
        
        if not earnings.moving_average_50_day and 'fiftyDayAverage' in info:
            earnings.moving_average_50_day = info['fiftyDayAverage']
        
        if not earnings.moving_average_200_day and 'twoHundredDayAverage' in info:
            earnings.moving_average_200_day = info['twoHundredDayAverage']
        
        if not earnings.percentage_short_interest and 'shortPercentOfFloat' in info:
            earnings.percentage_short_interest = info['shortPercentOfFloat'] * 100
        
        # Fill price and volume data from historical data
        if hist is not None and not hist.empty:
            earnings_dt = datetime.fromisoformat(earnings.earnings_date).date()
            
            # Find closest trading day to earnings date
            hist_dates = [d.date() for d in hist.index]
            closest_date = min(hist_dates, key=lambda x: abs((x - earnings_dt).days))
            
            if closest_date in hist_dates:
                idx = hist_dates.index(closest_date)
                hist_row = hist.iloc[idx]
                
                if not earnings.price_at_close_earnings_report_date:
                    earnings.price_at_close_earnings_report_date = hist_row['Close']
                
                if not earnings.stock_price_on_date:
                    earnings.stock_price_on_date = hist_row['Close']
                
                if not earnings.volume_day_of_earnings_report:
                    earnings.volume_day_of_earnings_report = int(hist_row['Volume'])
                
                # Get next day data if available
                if idx + 1 < len(hist):
                    next_row = hist.iloc[idx + 1]
                    if not earnings.price_at_open_day_after_earnings_report_date:
                        earnings.price_at_open_day_after_earnings_report_date = next_row['Open']
                    
                    if not earnings.volume_day_after_earnings_report:
                        earnings.volume_day_after_earnings_report = int(next_row['Volume'])
                    
                    # Calculate percentage change
                    if not earnings.percentage_stock_change:
                        close_price = hist_row['Close']
                        next_open = next_row['Open']
                        earnings.percentage_stock_change = round(
                            ((next_open - close_price) / close_price) * 100, 2
                        )
        
        # Find ex-dividend date closest to earnings date
        if dividends is not None and not dividends.empty and not earnings.ex_dividend_date:
            earnings_dt = datetime.fromisoformat(earnings.earnings_date).date()
            div_dates = [d.date() for d in dividends.index]
            
            if div_dates:
                closest_div_date = min(div_dates, key=lambda x: abs((x - earnings_dt).days))
                if abs((closest_div_date - earnings_dt).days) <= 90:  # Within 90 days
                    earnings.ex_dividend_date = closest_div_date.isoformat()
        
        return earnings
    
    def _extract_quarter_year(self, date_str: str) -> Tuple[int, int]:
        """Extract quarter and year from date string"""
        if not date_str:
            return 0, 0
        
        try:
            dt = datetime.fromisoformat(date_str)
            quarter = (dt.month - 1) // 3 + 1
            return quarter, dt.year
        except:
            return 0, 0
    
    def _fill_missing_fields(self, earnings: EarningsData, missing_fields: List[str]) -> EarningsData:
        """Fill missing fields with appropriate default values"""
        defaults = {
            'quarter': 0,
            'year': 0,
            'confidence_score': 0.3,  # Lower confidence for incomplete data
            'announcement_time': 'AMC',
            'consensus_rating': 'Hold',
            'earnings_date': '',
            'date_earnings_report': '',
            'data_verified_date': date.today().isoformat(),
            'source_url': f"https://www.nasdaq.com/market-activity/stocks/{earnings.symbol.lower()}/earnings"
        }
        
        earnings_dict = asdict(earnings)
        
        for field in missing_fields:
            if field in defaults:
                earnings_dict[field] = defaults[field]
            else:
                earnings_dict[field] = None
        
        # Recreate EarningsData object with filled fields
        return EarningsData(**earnings_dict)
    
    def get_field_completeness_report(self, earnings_list: List[EarningsData]) -> Dict[str, Any]:
        """Generate a report on field completeness across all earnings records"""
        if not earnings_list:
            return {'error': 'No earnings data provided'}
        
        field_counts = {field: 0 for field in self.required_fields}
        total_records = len(earnings_list)
        
        for earnings in earnings_list:
            earnings_dict = asdict(earnings)
            for field in self.required_fields:
                if field in earnings_dict and earnings_dict[field] is not None:
                    field_counts[field] += 1
        
        # Calculate percentages
        field_percentages = {
            field: round((count / total_records) * 100, 1)
            for field, count in field_counts.items()
        }
        
        # Overall completeness
        total_possible_fields = len(self.required_fields) * total_records
        total_filled_fields = sum(field_counts.values())
        overall_completeness = round((total_filled_fields / total_possible_fields) * 100, 1)
        
        return {
            'total_records': total_records,
            'total_required_fields': len(self.required_fields),
            'overall_completeness_percent': overall_completeness,
            'field_completeness': field_percentages,
            'missing_fields': [field for field, pct in field_percentages.items() if pct < 100],
            'complete_fields': [field for field, pct in field_percentages.items() if pct == 100]
        }

def main():
    """Test the data processor"""
    processor = EarningsDataProcessor()
    
    # Test with sample data
    sample_report = {
        'symbol': 'AAPL',
        'earnings_date': '2024-05-01',
        'actual_eps': 1.65,
        'estimated_eps': 1.63,
        'revenue_billions': 95.4
    }
    
    sample_company = {
        'symbol': 'AAPL',
        'gics_sector': 'Information Technology',
        'gics_sub_industry': 'Technology Hardware, Storage & Peripherals'
    }
    
    raw_data = {
        'symbol': 'AAPL',
        'earnings_reports': [sample_report]
    }
    
    processed = processor.process_raw_earnings_data(raw_data, sample_company)
    
    if processed:
        earnings = processed[0]
        is_valid, missing = processor.validate_all_fields_present(earnings)
        print(f"Valid: {is_valid}")
        print(f"Missing fields: {missing}")
        
        report = processor.get_field_completeness_report(processed)
        print(f"Completeness: {report['overall_completeness_percent']}%")

if __name__ == "__main__":
    main()