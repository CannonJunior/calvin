#!/usr/bin/env python3
"""
Simple Earnings Data Ingestion Service
Populates PostgreSQL database with realistic earnings data
"""

import json
import logging
import random
from datetime import datetime, date, timedelta
from typing import List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleEarningsIngestion:
    def __init__(self):
        """Initialize the simple earnings ingestion service"""
        
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
        """Load S&P 500 companies from JSON file"""
        try:
            with open('sp500_companies.json', 'r', encoding='utf-8') as f:
                self.sp500_companies = json.load(f)
            logger.info(f"📊 Loaded {len(self.sp500_companies)} S&P 500 companies")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load S&P 500 companies: {e}")
            return False
    
    def populate_companies_table(self):
        """Populate companies table with S&P 500 data"""
        if not self.sp500_companies or not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            for company in self.sp500_companies:
                # Parse date_added
                date_added = None
                if company.get('date_added'):
                    try:
                        date_added = datetime.strptime(company['date_added'], '%Y-%m-%d').date()
                    except:
                        try:
                            date_added = datetime.strptime(company['date_added'], '%B %d, %Y').date()
                        except:
                            pass
                
                # Insert or update company
                query = """
                    INSERT INTO companies (symbol, company_name, gics_sector, gics_sub_industry, 
                                         headquarters, date_added, cik, founded)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol) 
                    DO UPDATE SET 
                        company_name = EXCLUDED.company_name,
                        gics_sector = EXCLUDED.gics_sector,
                        gics_sub_industry = EXCLUDED.gics_sub_industry,
                        headquarters = EXCLUDED.headquarters,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                cursor.execute(query, (
                    company.get('symbol', ''),
                    company.get('company_name', ''),
                    company.get('gics_sector', ''),
                    company.get('gics_sub_industry', ''),
                    company.get('headquarters', ''),
                    date_added,
                    company.get('cik', ''),
                    company.get('founded', '')
                ))
            
            cursor.close()
            logger.info(f"✅ Populated companies table with {len(self.sp500_companies)} companies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to populate companies table: {e}")
            return False
    
    def get_sector_base_eps(self, sector: str) -> float:
        """Get base EPS estimate for sector"""
        sector_eps_map = {
            'Information Technology': 2.5,
            'Health Care': 2.0,
            'Financials': 3.0,
            'Consumer Discretionary': 1.8,
            'Communication Services': 1.5,
            'Industrials': 2.2,
            'Consumer Staples': 1.6,
            'Energy': 2.8,
            'Utilities': 1.4,
            'Real Estate': 1.2,
            'Materials': 2.0
        }
        return sector_eps_map.get(sector, 2.0)
    
    def generate_realistic_earnings(self, symbol: str, company_data: Dict) -> List[Dict]:
        """Generate realistic earnings data for a company"""
        earnings_list = []
        current_date = date.today()
        sector = company_data.get('gics_sector', 'Information Technology')
        base_eps = self.get_sector_base_eps(sector)
        
        # Generate past earnings (last 8 quarters with recent dates)
        for q in range(8, 0, -1):
            earnings_date = current_date - timedelta(days=q * 30 + random.randint(-10, 10))
            quarter = ((earnings_date.month - 1) // 3) + 1
            
            # Generate realistic historical data
            estimated_eps = base_eps * (1 + random.uniform(-0.2, 0.2))
            actual_eps = estimated_eps * (1 + random.uniform(-0.15, 0.25))  # Slight tendency to beat
            
            # Calculate metrics
            surprise_percent = ((actual_eps - estimated_eps) / estimated_eps) * 100
            beat_miss_meet = 'BEAT' if surprise_percent > 2 else ('MISS' if surprise_percent < -2 else 'MEET')
            
            # Price change correlation with surprise
            price_change = surprise_percent * random.uniform(0.3, 0.8) + random.uniform(-2, 2)
            
            earnings_list.append({
                'symbol': symbol,
                'earnings_date': earnings_date,
                'quarter': quarter,
                'year': earnings_date.year,
                'estimated_eps': round(estimated_eps, 2),
                'actual_eps': round(actual_eps, 2),
                'surprise_percent': round(surprise_percent, 2),
                'beat_miss_meet': beat_miss_meet,
                'price_change_percent': round(price_change, 2),
                'volume': random.randint(10000000, 100000000),
                'confidence_score': 0.9,  # High confidence for historical data
                'consensus_rating': random.choice(['Buy', 'Hold', 'Sell']),
                'num_analysts': random.randint(8, 25),
                'announcement_time': random.choice(['BMO', 'AMC'])
            })
        
        # Generate future earnings (next 4 quarters with closer dates)
        for q in range(1, 5):
            earnings_date = current_date + timedelta(days=q * 45 + random.randint(-10, 15))
            quarter = ((earnings_date.month - 1) // 3) + 1
            
            # Future estimates with some variance
            estimated_eps = base_eps * (1 + random.uniform(-0.1, 0.3))  # Growth expectation
            
            # Assign consensus rating based on sector trends
            consensus_weights = [0.5, 0.4, 0.1] if 'Technology' in sector else [0.3, 0.5, 0.2]
            consensus_rating = random.choices(['Buy', 'Hold', 'Sell'], weights=consensus_weights)[0]
            
            earnings_list.append({
                'symbol': symbol,
                'earnings_date': earnings_date,
                'quarter': quarter,
                'year': earnings_date.year,
                'estimated_eps': round(estimated_eps, 2),
                'consensus_rating': consensus_rating,
                'num_analysts': random.randint(8, 25),
                'confidence_score': round(random.uniform(0.6, 0.9), 2),
                'announcement_time': random.choice(['BMO', 'AMC'])
            })
        
        return earnings_list
    
    def insert_earnings_data(self, earnings_list: List[Dict]) -> bool:
        """Insert earnings data into database"""
        if not earnings_list or not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            for earnings in earnings_list:
                # Get company_id
                cursor.execute("SELECT id FROM companies WHERE symbol = %s", (earnings['symbol'],))
                company_row = cursor.fetchone()
                
                if not company_row:
                    logger.warning(f"Company not found: {earnings['symbol']}")
                    continue
                
                company_id = company_row[0]
                
                # Insert earnings data
                query = """
                    INSERT INTO earnings (
                        company_id, symbol, earnings_date, quarter, year,
                        actual_eps, estimated_eps, consensus_rating, num_analysts,
                        beat_miss_meet, surprise_percent, confidence_score,
                        announcement_time, price_change_percent, volume
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (symbol, earnings_date, quarter, year)
                    DO UPDATE SET
                        actual_eps = EXCLUDED.actual_eps,
                        estimated_eps = EXCLUDED.estimated_eps,
                        consensus_rating = EXCLUDED.consensus_rating,
                        beat_miss_meet = EXCLUDED.beat_miss_meet,
                        surprise_percent = EXCLUDED.surprise_percent,
                        confidence_score = EXCLUDED.confidence_score,
                        price_change_percent = EXCLUDED.price_change_percent,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                cursor.execute(query, (
                    company_id,
                    earnings['symbol'],
                    earnings['earnings_date'],
                    earnings['quarter'],
                    earnings['year'],
                    earnings.get('actual_eps'),
                    earnings.get('estimated_eps'),
                    earnings.get('consensus_rating'),
                    earnings.get('num_analysts'),
                    earnings.get('beat_miss_meet'),
                    earnings.get('surprise_percent'),
                    earnings.get('confidence_score', 0.5),
                    earnings.get('announcement_time'),
                    earnings.get('price_change_percent'),
                    earnings.get('volume')
                ))
            
            cursor.close()
            logger.info(f"✅ Inserted {len(earnings_list)} earnings records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to insert earnings data: {e}")
            return False
    
    def ingest_earnings_for_companies(self, limit: int = 50):
        """Ingest earnings data for specified number of companies"""
        if not self.sp500_companies:
            logger.error("No S&P 500 companies loaded")
            return False
        
        logger.info(f"🚀 Starting earnings data ingestion for {min(limit, len(self.sp500_companies))} companies...")
        
        success_count = 0
        error_count = 0
        
        for i, company in enumerate(self.sp500_companies[:limit]):
            symbol = company.get('symbol')
            if not symbol:
                continue
            
            logger.info(f"📊 Processing {symbol} ({i+1}/{min(limit, len(self.sp500_companies))})")
            
            try:
                # Generate earnings data
                earnings_data = self.generate_realistic_earnings(symbol, company)
                
                if earnings_data:
                    if self.insert_earnings_data(earnings_data):
                        success_count += 1
                        logger.info(f"✅ {symbol}: Generated {len(earnings_data)} earnings records")
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.warning(f"⚠️ No earnings data generated for {symbol}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {symbol}: {e}")
        
        logger.info(f"🎉 Ingestion complete: {success_count} success, {error_count} errors")
        return success_count > 0
    
    def run_ingestion(self, limit: int = 50):
        """Run the complete ingestion process"""
        logger.info("🚀 Starting simple earnings data ingestion service...")
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
        # Load S&P 500 companies
        if not self.load_sp500_companies():
            return False
        
        # Populate companies table
        if not self.populate_companies_table():
            return False
        
        # Ingest earnings data
        self.ingest_earnings_for_companies(limit=limit)
        
        # Show summary
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        companies_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM earnings")
        earnings_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM earnings WHERE earnings_date < CURRENT_DATE")
        past_earnings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM earnings WHERE earnings_date >= CURRENT_DATE")
        future_earnings = cursor.fetchone()[0]
        
        cursor.close()
        self.conn.close()
        
        logger.info("✅ Earnings data ingestion completed")
        logger.info(f"📊 Database Summary:")
        logger.info(f"   Companies: {companies_count}")
        logger.info(f"   Total Earnings: {earnings_count}")
        logger.info(f"   Past Earnings: {past_earnings}")
        logger.info(f"   Future Earnings: {future_earnings}")
        
        return True


def main():
    """Main function"""
    ingestion_service = SimpleEarningsIngestion()
    ingestion_service.run_ingestion(limit=50)  # Process 50 companies for demo


if __name__ == "__main__":
    main()