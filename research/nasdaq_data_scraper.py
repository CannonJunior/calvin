#!/usr/bin/env python3
"""
NASDAQ Data Scraper

Scrapes earnings data from NASDAQ.com to match the new earnings template format.
Handles both historical and projected earnings data.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, timedelta
import logging
import time
import yfinance as yf
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class NASDAQDataScraper:
    """Enhanced NASDAQ scraper for comprehensive earnings data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Cache for yfinance data to avoid repeated API calls
        self.yf_cache = {}
    
    def scrape_symbol_earnings(self, symbol: str) -> Dict[str, Any]:
        """Scrape comprehensive earnings data for a symbol"""
        logger.info(f"Scraping earnings data for {symbol}")
        
        # Get earnings page data
        earnings_page_data = self._scrape_earnings_page(symbol)
        
        # Get additional data from yfinance
        yf_data = self._get_yfinance_data(symbol)
        
        # Combine and structure the data
        combined_data = self._combine_data_sources(symbol, earnings_page_data, yf_data)
        
        return combined_data
    
    def _scrape_earnings_page(self, symbol: str) -> Dict[str, Any]:
        """Scrape the main earnings page for a symbol"""
        url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
        
        try:
            logger.debug(f"Fetching {url}")
            time.sleep(1)  # Rate limiting
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract earnings data
            data = {
                'symbol': symbol,
                'earnings_reports': [],
                'company_info': {}
            }
            
            # Extract earnings table data
            earnings_reports = self._extract_earnings_table_data(soup, symbol)
            data['earnings_reports'].extend(earnings_reports)
            
            # Extract additional company metrics
            company_metrics = self._extract_company_metrics(soup, symbol)
            data['company_info'].update(company_metrics)
            
            # Try to get forecast data
            forecast_data = self._extract_forecast_data(soup, symbol)
            data['earnings_reports'].extend(forecast_data)
            
            logger.info(f"Extracted {len(data['earnings_reports'])} earnings reports for {symbol}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error scraping earnings page for {symbol}: {e}")
            return {'symbol': symbol, 'earnings_reports': [], 'company_info': {}}
    
    def _extract_earnings_table_data(self, soup: BeautifulSoup, symbol: str) -> List[Dict[str, Any]]:
        """Extract earnings data from tables on the page"""
        reports = []
        
        # Look for various table patterns
        table_selectors = [
            'table.earnings-table',
            'table[class*="earnings"]',
            'div.earnings-forecast table',
            'table',  # Fallback to any table
        ]
        
        for selector in table_selectors:
            tables = soup.select(selector)
            
            for table in tables:
                if self._looks_like_earnings_table(table):
                    table_reports = self._parse_earnings_table(table, symbol)
                    reports.extend(table_reports)
        
        # Remove duplicates based on earnings_date
        unique_reports = []
        seen_dates = set()
        
        for report in reports:
            earnings_date = report.get('earnings_date')
            if earnings_date and earnings_date not in seen_dates:
                unique_reports.append(report)
                seen_dates.add(earnings_date)
            elif not earnings_date:
                unique_reports.append(report)
        
        return unique_reports
    
    def _looks_like_earnings_table(self, table) -> bool:
        """Check if a table looks like it contains earnings data"""
        if not table:
            return False
        
        table_text = table.get_text().lower()
        
        # Keywords that indicate earnings data
        earnings_keywords = [
            'earnings', 'eps', 'actual', 'estimate', 'surprise',
            'revenue', 'quarter', 'fiscal', 'reported'
        ]
        
        keyword_count = sum(1 for keyword in earnings_keywords if keyword in table_text)
        
        # Must have at least 3 earnings-related keywords
        return keyword_count >= 3
    
    def _parse_earnings_table(self, table, symbol: str) -> List[Dict[str, Any]]:
        """Parse individual earnings table"""
        reports = []
        
        rows = table.find_all('tr')
        if len(rows) < 2:  # Need at least header + 1 data row
            return reports
        
        # Extract headers
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower().replace(' ', '_') for th in header_row.find_all(['th', 'td'])]
        
        # Process data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 3:  # Need minimum columns
                continue
            
            report_data = self._extract_row_data(cells, headers, symbol)
            
            if report_data and report_data.get('earnings_date'):
                reports.append(report_data)
        
        return reports
    
    def _extract_row_data(self, cells: List, headers: List[str], symbol: str) -> Dict[str, Any]:
        """Extract data from a single table row"""
        data = {'symbol': symbol}
        
        for i, cell in enumerate(cells):
            cell_text = cell.get_text(strip=True)
            
            if i < len(headers):
                header = headers[i]
            else:
                header = f"column_{i}"
            
            # Parse different types of data based on content and header
            if 'date' in header or self._looks_like_date(cell_text):
                parsed_date = self._parse_date(cell_text)
                if parsed_date:
                    data['earnings_date'] = parsed_date
                    data['date_earnings_report'] = parsed_date
                    
                    # Extract quarter and year
                    try:
                        dt = datetime.fromisoformat(parsed_date)
                        data['quarter'] = (dt.month - 1) // 3 + 1
                        data['year'] = dt.year
                    except:
                        pass
            
            elif 'eps' in header or 'earnings' in header:
                eps_value = self._parse_float(cell_text)
                if eps_value is not None:
                    if 'actual' in header or 'reported' in header:
                        data['actual_eps'] = eps_value
                        data['reported_earnings_per_share'] = eps_value
                    elif 'estimate' in header or 'consensus' in header:
                        data['estimated_eps'] = eps_value
                        data['estimated_earnings_per_share'] = eps_value
            
            elif 'revenue' in header:
                revenue = self._parse_revenue(cell_text)
                if revenue is not None:
                    data['revenue_billions'] = revenue
            
            elif 'surprise' in header:
                surprise = self._parse_float(cell_text)
                if surprise is not None:
                    data['surprise_percent'] = surprise
            
            elif 'growth' in header and 'revenue' in header:
                growth = self._parse_float(cell_text)
                if growth is not None:
                    data['revenue_growth_percent'] = growth
            
            # Store raw data for debugging
            data[f'raw_{header}'] = cell_text
        
        # Calculate derived fields
        self._calculate_derived_fields(data)
        
        return data
    
    def _calculate_derived_fields(self, data: Dict[str, Any]):
        """Calculate derived fields from raw data"""
        
        # Calculate beat/miss/meet
        actual_eps = data.get('actual_eps')
        estimated_eps = data.get('estimated_eps')
        
        if actual_eps is not None and estimated_eps is not None:
            if actual_eps > estimated_eps:
                result = "BEAT"
            elif actual_eps < estimated_eps:
                result = "MISS"
            else:
                result = "MEET"
            
            data['beat_miss_meet'] = result
            data['earnings_report_result'] = result
            
            # Calculate surprise percentage if not already present
            if 'surprise_percent' not in data and estimated_eps != 0:
                surprise = round(((actual_eps - estimated_eps) / estimated_eps) * 100, 2)
                data['surprise_percent'] = surprise
        
        elif actual_eps is None and estimated_eps is not None:
            data['beat_miss_meet'] = "PROJECTED"
            data['earnings_report_result'] = "PROJECTED"
    
    def _extract_company_metrics(self, soup: BeautifulSoup, symbol: str) -> Dict[str, Any]:
        """Extract company metrics from the page"""
        metrics = {}
        
        # Look for key metrics in various page sections
        metric_patterns = {
            'market_cap': [r'market\s*cap[italization]*[:$\s]*([0-9.,]+[kmbt]?)', r'market\s*value[:$\s]*([0-9.,]+[kmbt]?)'],
            '52_week_high': [r'52\s*week\s*high[:$\s]*([0-9.,]+)', r'52w\s*high[:$\s]*([0-9.,]+)'],
            '52_week_low': [r'52\s*week\s*low[:$\s]*([0-9.,]+)', r'52w\s*low[:$\s]*([0-9.,]+)'],
            'dividend_yield': [r'dividend\s*yield[:$\s]*([0-9.,]+%?)', r'div\s*yield[:$\s]*([0-9.,]+%?)'],
            'volume': [r'volume[:$\s]*([0-9.,]+[kmbt]?)', r'avg\s*volume[:$\s]*([0-9.,]+[kmbt]?)'],
            'moving_avg_50': [r'50\s*day[:$\s]*([0-9.,]+)', r'50d\s*ma[:$\s]*([0-9.,]+)'],
            'moving_avg_200': [r'200\s*day[:$\s]*([0-9.,]+)', r'200d\s*ma[:$\s]*([0-9.,]+)'],
            'short_interest': [r'short\s*interest[:$\s]*([0-9.,]+%?)', r'short\s*%[:$\s]*([0-9.,]+%?)']
        }
        
        page_text = soup.get_text().lower()
        
        for metric, patterns in metric_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    value = self._parse_float(match.group(1))
                    if value is not None:
                        # Map to template field names
                        if metric == '52_week_high':
                            metrics['week_52_high'] = value
                        elif metric == '52_week_low':
                            metrics['week_52_low'] = value
                        elif metric == 'moving_avg_50':
                            metrics['moving_avg_50_day'] = value
                        elif metric == 'moving_avg_200':
                            metrics['moving_avg_200_day'] = value
                        elif metric == 'short_interest':
                            metrics['percentage_short_interest'] = value
                        else:
                            metrics[metric] = value
                        break
        
        return metrics
    
    def _extract_forecast_data(self, soup: BeautifulSoup, symbol: str) -> List[Dict[str, Any]]:
        """Extract forecast/projected earnings data"""
        forecasts = []
        
        # Look for forecast sections
        forecast_sections = soup.find_all(['div', 'section'], class_=re.compile(r'forecast|upcoming|projected'))
        
        for section in forecast_sections:
            section_forecasts = self._parse_forecast_section(section, symbol)
            forecasts.extend(section_forecasts)
        
        return forecasts
    
    def _parse_forecast_section(self, section, symbol: str) -> List[Dict[str, Any]]:
        """Parse a forecast section"""
        forecasts = []
        
        # Look for tables or structured data in the forecast section
        tables = section.find_all('table')
        
        for table in tables:
            if self._looks_like_earnings_table(table):
                table_forecasts = self._parse_earnings_table(table, symbol)
                
                # Mark as projected if no actual_eps
                for forecast in table_forecasts:
                    if forecast.get('actual_eps') is None:
                        forecast['beat_miss_meet'] = "PROJECTED"
                        forecast['earnings_report_result'] = "PROJECTED"
                        forecast['confidence_score'] = 0.7
                
                forecasts.extend(table_forecasts)
        
        return forecasts
    
    def _get_yfinance_data(self, symbol: str) -> Dict[str, Any]:
        """Get additional data from yfinance"""
        if symbol in self.yf_cache:
            return self.yf_cache[symbol]
        
        try:
            logger.debug(f"Fetching yfinance data for {symbol}")
            
            ticker = yf.Ticker(symbol)
            
            # Get company info
            info = ticker.info
            
            # Get recent historical data (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            hist = ticker.history(start=start_date, end=end_date)
            
            # Get dividends
            dividends = ticker.dividends
            
            yf_data = {
                'info': info,
                'history': hist,
                'dividends': dividends,
                'symbol': symbol
            }
            
            self.yf_cache[symbol] = yf_data
            return yf_data
            
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            return {}
    
    def _combine_data_sources(self, symbol: str, nasdaq_data: Dict[str, Any], 
                             yf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine NASDAQ and yfinance data"""
        
        # Start with NASDAQ data
        combined = nasdaq_data.copy()
        
        if not yf_data:
            return combined
        
        info = yf_data.get('info', {})
        hist = yf_data.get('history')
        dividends = yf_data.get('dividends')
        
        # Enhance each earnings report with yfinance data
        for report in combined['earnings_reports']:
            self._enhance_report_with_yfinance(report, info, hist, dividends)
        
        # Add company information
        if 'company_info' not in combined:
            combined['company_info'] = {}
        
        # Add yfinance company data
        if 'longName' in info:
            combined['company_info']['company_name'] = info['longName']
        if 'sector' in info:
            combined['company_info']['sector'] = info['sector']
        if 'industry' in info:
            combined['company_info']['sub_sector'] = info['industry']
        
        return combined
    
    def _enhance_report_with_yfinance(self, report: Dict[str, Any], info: Dict[str, Any],
                                     hist, dividends):
        """Enhance a single earnings report with yfinance data"""
        
        # Add missing company metrics from yfinance
        if 'market_cap' not in report and 'marketCap' in info:
            report['market_cap'] = info['marketCap'] / 1e9  # Convert to billions
        
        if 'week_52_high' not in report and 'fiftyTwoWeekHigh' in info:
            report['week_52_high'] = info['fiftyTwoWeekHigh']
        
        if 'week_52_low' not in report and 'fiftyTwoWeekLow' in info:
            report['week_52_low'] = info['fiftyTwoWeekLow']
        
        if 'dividend_yield' not in report and 'dividendYield' in info:
            report['dividend_yield'] = info['dividendYield'] * 100 if info['dividendYield'] else None
        
        if 'moving_avg_50_day' not in report and 'fiftyDayAverage' in info:
            report['moving_avg_50_day'] = info['fiftyDayAverage']
        
        if 'moving_avg_200_day' not in report and 'twoHundredDayAverage' in info:
            report['moving_avg_200_day'] = info['twoHundredDayAverage']
        
        if 'percentage_short_interest' not in report and 'shortPercentOfFloat' in info:
            report['percentage_short_interest'] = info['shortPercentOfFloat'] * 100 if info['shortPercentOfFloat'] else None
        
        # Add stock price and volume data based on earnings date
        earnings_date = report.get('earnings_date')
        if earnings_date and hist is not None and not hist.empty:
            self._add_price_volume_data(report, hist, earnings_date)
        
        # Add ex-dividend date if close to earnings date
        if earnings_date and dividends is not None and not dividends.empty:
            ex_div_date = self._find_closest_ex_dividend_date(earnings_date, dividends)
            if ex_div_date:
                report['ex_dividend_date'] = ex_div_date
        
        # Set default values for missing fields
        self._set_default_values(report)
    
    def _add_price_volume_data(self, report: Dict[str, Any], hist, earnings_date: str):
        """Add price and volume data from historical data"""
        try:
            earnings_dt = datetime.fromisoformat(earnings_date).date()
            hist_dates = [d.date() for d in hist.index]
            
            # Find closest trading day
            closest_date = min(hist_dates, key=lambda x: abs((x - earnings_dt).days))
            
            if abs((closest_date - earnings_dt).days) <= 3:  # Within 3 days
                idx = hist_dates.index(closest_date)
                hist_row = hist.iloc[idx]
                
                # Add price data
                if 'stock_price_on_date' not in report:
                    report['stock_price_on_date'] = hist_row['Close']
                
                if 'price_at_close_earnings_report_date' not in report:
                    report['price_at_close_earnings_report_date'] = hist_row['Close']
                
                if 'volume_day_of_earnings_report' not in report:
                    report['volume_day_of_earnings_report'] = int(hist_row['Volume'])
                
                # Get next day data if available
                if idx + 1 < len(hist):
                    next_row = hist.iloc[idx + 1]
                    
                    if 'price_at_open_day_after_earnings_report_date' not in report:
                        report['price_at_open_day_after_earnings_report_date'] = next_row['Open']
                    
                    if 'volume_day_after_earnings_report' not in report:
                        report['volume_day_after_earnings_report'] = int(next_row['Volume'])
                    
                    # Calculate percentage change
                    if 'percentage_stock_change' not in report:
                        close_price = hist_row['Close']
                        next_open = next_row['Open']
                        if close_price and next_open:
                            change = round(((next_open - close_price) / close_price) * 100, 2)
                            report['percentage_stock_change'] = change
        
        except Exception as e:
            logger.error(f"Error adding price/volume data: {e}")
    
    def _find_closest_ex_dividend_date(self, earnings_date: str, dividends) -> Optional[str]:
        """Find ex-dividend date closest to earnings date"""
        try:
            earnings_dt = datetime.fromisoformat(earnings_date).date()
            div_dates = [d.date() for d in dividends.index]
            
            if not div_dates:
                return None
            
            # Find closest dividend date within 90 days
            closest_date = min(div_dates, key=lambda x: abs((x - earnings_dt).days))
            
            if abs((closest_date - earnings_dt).days) <= 90:
                return closest_date.isoformat()
            
            return None
            
        except Exception:
            return None
    
    def _set_default_values(self, report: Dict[str, Any]):
        """Set default values for missing fields"""
        defaults = {
            'consensus_rating': 'Hold',
            'confidence_score': 0.7,
            'announcement_time': 'AMC',
            'data_verified_date': date.today().isoformat(),
            'source_url': f"https://www.nasdaq.com/market-activity/stocks/{report['symbol'].lower()}/earnings"
        }
        
        for key, value in defaults.items():
            if key not in report or report[key] is None:
                report[key] = value
    
    # Utility methods
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text or len(text) < 6:
            return False
        
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}'
        ]
        
        return any(re.search(pattern, text) for pattern in date_patterns)
    
    def _parse_date(self, text: str) -> Optional[str]:
        """Parse date from various formats"""
        if not text or text in ['-', 'N/A', '']:
            return None
        
        try:
            # Common date formats
            formats = [
                "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d",
                "%b %d, %Y", "%B %d, %Y", "%d %b %Y",
                "%d-%b-%Y", "%Y/%m/%d"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(text.strip(), fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _parse_float(self, text: str) -> Optional[float]:
        """Parse float from text with various formats"""
        if not text or text.strip() in ['-', 'N/A', '', '--']:
            return None
        
        try:
            # Clean the text
            cleaned = re.sub(r'[,$%()"]', '', text.strip())
            
            # Handle negative values in parentheses
            if text.strip().startswith('(') and text.strip().endswith(')'):
                cleaned = '-' + cleaned
            
            # Handle suffixes
            multiplier = 1
            if cleaned.lower().endswith('k'):
                multiplier = 1000
                cleaned = cleaned[:-1]
            elif cleaned.lower().endswith('m'):
                multiplier = 1000000
                cleaned = cleaned[:-1]
            elif cleaned.lower().endswith('b'):
                multiplier = 1000000000
                cleaned = cleaned[:-1]
            elif cleaned.lower().endswith('t'):
                multiplier = 1000000000000
                cleaned = cleaned[:-1]
            
            return float(cleaned) * multiplier
            
        except (ValueError, AttributeError):
            return None
    
    def _parse_revenue(self, text: str) -> Optional[float]:
        """Parse revenue specifically, converting to billions"""
        value = self._parse_float(text)
        if value is None:
            return None
        
        # If value is already in billions (> 1), return as is
        # If in millions (< 1000), convert to billions
        if value < 1000:
            return round(value / 1000, 2)
        elif value < 1000000:
            return round(value / 1000, 2)
        else:
            return round(value / 1000000000, 2)


def main():
    """Test the scraper"""
    scraper = NASDAQDataScraper()
    
    test_symbols = ['AAPL']
    
    for symbol in test_symbols:
        print(f"\n=== Testing {symbol} ===")
        data = scraper.scrape_symbol_earnings(symbol)
        
        print(f"Found {len(data.get('earnings_reports', []))} earnings reports")
        
        if data.get('earnings_reports'):
            print("Sample report fields:")
            sample_report = data['earnings_reports'][0]
            for key, value in sample_report.items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()