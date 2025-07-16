#!/usr/bin/env python3
"""
NASDAQ API Earnings Data Scraper
Uses the NASDAQ API endpoints to fetch real earnings data
Based on discovered API endpoints: https://qcapi.nasdaq.com/api
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

class NASDAQAPIEarningsScraper:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'calvin_earnings',
            'user': 'calvin_user',
            'password': 'calvin_pass'
        }
        
        # NASDAQ API configuration (discovered from webpage)
        self.api_base = "https://qcapi.nasdaq.com/api"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nasdaq.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        })
        
        # Get list of companies from earnings-icons directory
        self.companies = []
        if os.path.exists('earnings-icons'):
            for file in os.listdir('earnings-icons'):
                if file.endswith('.json'):
                    symbol = file.replace('.json', '')
                    self.companies.append(symbol)
        
        print(f"📊 Found {len(self.companies)} companies to scrape via API: {', '.join(sorted(self.companies))}")

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    def fetch_earnings_data_api(self, symbol: str) -> Optional[Dict]:
        """Fetch earnings data from NASDAQ API"""
        # Try multiple possible endpoints for earnings data
        endpoints_to_try = [
            f"/quote/{symbol.upper()}/earnings",
            f"/quote/{symbol.upper()}/financials", 
            f"/quote/{symbol.upper()}/info",
            f"/quote/{symbol}/earnings",
            f"/earnings/{symbol}",
            f"/company/{symbol}/earnings"
        ]
        
        for endpoint in endpoints_to_try:
            url = f"{self.api_base}{endpoint}"
            
            try:
                print(f"🌐 Trying API endpoint: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ Successfully fetched data from {endpoint}")
                        
                        # Save raw response for debugging
                        debug_file = f"debug_{symbol}_api_response.json"
                        with open(debug_file, 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"💾 Saved API response to: {debug_file}")
                        
                        return data
                        
                    except json.JSONDecodeError:
                        print(f"⚠️ Invalid JSON response from {endpoint}")
                        continue
                        
                elif response.status_code == 404:
                    print(f"⚠️ Endpoint not found: {endpoint}")
                    continue
                    
                else:
                    print(f"⚠️ HTTP {response.status_code} from {endpoint}")
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error for {endpoint}: {e}")
                continue
        
        print(f"❌ No working API endpoints found for {symbol}")
        return None

    def parse_api_earnings_data(self, data: Dict, symbol: str) -> List[Dict]:
        """Parse earnings data from API response"""
        earnings_list = []
        
        try:
            # Look for earnings data in various possible structures
            possible_keys = [
                'earnings', 'earningsData', 'earnings_data', 
                'results', 'data', 'earningsHistory',
                'earningsTable', 'quarterlyEarnings', 'historical'
            ]
            
            earnings_data = None
            for key in possible_keys:
                if key in data:
                    earnings_data = data[key]
                    print(f"📊 Found earnings data under key: {key}")
                    break
            
            if not earnings_data:
                # Sometimes data is at root level
                if isinstance(data, list):
                    earnings_data = data
                elif 'rows' in data:
                    earnings_data = data['rows']
                elif 'data' in data and isinstance(data['data'], list):
                    earnings_data = data['data']
            
            if not earnings_data:
                print(f"⚠️ No earnings data structure found for {symbol}")
                return []
            
            # Parse each earnings record
            for record in earnings_data:
                if not isinstance(record, dict):
                    continue
                
                # Extract earnings information with various possible field names
                date_fields = ['date', 'reportDate', 'earningsDate', 'period', 'periodEnding']
                actual_fields = ['actual', 'actualEps', 'actual_eps', 'reportedEPS', 'eps']
                estimate_fields = ['estimate', 'estimateEps', 'estimated_eps', 'consensusEPS', 'consensus']
                surprise_fields = ['surprise', 'surprisePercent', 'surprise_percent', 'surprisePct']
                
                # Find date
                earnings_date = None
                for field in date_fields:
                    if field in record and record[field]:
                        try:
                            if isinstance(record[field], str):
                                earnings_date = datetime.strptime(record[field][:10], '%Y-%m-%d')
                            else:
                                earnings_date = datetime.fromtimestamp(record[field] / 1000) if record[field] > 1000000000000 else datetime.fromtimestamp(record[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                if not earnings_date:
                    continue
                
                # Find actual EPS
                actual_eps = None
                for field in actual_fields:
                    if field in record and record[field] is not None:
                        try:
                            actual_eps = float(record[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Find estimated EPS
                estimated_eps = None
                for field in estimate_fields:
                    if field in record and record[field] is not None:
                        try:
                            estimated_eps = float(record[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Find surprise percentage
                surprise_percent = None
                for field in surprise_fields:
                    if field in record and record[field] is not None:
                        try:
                            surprise_percent = float(record[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # Calculate missing values
                if actual_eps is not None and estimated_eps is not None:
                    if surprise_percent is None and estimated_eps != 0:
                        surprise_percent = round(((actual_eps - estimated_eps) / estimated_eps) * 100, 1)
                    
                    # Determine beat/miss/meet
                    if actual_eps > estimated_eps:
                        beat_miss_meet = 'BEAT'
                    elif actual_eps < estimated_eps:
                        beat_miss_meet = 'MISS'
                    else:
                        beat_miss_meet = 'MEET'
                    
                    # Extract quarter and year
                    quarter = (earnings_date.month - 1) // 3 + 1
                    year = earnings_date.year
                    
                    earnings_list.append({
                        'earnings_date': earnings_date.strftime('%Y-%m-%d'),
                        'quarter': quarter,
                        'year': year,
                        'actual_eps': actual_eps,
                        'estimated_eps': estimated_eps,
                        'beat_miss_meet': beat_miss_meet,
                        'surprise_percent': surprise_percent or 0.0
                    })
                    
                    print(f"✅ Parsed earnings: {symbol} {year} Q{quarter} - Actual: ${actual_eps}, Est: ${estimated_eps}")
            
            return earnings_list
            
        except Exception as e:
            print(f"❌ Error parsing API earnings data for {symbol}: {e}")
            return []

    def insert_api_earnings(self, symbol: str, earnings_data: List[Dict]) -> bool:
        """Insert API-sourced earnings data into database"""
        if not earnings_data:
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
            for earning in earnings_data:
                # Check if record already exists
                cursor.execute("""
                    SELECT id FROM earnings 
                    WHERE company_id = %s AND earnings_date = %s AND quarter = %s AND year = %s
                """, (company_id, earning['earnings_date'], earning['quarter'], earning['year']))
                
                if cursor.fetchone():
                    print(f"📝 API earnings record for {symbol} {earning['year']} Q{earning['quarter']} already exists, updating")
                    # Update existing record with real API data
                    cursor.execute("""
                        UPDATE earnings SET
                            actual_eps = %s, estimated_eps = %s, beat_miss_meet = %s, 
                            surprise_percent = %s, source_url = %s, updated_at = %s
                        WHERE company_id = %s AND earnings_date = %s AND quarter = %s AND year = %s
                    """, (
                        earning['actual_eps'], earning['estimated_eps'], earning['beat_miss_meet'],
                        earning['surprise_percent'], 
                        f"https://qcapi.nasdaq.com/api/quote/{symbol}/earnings",
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
                        f"https://qcapi.nasdaq.com/api/quote/{symbol}/earnings",
                        datetime.now(), datetime.now()
                    ))
                
                inserted_count += 1
                print(f"✅ Processed API earnings for {symbol} {earning['year']} Q{earning['quarter']}")
            
            self.conn.commit()
            cursor.close()
            print(f"✅ Successfully processed {inserted_count} API earnings records for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error inserting API earnings for {symbol}: {e}")
            self.conn.rollback()
            return False

    def scrape_company_earnings_api(self, symbol: str) -> bool:
        """Scrape earnings data for a single company via API"""
        try:
            print(f"\n🚀 Starting API earnings scraping for {symbol}")
            
            # Fetch API data
            api_data = self.fetch_earnings_data_api(symbol)
            if not api_data:
                print(f"⚠️ Could not fetch API data for {symbol}")
                return False
            
            # Parse earnings data
            earnings_data = self.parse_api_earnings_data(api_data, symbol)
            
            if not earnings_data:
                print(f"⚠️ No parseable earnings data found for {symbol}")
                return False
            
            # Insert into database
            success = self.insert_api_earnings(symbol, earnings_data)
            
            if success:
                print(f"✅ Successfully scraped {len(earnings_data)} API earnings for {symbol}")
                return True
            else:
                print(f"❌ Failed to insert API earnings for {symbol}")
                return False
                
        except Exception as e:
            print(f"❌ Error scraping API earnings for {symbol}: {e}")
            return False

    def scrape_all_companies_api(self):
        """Scrape earnings for all companies via API"""
        if not self.connect_to_database():
            return
        
        success_count = 0
        total_companies = len(self.companies)
        
        print(f"\n📈 Starting API earnings scraping for {total_companies} companies...")
        
        for i, symbol in enumerate(sorted(self.companies), 1):
            print(f"\n[{i}/{total_companies}] Processing {symbol}...")
            
            success = self.scrape_company_earnings_api(symbol)
            if success:
                success_count += 1
            
            # Respectful delay
            print(f"⏱️ Waiting 2 seconds before next request...")
            time.sleep(2)
        
        self.conn.close()
        
        print(f"\n📊 API earnings scraping complete!")
        print(f"✅ Successfully scraped: {success_count}/{total_companies} companies")
        print(f"❌ Failed: {total_companies - success_count} companies")

def main():
    """Main function"""
    print("🚀 NASDAQ API Earnings Scraper")
    print("=" * 50)
    
    scraper = NASDAQAPIEarningsScraper()
    
    # Option to scrape single company for testing
    import sys
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        if symbol in scraper.companies:
            if scraper.connect_to_database():
                scraper.scrape_company_earnings_api(symbol)
                scraper.conn.close()
        else:
            print(f"❌ Company {symbol} not found in earnings-icons directory")
    else:
        scraper.scrape_all_companies_api()

if __name__ == "__main__":
    main()