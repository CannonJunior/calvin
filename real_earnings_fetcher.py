#!/usr/bin/env python3
"""
Real Earnings Data Fetcher Service
Fetches the most recent actual earnings reports for all S&P 500 companies
"""

import json
import logging
import time
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealEarningsFetcher:
    def __init__(self):
        """Initialize the real earnings fetcher service"""
        
        # API configurations
        self.apis = {
            'finnhub': {
                'base_url': 'https://finnhub.io/api/v1',
                'token': 'demo',  # Use demo token for testing
                'rate_limit': 60  # calls per minute
            },
            'alpha_vantage': {
                'base_url': 'https://www.alphavantage.co/query',
                'api_key': 'demo',
                'rate_limit': 5  # calls per minute for free tier
            }
        }
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'calvin_earnings',
            'user': 'calvin_user',
            'password': 'calvin_pass'
        }
        
        self.conn = None
        self.sp500_companies = []
        self.fetched_earnings = []
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    def load_sp500_companies(self):
        """Load S&P 500 companies from database"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM companies ORDER BY symbol")
            companies = [dict(row) for row in cursor.fetchall()]
            self.sp500_companies = companies
            cursor.close()
            logger.info(f"📊 Loaded {len(self.sp500_companies)} S&P 500 companies from database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load companies: {e}")
            return False
    
    def fetch_finnhub_earnings(self, symbol: str) -> Optional[Dict]:
        """Fetch earnings data from Finnhub API"""
        try:
            # Get basic earnings info
            earnings_url = f"{self.apis['finnhub']['base_url']}/stock/earnings"
            params = {
                'symbol': symbol,
                'token': self.apis['finnhub']['token']
            }
            
            response = requests.get(earnings_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Get the most recent earnings
                    latest = data[0]
                    
                    # Also try to get earnings calendar for more detailed info
                    from_date = (date.today() - timedelta(days=90)).isoformat()
                    to_date = date.today().isoformat()
                    
                    calendar_url = f"{self.apis['finnhub']['base_url']}/calendar/earnings"
                    calendar_params = {
                        'from': from_date,
                        'to': to_date,
                        'symbol': symbol,
                        'token': self.apis['finnhub']['token']
                    }
                    
                    calendar_response = requests.get(calendar_url, params=calendar_params, timeout=10)
                    calendar_data = None
                    if calendar_response.status_code == 200:
                        calendar_json = calendar_response.json()
                        if 'earningsCalendar' in calendar_json and calendar_json['earningsCalendar']:
                            calendar_data = calendar_json['earningsCalendar'][0]
                    
                    return {
                        'symbol': symbol,
                        'earnings_date': latest.get('period'),
                        'actual_eps': latest.get('actual'),
                        'estimated_eps': latest.get('estimate'),
                        'quarter': self.extract_quarter_from_period(latest.get('period')),
                        'year': self.extract_year_from_period(latest.get('period')),
                        'surprise': latest.get('surprise'),
                        'calendar_data': calendar_data,
                        'source': 'finnhub'
                    }
            
            time.sleep(1)  # Rate limiting
            return None
            
        except Exception as e:
            logger.warning(f"Failed to fetch Finnhub data for {symbol}: {e}")
            return None
    
    def fetch_alpha_vantage_earnings(self, symbol: str) -> Optional[Dict]:
        """Fetch earnings data from Alpha Vantage API"""
        try:
            url = self.apis['alpha_vantage']['base_url']
            params = {
                'function': 'EARNINGS',
                'symbol': symbol,
                'apikey': self.apis['alpha_vantage']['api_key']
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'quarterlyEarnings' in data and data['quarterlyEarnings']:
                    latest = data['quarterlyEarnings'][0]  # Most recent quarter
                    
                    return {
                        'symbol': symbol,
                        'earnings_date': latest.get('reportedDate'),
                        'actual_eps': float(latest.get('reportedEPS', 0)) if latest.get('reportedEPS') != 'None' else None,
                        'estimated_eps': float(latest.get('estimatedEPS', 0)) if latest.get('estimatedEPS') != 'None' else None,
                        'quarter': self.extract_quarter_from_fiscal(latest.get('fiscalDateEnding')),
                        'year': self.extract_year_from_fiscal(latest.get('fiscalDateEnding')),
                        'surprise': float(latest.get('surprise', 0)) if latest.get('surprise') != 'None' else None,
                        'surprise_percent': float(latest.get('surprisePercentage', 0)) if latest.get('surprisePercentage') != 'None' else None,
                        'source': 'alpha_vantage'
                    }
            
            time.sleep(12)  # Alpha Vantage rate limiting (5 calls per minute)
            return None
            
        except Exception as e:
            logger.warning(f"Failed to fetch Alpha Vantage data for {symbol}: {e}")
            return None
    
    def extract_quarter_from_period(self, period: str) -> Optional[int]:
        """Extract quarter from period string like '2024-12-31'"""
        if not period:
            return None
        try:
            date_obj = datetime.strptime(period, '%Y-%m-%d').date()
            return ((date_obj.month - 1) // 3) + 1
        except:
            return None
    
    def extract_year_from_period(self, period: str) -> Optional[int]:
        """Extract year from period string"""
        if not period:
            return None
        try:
            return datetime.strptime(period, '%Y-%m-%d').year
        except:
            return None
    
    def extract_quarter_from_fiscal(self, fiscal_date: str) -> Optional[int]:
        """Extract quarter from fiscal date ending"""
        if not fiscal_date:
            return None
        try:
            date_obj = datetime.strptime(fiscal_date, '%Y-%m-%d').date()
            return ((date_obj.month - 1) // 3) + 1
        except:
            return None
    
    def extract_year_from_fiscal(self, fiscal_date: str) -> Optional[int]:
        """Extract year from fiscal date"""
        if not fiscal_date:
            return None
        try:
            return datetime.strptime(fiscal_date, '%Y-%m-%d').year
        except:
            return None
    
    def calculate_beat_miss_meet(self, actual_eps: float, estimated_eps: float) -> str:
        """Calculate if earnings beat, missed, or met expectations"""
        if actual_eps is None or estimated_eps is None:
            return 'UNKNOWN'
        
        diff_percent = ((actual_eps - estimated_eps) / abs(estimated_eps)) * 100 if estimated_eps != 0 else 0
        
        if diff_percent > 2:
            return 'BEAT'
        elif diff_percent < -2:
            return 'MISS'
        else:
            return 'MEET'
    
    def fetch_earnings_for_company(self, company: Dict) -> Optional[Dict]:
        """Fetch earnings data for a single company using multiple APIs"""
        symbol = company['symbol']
        logger.info(f"📊 Fetching earnings for {symbol}...")
        
        # Try Finnhub first (more reliable for recent data)
        earnings_data = self.fetch_finnhub_earnings(symbol)
        
        # If Finnhub fails, try Alpha Vantage
        if not earnings_data:
            earnings_data = self.fetch_alpha_vantage_earnings(symbol)
        
        if earnings_data:
            # Calculate additional metrics
            if earnings_data.get('actual_eps') and earnings_data.get('estimated_eps'):
                actual = earnings_data['actual_eps']
                estimated = earnings_data['estimated_eps']
                
                earnings_data['beat_miss_meet'] = self.calculate_beat_miss_meet(actual, estimated)
                
                if not earnings_data.get('surprise_percent'):
                    earnings_data['surprise_percent'] = ((actual - estimated) / abs(estimated)) * 100 if estimated != 0 else 0
            
            # Add company info
            earnings_data['company_id'] = company['id']
            earnings_data['company_name'] = company['company_name']
            earnings_data['gics_sector'] = company['gics_sector']
            
            logger.info(f"✅ Found earnings for {symbol}: EPS {earnings_data.get('actual_eps')} vs {earnings_data.get('estimated_eps')}")
            return earnings_data
        
        logger.warning(f"⚠️ No earnings data found for {symbol}")
        return None
    
    def save_earnings_to_database(self, earnings_data: Dict) -> bool:
        """Save earnings data to PostgreSQL database"""
        if not self.conn or not earnings_data:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Convert earnings_date string to date object if needed
            earnings_date = earnings_data.get('earnings_date')
            if isinstance(earnings_date, str):
                try:
                    earnings_date = datetime.strptime(earnings_date, '%Y-%m-%d').date()
                except:
                    earnings_date = date.today()
            elif not earnings_date:
                earnings_date = date.today()
            
            # Insert or update earnings data
            query = """
                INSERT INTO earnings (
                    company_id, symbol, earnings_date, quarter, year,
                    actual_eps, estimated_eps, beat_miss_meet, surprise_percent,
                    consensus_rating, confidence_score, announcement_time,
                    num_analysts, price_change_percent, volume
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, earnings_date, quarter, year)
                DO UPDATE SET
                    actual_eps = EXCLUDED.actual_eps,
                    estimated_eps = EXCLUDED.estimated_eps,
                    beat_miss_meet = EXCLUDED.beat_miss_meet,
                    surprise_percent = EXCLUDED.surprise_percent,
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(query, (
                earnings_data.get('company_id'),
                earnings_data.get('symbol'),
                earnings_date,
                earnings_data.get('quarter'),
                earnings_data.get('year'),
                earnings_data.get('actual_eps'),
                earnings_data.get('estimated_eps'),
                earnings_data.get('beat_miss_meet', 'UNKNOWN'),
                earnings_data.get('surprise_percent'),
                'Hold',  # Default consensus rating
                0.9,  # High confidence for real data
                'AMC',  # Default announcement time
                10,  # Default analyst count
                0.0,  # Price change to be updated later
                50000000  # Default volume
            ))
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save earnings data for {earnings_data.get('symbol')}: {e}")
            return False
    
    def fetch_all_sp500_earnings(self, limit: Optional[int] = None):
        """Fetch earnings data for all S&P 500 companies"""
        if not self.sp500_companies:
            logger.error("No S&P 500 companies loaded")
            return False
        
        companies_to_process = self.sp500_companies[:limit] if limit else self.sp500_companies
        total_companies = len(companies_to_process)
        
        logger.info(f"🚀 Starting real earnings data fetch for {total_companies} companies...")
        
        success_count = 0
        error_count = 0
        
        for i, company in enumerate(companies_to_process):
            try:
                logger.info(f"Processing {company['symbol']} ({i+1}/{total_companies})")
                
                # Fetch earnings data
                earnings_data = self.fetch_earnings_for_company(company)
                
                if earnings_data:
                    # Save to database
                    if self.save_earnings_to_database(earnings_data):
                        success_count += 1
                        self.fetched_earnings.append(earnings_data)
                        logger.info(f"✅ Saved earnings for {company['symbol']}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to save earnings for {company['symbol']}")
                else:
                    error_count += 1
                    logger.warning(f"⚠️ No earnings data for {company['symbol']}")
                
                # Rate limiting to avoid API throttling
                if i % 10 == 0 and i > 0:
                    logger.info(f"⏳ Progress: {i}/{total_companies} - Taking a short break...")
                    time.sleep(2)
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {company.get('symbol', 'unknown')}: {e}")
        
        logger.info(f"🎉 Earnings fetch complete: {success_count} success, {error_count} errors")
        return success_count > 0
    
    def run_fetcher(self, limit: Optional[int] = None):
        """Run the complete earnings fetcher process"""
        logger.info("🚀 Starting real earnings data fetcher service...")
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
        # Load S&P 500 companies
        if not self.load_sp500_companies():
            return False
        
        # Fetch real earnings data
        success = self.fetch_all_sp500_earnings(limit=limit)
        
        if success:
            # Show summary
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM earnings WHERE actual_eps IS NOT NULL")
            real_earnings_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM earnings WHERE earnings_date >= CURRENT_DATE - INTERVAL '90 days'")
            recent_earnings_count = cursor.fetchone()[0]
            
            cursor.close()
            
            logger.info("✅ Real earnings data fetch completed")
            logger.info(f"📊 Database Summary:")
            logger.info(f"   Real Earnings Records: {real_earnings_count}")
            logger.info(f"   Recent Earnings (90 days): {recent_earnings_count}")
            logger.info(f"   Fetched This Session: {len(self.fetched_earnings)}")
        
        if self.conn:
            self.conn.close()
        
        return success


def main():
    """Main function"""
    fetcher = RealEarningsFetcher()
    
    # Start with a smaller batch for testing
    fetcher.run_fetcher(limit=50)  # Test with 50 companies first


if __name__ == "__main__":
    main()