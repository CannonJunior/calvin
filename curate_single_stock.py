#!/usr/bin/env python3
"""
Single Stock Earnings Curation
Modified from earnings_ingestion.py to process one symbol at a time
"""

import os
import json
import logging
import asyncio
import sys
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SingleStockCurator:
    def __init__(self):
        """Initialize the single stock curation service"""
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'calvin_earnings',
            'user': 'calvin_user',
            'password': 'calvin_pass'
        }
        
        # API configuration
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
        self.finnhub_key = os.getenv('FINNHUB_KEY', 'demo')
        
        # Initialize sentence transformer for embeddings
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Loaded sentence transformer model")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.embedding_model = None
        
        self.engine = None
        self.sp500_companies = []
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            db_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.engine = create_engine(db_url)
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
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
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get company info for a specific symbol"""
        for company in self.sp500_companies:
            if company.get('symbol') == symbol:
                return company
        return None
    
    def generate_earnings_embedding(self, earnings_data: Dict) -> Optional[List[float]]:
        """Generate vector embedding for earnings data"""
        if not self.embedding_model:
            return None
        
        try:
            text_repr = f"""
            Company: {earnings_data.get('symbol', '')}
            Sector: {earnings_data.get('sector', '')}
            Quarter: Q{earnings_data.get('quarter', '')} {earnings_data.get('year', '')}
            Estimated EPS: {earnings_data.get('estimated_eps', 'N/A')}
            Actual EPS: {earnings_data.get('actual_eps', 'N/A')}
            Beat/Miss: {earnings_data.get('beat_miss_meet', 'N/A')}
            Consensus: {earnings_data.get('consensus_rating', 'N/A')}
            """.strip()
            
            embedding = self.embedding_model.encode(text_repr)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def fetch_earnings_data_alpha_vantage(self, symbol: str) -> List[Dict]:
        """Fetch earnings data from Alpha Vantage"""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'EARNINGS',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} for {symbol}")
                return []
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"API Error for {symbol}: {data['Error Message']}")
                return []
            
            if 'Note' in data:
                logger.warning(f"API limit reached for {symbol}: {data['Note']}")
                return []
            
            earnings_list = []
            quarterly_earnings = data.get('quarterlyEarnings', [])
            
            for earnings in quarterly_earnings[:8]:  # Last 8 quarters
                fiscal_date = earnings.get('fiscalDateEnding')
                if not fiscal_date:
                    continue
                
                try:
                    earnings_date = datetime.strptime(fiscal_date, '%Y-%m-%d').date()
                    quarter = ((earnings_date.month - 1) // 3) + 1
                    
                    estimated_eps = self._safe_float(earnings.get('estimatedEPS'))
                    actual_eps = self._safe_float(earnings.get('reportedEPS'))
                    
                    surprise_percent = None
                    beat_miss_meet = 'MEET'
                    if estimated_eps and actual_eps:
                        surprise_percent = ((actual_eps - estimated_eps) / estimated_eps) * 100
                        if surprise_percent > 2:
                            beat_miss_meet = 'BEAT'
                        elif surprise_percent < -2:
                            beat_miss_meet = 'MISS'
                    
                    earnings_data = {
                        'symbol': symbol,
                        'earnings_date': earnings_date,
                        'quarter': quarter,
                        'year': earnings_date.year,
                        'estimated_eps': estimated_eps,
                        'actual_eps': actual_eps,
                        'surprise_percent': surprise_percent,
                        'beat_miss_meet': beat_miss_meet,
                        'confidence_score': 0.8
                    }
                    
                    earnings_list.append(earnings_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing earnings data for {symbol}: {e}")
                    continue
            
            return earnings_list
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return []
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == 'None' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def generate_mock_future_earnings(self, symbol: str, company_data: Dict) -> List[Dict]:
        """Generate realistic mock future earnings data"""
        earnings_list = []
        current_date = date.today()
        
        for q in range(1, 5):
            earnings_date = current_date + timedelta(days=q * 90 + np.random.randint(-15, 15))
            quarter = ((earnings_date.month - 1) // 3) + 1
            
            sector = company_data.get('gics_sector', '')
            base_eps = self._get_sector_base_eps(sector)
            estimated_eps = base_eps * (1 + np.random.normal(0, 0.1))
            
            consensus_ratings = ['Buy', 'Hold', 'Sell']
            weights = [0.5, 0.4, 0.1] if 'Technology' in sector else [0.3, 0.5, 0.2]
            consensus_rating = np.random.choice(consensus_ratings, p=weights)
            
            earnings_data = {
                'symbol': symbol,
                'earnings_date': earnings_date,
                'quarter': quarter,
                'year': earnings_date.year,
                'estimated_eps': round(estimated_eps, 2),
                'consensus_rating': consensus_rating,
                'num_analysts': np.random.randint(8, 25),
                'confidence_score': np.random.uniform(0.6, 0.9),
                'announcement_time': np.random.choice(['BMO', 'AMC'])
            }
            
            earnings_list.append(earnings_data)
        
        return earnings_list
    
    def _get_sector_base_eps(self, sector: str) -> float:
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
    
    def insert_earnings_data(self, earnings_list: List[Dict]) -> bool:
        """Insert earnings data into database"""
        if not earnings_list or not self.engine:
            return False
        
        try:
            with self.engine.connect() as conn:
                for earnings in earnings_list:
                    company_query = text("SELECT id FROM companies WHERE symbol = :symbol")
                    result = conn.execute(company_query, {'symbol': earnings['symbol']})
                    company_row = result.fetchone()
                    
                    if not company_row:
                        logger.warning(f"Company not found: {earnings['symbol']}")
                        continue
                    
                    company_id = company_row[0]
                    embedding = self.generate_earnings_embedding(earnings)
                    
                    query = text("""
                        INSERT INTO earnings (
                            company_id, symbol, earnings_date, quarter, year,
                            actual_eps, estimated_eps, consensus_rating, num_analysts,
                            beat_miss_meet, surprise_percent, confidence_score,
                            announcement_time, earnings_embedding
                        ) VALUES (
                            :company_id, :symbol, :earnings_date, :quarter, :year,
                            :actual_eps, :estimated_eps, :consensus_rating, :num_analysts,
                            :beat_miss_meet, :surprise_percent, :confidence_score,
                            :announcement_time, :earnings_embedding
                        )
                        ON CONFLICT (symbol, earnings_date, quarter, year)
                        DO UPDATE SET
                            actual_eps = EXCLUDED.actual_eps,
                            estimated_eps = EXCLUDED.estimated_eps,
                            consensus_rating = EXCLUDED.consensus_rating,
                            beat_miss_meet = EXCLUDED.beat_miss_meet,
                            surprise_percent = EXCLUDED.surprise_percent,
                            confidence_score = EXCLUDED.confidence_score,
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    conn.execute(query, {
                        'company_id': company_id,
                        'symbol': earnings['symbol'],
                        'earnings_date': earnings['earnings_date'],
                        'quarter': earnings['quarter'],
                        'year': earnings['year'],
                        'actual_eps': earnings.get('actual_eps'),
                        'estimated_eps': earnings.get('estimated_eps'),
                        'consensus_rating': earnings.get('consensus_rating'),
                        'num_analysts': earnings.get('num_analysts'),
                        'beat_miss_meet': earnings.get('beat_miss_meet'),
                        'surprise_percent': earnings.get('surprise_percent'),
                        'confidence_score': earnings.get('confidence_score', 0.5),
                        'announcement_time': earnings.get('announcement_time'),
                        'earnings_embedding': embedding
                    })
                
                conn.commit()
                logger.info(f"✅ Inserted {len(earnings_list)} earnings records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to insert earnings data: {e}")
            return False
    
    def ensure_company_exists(self, symbol: str) -> bool:
        """Ensure company exists in companies table"""
        try:
            company_info = self.get_company_info(symbol)
            if not company_info:
                logger.error(f"Company {symbol} not found in S&P 500 list")
                return False
            
            with self.engine.connect() as conn:
                date_added = None
                if company_info.get('date_added'):
                    try:
                        date_added = datetime.strptime(company_info['date_added'], '%Y-%m-%d').date()
                    except:
                        try:
                            date_added = datetime.strptime(company_info['date_added'], '%B %d, %Y').date()
                        except:
                            pass
                
                query = text("""
                    INSERT INTO companies (symbol, company_name, gics_sector, gics_sub_industry, 
                                         headquarters, date_added, cik, founded)
                    VALUES (:symbol, :company_name, :gics_sector, :gics_sub_industry, 
                            :headquarters, :date_added, :cik, :founded)
                    ON CONFLICT (symbol) 
                    DO UPDATE SET 
                        company_name = EXCLUDED.company_name,
                        gics_sector = EXCLUDED.gics_sector,
                        gics_sub_industry = EXCLUDED.gics_sub_industry,
                        headquarters = EXCLUDED.headquarters,
                        updated_at = CURRENT_TIMESTAMP
                """)
                
                conn.execute(query, {
                    'symbol': company_info.get('symbol', ''),
                    'company_name': company_info.get('company_name', ''),
                    'gics_sector': company_info.get('gics_sector', ''),
                    'gics_sub_industry': company_info.get('gics_sub_industry', ''),
                    'headquarters': company_info.get('headquarters', ''),
                    'date_added': date_added,
                    'cik': company_info.get('cik', ''),
                    'founded': company_info.get('founded', '')
                })
                
                conn.commit()
                logger.info(f"✅ Company {symbol} ready in database")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure company exists: {e}")
            return False
    
    async def curate_stock(self, symbol: str):
        """Curate earnings data for a single stock"""
        logger.info(f"🚀 Starting curation for {symbol}")
        
        if not self.connect_to_database():
            return False
        
        if not self.load_sp500_companies():
            return False
        
        if not self.ensure_company_exists(symbol):
            return False
        
        company_info = self.get_company_info(symbol)
        
        try:
            # Fetch real earnings data
            real_earnings = self.fetch_earnings_data_alpha_vantage(symbol)
            
            # Generate future earnings data
            future_earnings = self.generate_mock_future_earnings(symbol, company_info)
            
            # Combine all earnings
            all_earnings = real_earnings + future_earnings
            
            if all_earnings:
                if self.insert_earnings_data(all_earnings):
                    logger.info(f"✅ {symbol}: {len(real_earnings)} real + {len(future_earnings)} future earnings")
                    
                    # Save to earnings-icons directory
                    icon_file = f"earnings-icons/{symbol}.json"
                    with open(icon_file, 'w') as f:
                        json.dump({
                            'symbol': symbol,
                            'company_name': company_info.get('company_name', ''),
                            'sector': company_info.get('gics_sector', ''),
                            'total_earnings': len(all_earnings),
                            'real_earnings': len(real_earnings),
                            'future_earnings': len(future_earnings),
                            'curated_at': datetime.now().isoformat(),
                            'earnings_data': all_earnings
                        }, indent=2, default=str)
                    
                    logger.info(f"✅ Saved {symbol} data to {icon_file}")
                    return True
                else:
                    logger.error(f"❌ Failed to insert data for {symbol}")
                    return False
            else:
                logger.warning(f"⚠️ No earnings data retrieved for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
            return False

async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 curate_single_stock.py <SYMBOL>")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    curator = SingleStockCurator()
    success = await curator.curate_stock(symbol)
    
    if success:
        print(f"✅ Successfully curated {symbol}")
        sys.exit(0)
    else:
        print(f"❌ Failed to curate {symbol}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())