#!/usr/bin/env python3
"""
Generic Stock Data Curation Script
Replicates the AAPL data curation process for any stock symbol
"""

import json
import requests
import psycopg2
import logging
import argparse
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockDataCurator:
    def __init__(self, config_path: str = './config.json'):
        """Initialize the stock data curator with API configuration"""
        
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'calvin_earnings',
            'user': 'calvin_user',
            'password': 'calvin_pass'
        }
        
        # Initialize session for API calls
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Calvin Earnings Dashboard/1.0'
        })
        
        self.conn = None
        
    def load_config(self, config_path: str) -> dict:
        """Load API configuration from config file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info("✅ Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            # Fallback configuration
            return {
                "api_keys": {
                    "alpha_vantage": "demo",
                    "finnhub": "demo",
                    "financial_modeling_prep": "demo"
                },
                "api_endpoints": {
                    "alpha_vantage_base": "https://www.alphavantage.co/query",
                    "finnhub_base": "https://finnhub.io/api/v1",
                    "fmp_base": "https://financialmodelingprep.com/api/v3"
                }
            }
    
    def connect_to_database(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    def fetch_company_info(self, symbol: str) -> Optional[Dict]:
        """Fetch company information from Financial Modeling Prep"""
        try:
            url = f"{self.config['api_endpoints']['fmp_base']}/profile/{symbol}"
            params = {
                'apikey': self.config['api_keys']['financial_modeling_prep']
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                company_data = data[0]
                return {
                    'symbol': company_data.get('symbol'),
                    'company_name': company_data.get('companyName'),
                    'sector': company_data.get('sector'),
                    'industry': company_data.get('industry'),
                    'market_cap': company_data.get('mktCap'),
                    'website': company_data.get('website'),
                    'description': company_data.get('description'),
                    'exchange': company_data.get('exchangeShortName'),
                    'country': company_data.get('country'),
                    'source_url': f"https://finance.yahoo.com/quote/{symbol}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching company info for {symbol}: {e}")
            return None
    
    def fetch_historical_earnings(self, symbol: str) -> List[Dict]:
        """Fetch historical earnings data with API fallback logic"""
        
        # Try multiple APIs in order with fallback
        apis_to_try = [
            {
                'name': 'Financial Modeling Prep',
                'url': f"{self.config['api_endpoints']['fmp_base']}/historical/earning_calendar/{symbol}",
                'params': {'apikey': self.config['api_keys']['financial_modeling_prep']},
                'parser': self._parse_fmp_earnings
            },
            {
                'name': 'Alpha Vantage', 
                'url': f"{self.config['api_endpoints']['alpha_vantage_base']}",
                'params': {
                    'function': 'EARNINGS',
                    'symbol': symbol,
                    'apikey': self.config['api_keys']['alpha_vantage']
                },
                'parser': self._parse_alpha_vantage_earnings
            },
            {
                'name': 'Finnhub',
                'url': f"{self.config['api_endpoints']['finnhub_base']}/stock/earnings",
                'params': {
                    'symbol': symbol,
                    'token': self.config['api_keys']['finnhub']
                },
                'parser': self._parse_finnhub_earnings
            }
        ]
        
        for api in apis_to_try:
            try:
                logger.info(f"📊 Trying {api['name']} for {symbol} earnings...")
                
                response = self.session.get(api['url'], params=api['params'], timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API limit responses
                if self._is_rate_limited(data, api['name']):
                    logger.warning(f"⚠️ Rate limited on {api['name']}, trying next API...")
                    continue
                
                # Parse the data with API-specific parser
                earnings_data = api['parser'](data, symbol)
                
                if earnings_data:
                    logger.info(f"✅ Successfully fetched {len(earnings_data)} earnings from {api['name']}")
                    return earnings_data
                else:
                    logger.warning(f"⚠️ No earnings data from {api['name']}, trying next API...")
                    
            except Exception as e:
                logger.warning(f"⚠️ {api['name']} failed: {e}, trying next API...")
                continue
        
        logger.error(f"❌ All APIs failed for {symbol} earnings")
        return []
    
    def _parse_fmp_earnings(self, data: dict, symbol: str) -> List[Dict]:
        """Parse Financial Modeling Prep earnings data"""
        earnings_data = []
        
        for earning in data:
            # Parse earnings date
            earnings_date = datetime.strptime(earning.get('date'), '%Y-%m-%d').date()
            
            # Determine if this is past or future
            is_past = earnings_date <= date.today()
            
            earnings_entry = {
                'symbol': symbol,
                'earnings_date': earnings_date,
                'quarter': self.determine_quarter(earnings_date),
                'year': earnings_date.year,
                'estimated_eps': earning.get('epsEstimated'),
                'actual_eps': earning.get('eps') if is_past else None,
                'estimated_revenue': earning.get('revenueEstimated'),
                'actual_revenue': earning.get('revenue') if is_past else None,
                'announcement_time': earning.get('time', 'AMC'),
                'is_past': is_past,
                'source_url': f"https://finance.yahoo.com/quote/{symbol}/history"  # Safe URL for storage
            }
                
            # Calculate beat/miss/meet for past earnings
            if is_past and earnings_entry['actual_eps'] and earnings_entry['estimated_eps']:
                actual = float(earnings_entry['actual_eps'])
                estimated = float(earnings_entry['estimated_eps'])
                
                if actual > estimated:
                    earnings_entry['beat_miss_meet'] = 'BEAT'
                elif actual < estimated:
                    earnings_entry['beat_miss_meet'] = 'MISS'
                else:
                    earnings_entry['beat_miss_meet'] = 'MEET'
                
                # Calculate surprise percentage
                earnings_entry['surprise_percent'] = ((actual - estimated) / estimated) * 100
            
            earnings_data.append(earnings_entry)
        
        return earnings_data
    
    def _parse_alpha_vantage_earnings(self, data: dict, symbol: str) -> List[Dict]:
        """Parse Alpha Vantage earnings data"""
        earnings_data = []
        
        try:
            quarterly_earnings = data.get('quarterlyEarnings', [])
            
            for earning in quarterly_earnings[:8]:  # Last 8 quarters
                earnings_date = datetime.strptime(earning.get('fiscalDateEnding'), '%Y-%m-%d').date()
                is_past = earnings_date <= date.today()
                
                earnings_entry = {
                    'symbol': symbol,
                    'earnings_date': earnings_date,
                    'quarter': self.determine_quarter(earnings_date),
                    'year': earnings_date.year,
                    'estimated_eps': float(earning.get('estimatedEPS', 0)) if earning.get('estimatedEPS') else None,
                    'actual_eps': float(earning.get('reportedEPS', 0)) if earning.get('reportedEPS') else None,
                    'announcement_time': 'AMC',
                    'is_past': is_past,
                    'source_url': f"https://finance.yahoo.com/quote/{symbol}/history"
                }
                
                earnings_data.append(earnings_entry)
                
        except Exception as e:
            logger.error(f"❌ Error parsing Alpha Vantage data: {e}")
        
        return earnings_data
    
    def _parse_finnhub_earnings(self, data: dict, symbol: str) -> List[Dict]:
        """Parse Finnhub earnings data"""
        earnings_data = []
        
        try:
            earnings_list = data if isinstance(data, list) else []
            
            for earning in earnings_list[:8]:  # Last 8 quarters
                earnings_date = datetime.strptime(earning.get('period'), '%Y-%m-%d').date()
                is_past = earnings_date <= date.today()
                
                earnings_entry = {
                    'symbol': symbol,
                    'earnings_date': earnings_date,
                    'quarter': self.determine_quarter(earnings_date),
                    'year': earnings_date.year,
                    'estimated_eps': earning.get('epsEstimate'),
                    'actual_eps': earning.get('epsActual') if is_past else None,
                    'announcement_time': 'AMC',
                    'is_past': is_past,
                    'source_url': f"https://finance.yahoo.com/quote/{symbol}/history"
                }
                
                earnings_data.append(earnings_entry)
                
        except Exception as e:
            logger.error(f"❌ Error parsing Finnhub data: {e}")
        
        return earnings_data
    
    def _is_rate_limited(self, data: dict, api_name: str) -> bool:
        """Check if API response indicates rate limiting"""
        
        if api_name == 'Financial Modeling Prep':
            return 'Error Message' in data or 'error' in data
        elif api_name == 'Alpha Vantage':
            return 'Note' in data and 'call frequency' in str(data.get('Note', ''))
        elif api_name == 'Finnhub':
            return 'error' in data and 'limit' in str(data.get('error', '')).lower()
        
        return False
    
    def fetch_price_data_for_earnings(self, symbol: str, earnings_date: date) -> Optional[Dict]:
        """Fetch historical price data around earnings date with API fallback"""
        
        from_date = (earnings_date - timedelta(days=2)).strftime('%Y-%m-%d')
        to_date = (earnings_date + timedelta(days=5)).strftime('%Y-%m-%d')
        
        # Try FMP first, then Alpha Vantage
        apis_to_try = [
            {
                'name': 'Financial Modeling Prep',
                'url': f"{self.config['api_endpoints']['fmp_base']}/historical-price-full/{symbol}",
                'params': {
                    'from': from_date,
                    'to': to_date,
                    'apikey': self.config['api_keys']['financial_modeling_prep']
                }
            },
            {
                'name': 'Alpha Vantage',
                'url': f"{self.config['api_endpoints']['alpha_vantage_base']}",
                'params': {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'apikey': self.config['api_keys']['alpha_vantage']
                }
            }
        ]
        
        for api in apis_to_try:
            try:
                logger.info(f"📈 Trying {api['name']} for {symbol} price data...")
                
                response = self.session.get(api['url'], params=api['params'], timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if self._is_rate_limited(data, api['name']):
                    logger.warning(f"⚠️ Rate limited on {api['name']} for price data, trying next API...")
                    continue
                
                # Parse based on API
                if api['name'] == 'Financial Modeling Prep':
                    historical = data.get('historical', [])
                    if len(historical) >= 2:
                        earnings_price = None
                        next_day_price = None
                        
                        for price_data in historical:
                            price_date = datetime.strptime(price_data['date'], '%Y-%m-%d').date()
                            
                            if price_date == earnings_date:
                                earnings_price = price_data['close']
                            elif price_date == earnings_date + timedelta(days=1):
                                next_day_price = price_data['close']
                        
                        # If exact dates not found, use closest available
                        if not earnings_price and len(historical) > 0:
                            earnings_price = historical[-1]['close']
                        if not next_day_price and len(historical) > 1:
                            next_day_price = historical[0]['close']
                        
                        if earnings_price and next_day_price:
                            price_change = ((next_day_price - earnings_price) / earnings_price) * 100
                            
                            return {
                                'price_change_percent': price_change,
                                'earnings_price': earnings_price,
                                'next_day_price': next_day_price,
                                'volume': historical[-1].get('volume') if historical else None,
                                'source_url': f"https://finance.yahoo.com/quote/{symbol}/history"
                            }
                            
                elif api['name'] == 'Alpha Vantage':
                    time_series = data.get('Time Series (Daily)', {})
                    dates_list = sorted(time_series.keys(), reverse=True)
                    
                    earnings_price = None
                    next_day_price = None
                    
                    for date_str in dates_list:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if date_obj == earnings_date:
                            earnings_price = float(time_series[date_str]['4. close'])
                        elif date_obj == earnings_date + timedelta(days=1):
                            next_day_price = float(time_series[date_str]['4. close'])
                    
                    if earnings_price and next_day_price:
                        price_change = ((next_day_price - earnings_price) / earnings_price) * 100
                        
                        return {
                            'price_change_percent': price_change,
                            'earnings_price': earnings_price,
                            'next_day_price': next_day_price,
                            'volume': None,
                            'source_url': f"https://finance.yahoo.com/quote/{symbol}/history"
                        }
                
            except Exception as e:
                logger.warning(f"⚠️ {api['name']} failed for price data: {e}")
                continue
        
        logger.warning(f"⚠️ Could not fetch price data for {symbol} on {earnings_date}")
        return None
    
    def determine_quarter(self, earnings_date: date) -> int:
        """Determine fiscal quarter based on earnings date"""
        month = earnings_date.month
        
        # Most companies follow calendar year quarters
        if month in [1, 2, 3]:
            return 1
        elif month in [4, 5, 6]:
            return 2
        elif month in [7, 8, 9]:
            return 3
        else:
            return 4
    
    def insert_or_update_company(self, company_info: Dict) -> bool:
        """Insert or update company information in database"""
        try:
            cursor = self.conn.cursor()
            
            # Check if company exists
            cursor.execute("SELECT id FROM companies WHERE symbol = %s", (company_info['symbol'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing company
                update_query = """
                    UPDATE companies SET
                        company_name = %s,
                        gics_sector = %s,
                        gics_sub_industry = %s,
                        market_cap = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s
                """
                cursor.execute(update_query, (
                    company_info['company_name'],
                    company_info['sector'],
                    company_info['industry'],
                    company_info.get('market_cap'),
                    company_info['symbol']
                ))
                logger.info(f"✅ Updated company info for {company_info['symbol']}")
            else:
                # Insert new company
                insert_query = """
                    INSERT INTO companies (
                        symbol, company_name, gics_sector, gics_sub_industry,
                        market_cap, created_at
                    ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                cursor.execute(insert_query, (
                    company_info['symbol'],
                    company_info['company_name'],
                    company_info['sector'],
                    company_info['industry'],
                    company_info.get('market_cap')
                ))
                logger.info(f"✅ Added new company {company_info['symbol']}")
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inserting/updating company {company_info['symbol']}: {e}")
            return False
    
    def insert_earnings_data(self, earnings_list: List[Dict]) -> int:
        """Insert earnings data into database"""
        inserted_count = 0
        
        try:
            cursor = self.conn.cursor()
            
            for earning in earnings_list:
                # Check if this earning already exists
                cursor.execute("""
                    SELECT id FROM earnings 
                    WHERE symbol = %s AND earnings_date = %s AND quarter = %s AND year = %s
                """, (earning['symbol'], earning['earnings_date'], earning['quarter'], earning['year']))
                
                existing = cursor.fetchone()
                
                if not existing:
                    # Fetch price data for past earnings
                    price_data = None
                    if earning['is_past']:
                        price_data = self.fetch_price_data_for_earnings(
                            earning['symbol'], 
                            earning['earnings_date']
                        )
                        time.sleep(0.2)  # Rate limiting
                    
                    # Create Yahoo Finance URL (no API keys exposed)
                    source_url = f"https://finance.yahoo.com/quote/{symbol}/history"
                    
                    # Insert new earnings record
                    insert_query = """
                        INSERT INTO earnings (
                            company_id, symbol, earnings_date, quarter, year,
                            actual_eps, estimated_eps, actual_revenue, estimated_revenue,
                            beat_miss_meet, surprise_percent, announcement_time,
                            price_change_percent, volume, confidence_score,
                            source_url, data_verified_date, created_at
                        ) VALUES (
                            (SELECT id FROM companies WHERE symbol = %s LIMIT 1),
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            CURRENT_TIMESTAMP
                        )
                    """
                    
                    # Determine confidence score
                    confidence_score = 1.0 if earning['is_past'] else 0.75
                    
                    cursor.execute(insert_query, (
                        earning['symbol'],  # For company lookup
                        earning['symbol'],
                        earning['earnings_date'],
                        earning['quarter'],
                        earning['year'],
                        earning.get('actual_eps'),
                        earning.get('estimated_eps'),
                        earning.get('actual_revenue'),
                        earning.get('estimated_revenue'),
                        earning.get('beat_miss_meet'),
                        earning.get('surprise_percent'),
                        earning.get('announcement_time'),
                        price_data['price_change_percent'] if price_data else None,
                        price_data['volume'] if price_data else None,
                        confidence_score,
                        source_url,
                        date.today()
                    ))
                    
                    inserted_count += 1
                    
                    earnings_type = "past" if earning['is_past'] else "future"
                    logger.info(f"✅ Added {earnings_type} earnings for {earning['symbol']}: {earning['earnings_date']}")
                else:
                    logger.info(f"⏭️  Earnings already exists for {earning['symbol']} on {earning['earnings_date']}")
            
            cursor.close()
            return inserted_count
            
        except Exception as e:
            logger.error(f"❌ Error inserting earnings data: {e}")
            return 0
    
    def curate_stock_data(self, symbol: str) -> bool:
        """Main function to curate all data for a stock symbol"""
        try:
            logger.info(f"🚀 Starting data curation for {symbol}")
            
            # Connect to database
            if not self.connect_to_database():
                return False
            
            # Step 1: Fetch company information
            logger.info(f"📊 Fetching company information for {symbol}...")
            company_info = self.fetch_company_info(symbol)
            if not company_info:
                logger.error(f"❌ Could not fetch company info for {symbol}")
                return False
            
            # Step 2: Insert/update company information
            if not self.insert_or_update_company(company_info):
                logger.error(f"❌ Failed to update company info for {symbol}")
                return False
            
            # Step 3: Fetch historical and future earnings
            logger.info(f"📈 Fetching earnings data for {symbol}...")
            earnings_data = self.fetch_historical_earnings(symbol)
            if not earnings_data:
                logger.warning(f"⚠️  No earnings data found for {symbol}")
                return False
            
            # Step 4: Insert earnings data
            logger.info(f"💾 Inserting earnings data for {symbol}...")
            inserted_count = self.insert_earnings_data(earnings_data)
            
            # Summary
            past_earnings = len([e for e in earnings_data if e['is_past']])
            future_earnings = len([e for e in earnings_data if not e['is_past']])
            
            logger.info(f"🎉 Successfully curated data for {symbol}:")
            logger.info(f"   - Company: {company_info['company_name']}")
            logger.info(f"   - Sector: {company_info['sector']}")
            logger.info(f"   - Market Cap: ${company_info.get('market_cap', 0):,}")
            logger.info(f"   - Past Earnings: {past_earnings}")
            logger.info(f"   - Future Earnings: {future_earnings}")
            logger.info(f"   - New Records: {inserted_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error curating data for {symbol}: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Curate stock data for any symbol')
    parser.add_argument('symbol', help='Stock symbol to curate (e.g., MSFT)')
    parser.add_argument('--config', default='./config.json', 
                       help='Path to configuration file (default: ./config.json)')
    
    args = parser.parse_args()
    
    # Validate symbol format
    symbol = args.symbol.upper().strip()
    if not symbol or len(symbol) > 10:
        logger.error("❌ Invalid symbol format")
        return False
    
    # Initialize curator and run
    curator = StockDataCurator(args.config)
    success = curator.curate_stock_data(symbol)
    
    if success:
        logger.info(f"✅ Data curation completed successfully for {symbol}")
        return True
    else:
        logger.error(f"❌ Data curation failed for {symbol}")
        return False


if __name__ == "__main__":
    main()