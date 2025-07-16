#!/usr/bin/env python3
"""
Real NASDAQ Earnings Data Scraper
Fetches actual past earnings data from NASDAQ for companies in the timeline
Uses the link pattern: https://www.nasdaq.com/market-activity/stocks/<company>/earnings
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor

class NASDAQEarningsScraper:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'calvin_earnings',
            'user': 'calvin_user',
            'password': 'calvin_pass'
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Get list of companies from earnings-icons directory
        self.companies = []
        if os.path.exists('earnings-icons'):
            for file in os.listdir('earnings-icons'):
                if file.endswith('.json'):
                    symbol = file.replace('.json', '')
                    self.companies.append(symbol)
        
        print(f"📊 Found {len(self.companies)} companies to scrape: {', '.join(sorted(self.companies))}")

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    def fetch_nasdaq_earnings_page(self, symbol: str) -> Optional[str]:
        """Fetch the NASDAQ earnings page for a given symbol"""
        url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
        
        try:
            print(f"🌐 Fetching NASDAQ earnings page for {symbol}: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ Successfully fetched page for {symbol}")
                return response.text
            elif response.status_code == 404:
                print(f"⚠️ Company {symbol} not found on NASDAQ")
                return None
            else:
                print(f"❌ Failed to fetch page for {symbol}. Status: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching {symbol}: {e}")
            return None

    def parse_earnings_table(self, html: str, symbol: str) -> List[Dict]:
        """Parse the earnings table from NASDAQ HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            earnings_data = []
            
            # Look for the earnings table - NASDAQ uses various table structures
            # Try multiple selectors to find the earnings data
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Skip if table has too few rows
                if len(rows) < 2:
                    continue
                    
                # Check if this looks like an earnings table
                header_row = rows[0]
                headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]
                
                # Look for earnings-related headers
                earnings_indicators = ['eps', 'earnings', 'actual', 'estimate', 'surprise', 'period', 'quarter']
                if not any(indicator in ' '.join(headers) for indicator in earnings_indicators):
                    continue
                
                print(f"📊 Found potential earnings table for {symbol} with headers: {headers}")
                
                # Parse data rows
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 4:  # Need at least date, actual, estimate, surprise
                        continue
                    
                    try:
                        # Extract text from cells
                        cell_texts = [cell.get_text().strip() for cell in cells]
                        
                        # Try to identify date, actual EPS, estimate, surprise
                        period_ending = self.extract_date(cell_texts[0]) if cell_texts[0] else None
                        if not period_ending:
                            continue
                            
                        # Look for EPS values (usually in format like $1.23 or 1.23)
                        actual_eps = self.extract_eps_value(cell_texts[1]) if len(cell_texts) > 1 else None
                        estimated_eps = self.extract_eps_value(cell_texts[2]) if len(cell_texts) > 2 else None
                        surprise = self.extract_surprise(cell_texts[3]) if len(cell_texts) > 3 else None
                        
                        if actual_eps is not None and estimated_eps is not None:
                            # Calculate surprise percentage if not provided
                            if surprise is None and estimated_eps != 0:
                                surprise = round(((actual_eps - estimated_eps) / estimated_eps) * 100, 1)
                            
                            # Determine beat/miss/meet
                            if actual_eps > estimated_eps:
                                beat_miss_meet = 'BEAT'
                            elif actual_eps < estimated_eps:
                                beat_miss_meet = 'MISS'
                            else:
                                beat_miss_meet = 'MEET'
                            
                            # Extract quarter and year from date
                            quarter, year = self.extract_quarter_year(period_ending)
                            
                            earnings_data.append({
                                'earnings_date': period_ending.strftime('%Y-%m-%d'),
                                'quarter': quarter,
                                'year': year,
                                'actual_eps': actual_eps,
                                'estimated_eps': estimated_eps,
                                'beat_miss_meet': beat_miss_meet,
                                'surprise_percent': surprise
                            })
                            
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ Error parsing row for {symbol}: {e}")
                        continue
                
                # If we found earnings data, break out of table loop
                if earnings_data:
                    break
                    
            print(f"✅ Parsed {len(earnings_data)} earnings records for {symbol}")
            return earnings_data
            
        except Exception as e:
            print(f"❌ Error parsing earnings data for {symbol}: {e}")
            return []

    def extract_date(self, date_str: str) -> Optional[datetime]:
        """Extract date from various date formats"""
        date_str = date_str.strip()
        
        # Common date patterns
        patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\w{3})\s+(\d{1,2}),?\s+(\d{4})',  # Jan 15, 2024
            r'Q(\d)\s+(\d{4})',  # Q1 2024
            r'(\d{4})\s+Q(\d)',  # 2024 Q1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if 'Q' in pattern:  # Quarter format
                        if 'Q(' in pattern:  # Q1 2024
                            quarter, year = match.groups()
                            # Convert quarter to end of quarter date
                            quarter_ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
                            month, day = quarter_ends[int(quarter)]
                            return datetime(int(year), month, day)
                        else:  # 2024 Q1
                            year, quarter = match.groups()
                            quarter_ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
                            month, day = quarter_ends[int(quarter)]
                            return datetime(int(year), month, day)
                    elif '/' in pattern:  # MM/DD/YYYY
                        month, day, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif '-' in pattern:  # YYYY-MM-DD
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif r'\w{3}' in pattern:  # Month name format
                        month_str, day, year = match.groups()
                        month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                   'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                        month = month_map.get(month_str.lower()[:3])
                        if month:
                            return datetime(int(year), month, int(day))
                except (ValueError, KeyError):
                    continue
        
        return None

    def extract_eps_value(self, eps_str: str) -> Optional[float]:
        """Extract EPS value from string"""
        eps_str = eps_str.strip()
        
        # Remove common prefixes/suffixes
        eps_str = re.sub(r'[$$£€¥]', '', eps_str)  # Remove currency symbols
        eps_str = re.sub(r'[(),]', '', eps_str)  # Remove parentheses and commas
        
        # Look for number pattern
        match = re.search(r'([+-]?\d+\.?\d*)', eps_str)
        if match:
            try:
                value = float(match.group(1))
                return round(value, 2)
            except ValueError:
                pass
        
        return None

    def extract_surprise(self, surprise_str: str) -> Optional[float]:
        """Extract surprise percentage from string"""
        surprise_str = surprise_str.strip()
        
        # Look for percentage
        match = re.search(r'([+-]?\d+\.?\d*)%?', surprise_str)
        if match:
            try:
                value = float(match.group(1))
                return round(value, 1)
            except ValueError:
                pass
        
        return None

    def extract_quarter_year(self, date: datetime) -> tuple:
        """Extract quarter and year from date"""
        quarter = (date.month - 1) // 3 + 1
        return quarter, date.year

    def insert_real_past_earnings(self, symbol: str, past_earnings: List[Dict]) -> bool:
        """Insert real past earnings data into database"""
        if not past_earnings:
            return False
            
        try:
            cursor = self.conn.cursor()
            
            # Get company ID
            cursor.execute("SELECT id FROM companies WHERE symbol = %s", (symbol,))
            result = cursor.fetchone()
            if not result:
                print(f"❌ Company {symbol} not found in database")
                return False
            
            company_id = result[0]
            inserted_count = 0
            
            # Insert each earnings record
            for earning in past_earnings:
                # Check if record already exists
                cursor.execute("""
                    SELECT id FROM earnings 
                    WHERE company_id = %s AND earnings_date = %s AND quarter = %s AND year = %s
                """, (company_id, earning['earnings_date'], earning['quarter'], earning['year']))
                
                if cursor.fetchone():
                    print(f"📝 Real earnings record for {symbol} {earning['year']} Q{earning['quarter']} already exists, updating")
                    # Update existing record with real data
                    cursor.execute("""
                        UPDATE earnings SET
                            actual_eps = %s, estimated_eps = %s, beat_miss_meet = %s, 
                            surprise_percent = %s, source_url = %s, updated_at = %s
                        WHERE company_id = %s AND earnings_date = %s AND quarter = %s AND year = %s
                    """, (
                        earning['actual_eps'], earning['estimated_eps'], earning['beat_miss_meet'],
                        earning['surprise_percent'], 
                        f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings",
                        datetime.now(), company_id, earning['earnings_date'], 
                        earning['quarter'], earning['year']
                    ))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO earnings (
                            company_id, symbol, earnings_date, quarter, year,
                            actual_eps, estimated_eps, beat_miss_meet, surprise_percent,
                            confidence_score, consensus_rating, announcement_time,
                            source_url, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        company_id, symbol, earning['earnings_date'], earning['quarter'], earning['year'],
                        earning['actual_eps'], earning['estimated_eps'], earning['beat_miss_meet'],
                        earning['surprise_percent'], 1.0, 'Buy', 'AMC',
                        f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings",
                        datetime.now(), datetime.now()
                    ))
                
                inserted_count += 1
                print(f"✅ Processed real earnings for {symbol} {earning['year']} Q{earning['quarter']}")
            
            self.conn.commit()
            cursor.close()
            print(f"✅ Successfully processed {inserted_count} real earnings records for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error inserting real earnings for {symbol}: {e}")
            self.conn.rollback()
            return False

    def scrape_company_earnings(self, symbol: str) -> bool:
        """Scrape real past earnings data for a single company"""
        try:
            print(f"\n🚀 Starting real earnings scraping for {symbol}")
            
            # Fetch NASDAQ page
            html = self.fetch_nasdaq_earnings_page(symbol)
            if not html:
                print(f"⚠️ Could not fetch NASDAQ page for {symbol}")
                return False
            
            # Parse earnings data
            past_earnings = self.parse_earnings_table(html, symbol)
            
            if not past_earnings:
                print(f"⚠️ No real earnings data found for {symbol}")
                return False
            
            # Insert into database
            success = self.insert_real_past_earnings(symbol, past_earnings)
            
            if success:
                print(f"✅ Successfully scraped {len(past_earnings)} real earnings for {symbol}")
                return True
            else:
                print(f"❌ Failed to insert real earnings for {symbol}")
                return False
                
        except Exception as e:
            print(f"❌ Error scraping real earnings for {symbol}: {e}")
            return False

    def scrape_all_companies(self):
        """Scrape real past earnings for all companies"""
        if not self.connect_to_database():
            return
        
        success_count = 0
        total_companies = len(self.companies)
        
        print(f"\n📈 Starting real earnings scraping for {total_companies} companies...")
        
        for i, symbol in enumerate(sorted(self.companies), 1):
            print(f"\n[{i}/{total_companies}] Processing {symbol}...")
            
            success = self.scrape_company_earnings(symbol)
            if success:
                success_count += 1
            
            # Respectful delay to avoid being blocked
            print(f"⏱️ Waiting 3 seconds before next request...")
            time.sleep(3)
        
        self.conn.close()
        
        print(f"\n📊 Real earnings scraping complete!")
        print(f"✅ Successfully scraped: {success_count}/{total_companies} companies")
        print(f"❌ Failed: {total_companies - success_count} companies")

def main():
    """Main function"""
    print("🚀 NASDAQ Real Earnings Scraper")
    print("=" * 50)
    
    scraper = NASDAQEarningsScraper()
    
    # Option to scrape single company for testing
    import sys
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        if symbol in scraper.companies:
            if scraper.connect_to_database():
                scraper.scrape_company_earnings(symbol)
                scraper.conn.close()
        else:
            print(f"❌ Company {symbol} not found in earnings-icons directory")
    else:
        scraper.scrape_all_companies()

if __name__ == "__main__":
    main()