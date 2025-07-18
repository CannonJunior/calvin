"""
NASDAQ earnings data scraper for S&P 500 companies.
"""

import requests
import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from dataclasses import dataclass


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for web scraping."""
    base_url: str = "https://www.nasdaq.com"
    earnings_path: str = "/market-activity/stocks/{symbol}/earnings"
    headers: Dict[str, str] = None
    delay_between_requests: float = 2.0
    max_retries: int = 3
    timeout: int = 30
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }


class NasdaqEarningsScraper:
    """Scraper for NASDAQ earnings data with rate limiting."""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 60  # 1 minute window
        self.max_requests_per_window = 30  # Max 30 requests per minute
        
    def get_earnings_url(self, symbol: str) -> str:
        """Generate NASDAQ earnings URL for a symbol."""
        return self.config.base_url + self.config.earnings_path.format(symbol=symbol.lower())
    
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting to respect server resources."""
        current_time = time.time()
        
        # Reset request count if window has passed
        if current_time - self.last_request_time > self.rate_limit_window:
            self.request_count = 0
            
        # Check if we've exceeded rate limit
        if self.request_count >= self.max_requests_per_window:
            wait_time = self.rate_limit_window - (current_time - self.last_request_time)
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                self.request_count = 0
        
        # Enforce minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.config.delay_between_requests:
            sleep_time = self.config.delay_between_requests - time_since_last
            time.sleep(sleep_time)
        
        self.request_count += 1
        self.last_request_time = time.time()

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with retry logic and rate limiting."""
        for attempt in range(self.config.max_retries):
            try:
                # Enforce rate limiting before each request
                self._enforce_rate_limit()
                
                logger.info(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.config.timeout)
                
                # Handle rate limiting responses
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited by server. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff for retries
                    backoff_time = self.config.delay_between_requests * (2 ** attempt)
                    time.sleep(min(backoff_time, 30))  # Cap at 30 seconds
                else:
                    logger.error(f"Failed to fetch {url} after {self.config.max_retries} attempts")
                    return None
    
    def extract_earnings_data(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract earnings data from NASDAQ page."""
        data = {
            'historical_earnings': [],
            'projected_earnings': [],
            'company_info': {},
            'current_metrics': {}
        }
        
        try:
            # Extract company name
            company_name_elem = soup.find('h1', class_='symbol-page-header__name')
            if company_name_elem:
                data['company_info']['name'] = company_name_elem.get_text(strip=True)
            
            # Extract current stock price
            price_elem = soup.find('span', class_='symbol-page-header__price')
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace('$', '').replace(',', '')
                try:
                    data['current_metrics']['current_price'] = float(price_text)
                except ValueError:
                    pass
            
            # Extract earnings table data
            earnings_tables = soup.find_all('table', class_='earnings-table')
            for table in earnings_tables:
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:
                        earnings_entry = self._parse_earnings_row(cells)
                        if earnings_entry:
                            # Determine if historical or projected based on date
                            if self._is_historical_date(earnings_entry.get('date')):
                                data['historical_earnings'].append(earnings_entry)
                            else:
                                data['projected_earnings'].append(earnings_entry)
            
            # Extract additional metrics
            self._extract_additional_metrics(soup, data)
            
        except Exception as e:
            logger.error(f"Error extracting earnings data: {e}")
        
        return data
    
    def _parse_earnings_row(self, cells: List) -> Optional[Dict]:
        """Parse a single earnings table row."""
        try:
            earnings_data = {}
            
            # Date (usually first column)
            date_text = cells[0].get_text(strip=True)
            earnings_data['date'] = self._parse_date(date_text)
            
            # EPS data (varies by table structure)
            if len(cells) >= 3:
                # Estimated EPS
                est_eps_text = cells[1].get_text(strip=True).replace('$', '')
                try:
                    earnings_data['estimated_eps'] = float(est_eps_text) if est_eps_text != 'N/A' else 0.0
                except ValueError:
                    earnings_data['estimated_eps'] = 0.0
                
                # Reported EPS
                rep_eps_text = cells[2].get_text(strip=True).replace('$', '')
                try:
                    earnings_data['reported_eps'] = float(rep_eps_text) if rep_eps_text != 'N/A' else 0.0
                except ValueError:
                    earnings_data['reported_eps'] = 0.0
                
                # Beat or miss
                if earnings_data['reported_eps'] > earnings_data['estimated_eps']:
                    earnings_data['beat_or_miss'] = 'beat'
                elif earnings_data['reported_eps'] < earnings_data['estimated_eps']:
                    earnings_data['beat_or_miss'] = 'miss'
                else:
                    earnings_data['beat_or_miss'] = 'meet'
            
            return earnings_data if earnings_data.get('date') else None
            
        except Exception as e:
            logger.warning(f"Error parsing earnings row: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date from various formats."""
        try:
            # Remove extra whitespace and common prefixes
            date_text = re.sub(r'^(Q[1-4]\s+)', '', date_text.strip())
            
            # Try common date formats
            date_formats = [
                '%b %d, %Y',      # Jan 24, 2024
                '%B %d, %Y',      # January 24, 2024
                '%m/%d/%Y',       # 01/24/2024
                '%Y-%m-%d',       # 2024-01-24
                '%d-%b-%Y',       # 24-Jan-2024
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_text, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_text}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_text}': {e}")
            return None
    
    def _is_historical_date(self, date_str: Optional[str]) -> bool:
        """Determine if a date is historical (past) or projected (future)."""
        if not date_str:
            return False
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj < datetime.now()
        except ValueError:
            return False
    
    def _extract_additional_metrics(self, soup: BeautifulSoup, data: Dict) -> None:
        """Extract additional financial metrics from the page."""
        try:
            # Market cap
            market_cap_elem = soup.find('span', string=re.compile(r'Market Cap', re.I))
            if market_cap_elem:
                market_cap_value = market_cap_elem.find_next('span')
                if market_cap_value:
                    data['current_metrics']['market_cap'] = self._parse_financial_value(
                        market_cap_value.get_text(strip=True)
                    )
            
            # Volume
            volume_elem = soup.find('span', string=re.compile(r'Volume', re.I))
            if volume_elem:
                volume_value = volume_elem.find_next('span')
                if volume_value:
                    data['current_metrics']['volume'] = self._parse_financial_value(
                        volume_value.get_text(strip=True)
                    )
            
            # 52-week high/low
            high_elem = soup.find('span', string=re.compile(r'52.*High', re.I))
            if high_elem:
                high_value = high_elem.find_next('span')
                if high_value:
                    data['current_metrics']['52_week_high'] = self._parse_price(
                        high_value.get_text(strip=True)
                    )
            
            low_elem = soup.find('span', string=re.compile(r'52.*Low', re.I))
            if low_elem:
                low_value = low_elem.find_next('span')
                if low_value:
                    data['current_metrics']['52_week_low'] = self._parse_price(
                        low_value.get_text(strip=True)
                    )
            
        except Exception as e:
            logger.warning(f"Error extracting additional metrics: {e}")
    
    def _parse_financial_value(self, value_text: str) -> float:
        """Parse financial values with suffixes (B, M, K)."""
        try:
            value_text = value_text.replace('$', '').replace(',', '').strip()
            
            if value_text.endswith('B'):
                return float(value_text[:-1]) * 1_000_000_000
            elif value_text.endswith('M'):
                return float(value_text[:-1]) * 1_000_000
            elif value_text.endswith('K'):
                return float(value_text[:-1]) * 1_000
            else:
                return float(value_text)
        except ValueError:
            return 0.0
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price values."""
        try:
            return float(price_text.replace('$', '').replace(',', '').strip())
        except ValueError:
            return 0.0
    
    def scrape_company_earnings(self, symbol: str) -> Optional[Dict]:
        """Scrape earnings data for a single company."""
        url = self.get_earnings_url(symbol)
        soup = self.fetch_page(url)
        
        if soup is None:
            return None
        
        # Rate limiting is already handled in fetch_page method
        
        earnings_data = self.extract_earnings_data(soup)
        earnings_data['symbol'] = symbol.upper()
        earnings_data['scrape_timestamp'] = datetime.now().isoformat()
        earnings_data['source_url'] = url
        
        return earnings_data


if __name__ == "__main__":
    # Demo usage
    scraper = NasdaqEarningsScraper()
    
    # Test with Apple
    print("Testing NASDAQ scraper with AAPL...")
    aapl_data = scraper.scrape_company_earnings("AAPL")
    
    if aapl_data:
        print(f"Successfully scraped data for {aapl_data.get('symbol')}")
        print(f"Historical earnings: {len(aapl_data.get('historical_earnings', []))}")
        print(f"Projected earnings: {len(aapl_data.get('projected_earnings', []))}")
    else:
        print("Failed to scrape AAPL data")