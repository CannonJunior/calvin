#!/usr/bin/env python3
"""
NASDAQ Earnings Data Scraper

Scrapes earnings data from NASDAQ.com earnings pages to extract all required fields
for the earnings template.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging
import time

logger = logging.getLogger(__name__)

class NASDAQScraper:
    """Scraper for NASDAQ earnings data"""
    
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
    
    def scrape_earnings_page(self, symbol: str) -> Dict[str, Any]:
        """Scrape NASDAQ earnings page for a given symbol"""
        url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
        
        try:
            logger.info(f"Scraping NASDAQ earnings for {symbol}")
            time.sleep(2)  # Rate limiting
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract earnings data from the page
            earnings_data = self._extract_earnings_data(soup, symbol)
            
            return earnings_data
            
        except Exception as e:
            logger.error(f"Error scraping NASDAQ data for {symbol}: {e}")
            return {}
    
    def _extract_earnings_data(self, soup: BeautifulSoup, symbol: str) -> Dict[str, Any]:
        """Extract earnings data from NASDAQ page HTML"""
        data = {
            'symbol': symbol,
            'earnings_reports': []
        }
        
        # Extract earnings table data
        earnings_table = soup.find('table', {'class': 'earnings-table'}) or \
                        soup.find('div', {'class': 'earnings-forecast'}) or \
                        soup.find_all('table')
        
        if earnings_table:
            if isinstance(earnings_table, list):
                for table in earnings_table:
                    reports = self._parse_earnings_table(table, symbol)
                    data['earnings_reports'].extend(reports)
            else:
                reports = self._parse_earnings_table(earnings_table, symbol)
                data['earnings_reports'].extend(reports)
        
        # Extract additional company data
        data.update(self._extract_company_metrics(soup, symbol))
        
        return data
    
    def _parse_earnings_table(self, table, symbol: str) -> List[Dict[str, Any]]:
        """Parse earnings table to extract individual earnings reports"""
        reports = []
        
        if not table:
            return reports
        
        rows = table.find_all('tr')
        headers = []
        
        for row in rows:
            cells = row.find_all(['th', 'td'])
            
            # Extract headers
            if not headers and cells and cells[0].name == 'th':
                headers = [cell.get_text(strip=True).lower().replace(' ', '_') for cell in cells]
                continue
            
            if len(cells) >= 4:  # Minimum expected columns
                report_data = self._extract_earnings_row_data(cells, headers, symbol)
                if report_data:
                    reports.append(report_data)
        
        return reports
    
    def _extract_earnings_row_data(self, cells, headers: List[str], symbol: str) -> Dict[str, Any]:
        """Extract data from a single earnings table row"""
        data = {'symbol': symbol}
        
        try:
            # Map common column patterns
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                
                if i < len(headers):
                    header = headers[i]
                else:
                    header = f"column_{i}"
                
                # Extract specific data based on content patterns
                if 'date' in header or self._looks_like_date(text):
                    data['earnings_date'] = self._parse_date(text)
                    data['date_earnings_report'] = self._parse_date(text)
                
                elif 'eps' in header.lower() or 'earnings' in header.lower():
                    if 'actual' in header or 'reported' in header:
                        data['actual_eps'] = self._parse_float(text)
                        data['reported_earnings_per_share'] = self._parse_float(text)
                    elif 'estimate' in header or 'consensus' in header:
                        data['estimated_eps'] = self._parse_float(text)
                        data['estimated_earnings_per_share'] = self._parse_float(text)
                
                elif 'revenue' in header.lower():
                    revenue_val = self._parse_revenue(text)
                    if revenue_val:
                        data['revenue_billions'] = revenue_val
                
                elif 'surprise' in header.lower():
                    data['surprise_percent'] = self._parse_float(text)
                
                # Store raw cell data as well
                data[f'raw_{header}'] = text
            
            # Calculate derived fields
            if 'actual_eps' in data and 'estimated_eps' in data:
                actual = data['actual_eps']
                estimated = data['estimated_eps']
                
                if actual is not None and estimated is not None:
                    if actual > estimated:
                        data['beat_miss_meet'] = 'BEAT'
                        data['earnings_report_result'] = 'BEAT'
                    elif actual < estimated:
                        data['beat_miss_meet'] = 'MISS'
                        data['earnings_report_result'] = 'MISS'
                    else:
                        data['beat_miss_meet'] = 'MEET'
                        data['earnings_report_result'] = 'MEET'
                    
                    if estimated != 0:
                        data['surprise_percent'] = round(((actual - estimated) / estimated) * 100, 2)
            
            # Add metadata
            data['source_url'] = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
            data['data_verified_date'] = date.today().isoformat()
            data['confidence_score'] = 0.7 if len([k for k in data.keys() if data[k] is not None]) > 5 else 0.5
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing earnings row for {symbol}: {e}")
            return {}
    
    def _extract_company_metrics(self, soup: BeautifulSoup, symbol: str) -> Dict[str, Any]:
        """Extract additional company metrics from the page"""
        metrics = {}
        
        # Look for various patterns of financial data
        metric_patterns = {
            'market_cap': [r'market.cap', r'market.capitalization'],
            '52_week_high': [r'52.week.high', r'52w.high'],
            '52_week_low': [r'52.week.low', r'52w.low'],
            'dividend_yield': [r'dividend.yield', r'div.yield'],
            'volume': [r'volume', r'avg.volume'],
            '50_day_moving_average': [r'50.day', r'50d.ma'],
            '200_day_moving_average': [r'200.day', r'200d.ma'],
            'percentage_short_interest': [r'short.interest', r'short.%']
        }
        
        # Extract from various page sections
        for key, patterns in metric_patterns.items():
            value = self._find_metric_value(soup, patterns)
            if value is not None:
                metrics[key] = value
        
        return metrics
    
    def _find_metric_value(self, soup: BeautifulSoup, patterns: List[str]) -> Optional[float]:
        """Find a metric value using regex patterns"""
        for pattern in patterns:
            # Look in text content
            text = soup.get_text().lower()
            match = re.search(f'{pattern}[:\s]*([0-9,.]+[kmb]?)', text)
            if match:
                return self._parse_float(match.group(1))
        
        return None
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _parse_date(self, text: str) -> Optional[str]:
        """Parse date from various formats"""
        if not text or text == '-':
            return None
        
        try:
            # Common date formats
            formats = [
                "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d",
                "%b %d, %Y", "%B %d, %Y", "%d-%b-%Y"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(text.strip(), fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            
            # If no format matches, return as-is if it looks like a date
            if self._looks_like_date(text):
                return text.strip()
            
        except Exception:
            pass
        
        return None
    
    def _parse_float(self, text: str) -> Optional[float]:
        """Parse float from text with various formats"""
        if not text or text == '-' or text.lower() == 'n/a':
            return None
        
        try:
            # Remove common formatting
            cleaned = re.sub(r'[,$%()]', '', text.strip())
            
            # Handle K, M, B suffixes
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
            
            return float(cleaned) * multiplier
            
        except (ValueError, AttributeError):
            return None
    
    def _parse_revenue(self, text: str) -> Optional[float]:
        """Parse revenue specifically, converting to billions"""
        value = self._parse_float(text)
        if value is None:
            return None
        
        # If value seems to be in millions, convert to billions
        if value > 1000 and value < 1000000:
            return round(value / 1000, 2)
        
        return value

def main():
    """Test the scraper"""
    scraper = NASDAQScraper()
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        print(f"\n=== Testing {symbol} ===")
        data = scraper.scrape_earnings_page(symbol)
        print(json.dumps(data, indent=2, default=str))

if __name__ == "__main__":
    main()