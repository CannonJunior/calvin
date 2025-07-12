#!/usr/bin/env python3
"""
Earnings Data Ingestion Service
Fetches real earnings data and populates PostgreSQL database
"""

import os
import json
import logging
import asyncio
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


class EarningsDataIngestion:
    def __init__(self):
        """Initialize the earnings data ingestion service"""
        
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
            # Create SQLAlchemy engine
            db_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.engine = create_engine(db_url)
            
            # Test connection
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
    
    def populate_companies_table(self):
        """Populate companies table with S&P 500 data"""
        if not self.sp500_companies or not self.engine:
            return False
        
        try:
            with self.engine.connect() as conn:
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
                        'symbol': company.get('symbol', ''),
                        'company_name': company.get('company_name', ''),
                        'gics_sector': company.get('gics_sector', ''),
                        'gics_sub_industry': company.get('gics_sub_industry', ''),
                        'headquarters': company.get('headquarters', ''),
                        'date_added': date_added,
                        'cik': company.get('cik', ''),
                        'founded': company.get('founded', '')
                    })
                
                conn.commit()
                logger.info(f"✅ Populated companies table with {len(self.sp500_companies)} companies")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to populate companies table: {e}")
            return False
    
    def generate_earnings_embedding(self, earnings_data: Dict) -> Optional[List[float]]:
        """Generate vector embedding for earnings data"""
        if not self.embedding_model:
            return None
        
        try:
            # Create text representation of earnings data
            text_repr = f"""
            Company: {earnings_data.get('symbol', '')}
            Sector: {earnings_data.get('sector', '')}
            Quarter: Q{earnings_data.get('quarter', '')} {earnings_data.get('year', '')}
            Estimated EPS: {earnings_data.get('estimated_eps', 'N/A')}
            Actual EPS: {earnings_data.get('actual_eps', 'N/A')}
            Beat/Miss: {earnings_data.get('beat_miss_meet', 'N/A')}
            Consensus: {earnings_data.get('consensus_rating', 'N/A')}
            """.strip()
            
            # Generate embedding
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
                return []
            
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                logger.warning(f"API limit or error for {symbol}: {data}")
                return []
            
            earnings_list = []
            
            # Process quarterly earnings
            quarterly_earnings = data.get('quarterlyEarnings', [])
            for earnings in quarterly_earnings[:8]:  # Last 8 quarters
                fiscal_date = earnings.get('fiscalDateEnding')
                if not fiscal_date:
                    continue
                
                try:
                    earnings_date = datetime.strptime(fiscal_date, '%Y-%m-%d').date()
                    quarter = ((earnings_date.month - 1) // 3) + 1
                    
                    # Extract numeric values
                    estimated_eps = self._safe_float(earnings.get('estimatedEPS'))
                    actual_eps = self._safe_float(earnings.get('reportedEPS'))
                    
                    # Calculate surprise
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
                        'confidence_score': 0.8  # Default confidence for Alpha Vantage data
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
        
        # Generate next 4 quarters
        for q in range(1, 5):
            # Calculate next earnings date (roughly every 3 months)
            earnings_date = current_date + timedelta(days=q * 90 + np.random.randint(-15, 15))
            quarter = ((earnings_date.month - 1) // 3) + 1
            
            # Generate realistic estimates based on sector
            sector = company_data.get('gics_sector', '')
            base_eps = self._get_sector_base_eps(sector)
            
            # Add some randomness but keep it realistic
            estimated_eps = base_eps * (1 + np.random.normal(0, 0.1))
            
            # Assign consensus rating based on sector trends
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
                    # Get company_id
                    company_query = text("SELECT id FROM companies WHERE symbol = :symbol")
                    result = conn.execute(company_query, {'symbol': earnings['symbol']})
                    company_row = result.fetchone()
                    
                    if not company_row:
                        logger.warning(f"Company not found: {earnings['symbol']}")
                        continue
                    
                    company_id = company_row[0]
                    
                    # Generate embedding
                    embedding = self.generate_earnings_embedding(earnings)
                    
                    # Insert earnings data
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
    
    async def ingest_all_earnings_data(self, limit: int = 50):
        """Ingest earnings data for all S&P 500 companies"""
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
                # Fetch real earnings data (past)
                real_earnings = self.fetch_earnings_data_alpha_vantage(symbol)
                
                # Generate future earnings data
                future_earnings = self.generate_mock_future_earnings(symbol, company)
                
                # Combine all earnings
                all_earnings = real_earnings + future_earnings
                
                if all_earnings:
                    if self.insert_earnings_data(all_earnings):
                        success_count += 1
                        logger.info(f"✅ {symbol}: {len(real_earnings)} real + {len(future_earnings)} future earnings")
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.warning(f"⚠️ No earnings data for {symbol}")
                
                # Rate limiting for API
                if self.alpha_vantage_key != 'demo' and i % 5 == 0:
                    await asyncio.sleep(12)  # Alpha Vantage: 5 calls per minute
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {symbol}: {e}")
        
        logger.info(f"🎉 Ingestion complete: {success_count} success, {error_count} errors")
        return success_count > 0
    
    async def run_ingestion(self):
        """Run the complete ingestion process"""
        logger.info("🚀 Starting earnings data ingestion service...")
        
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
        await self.ingest_all_earnings_data(limit=50)  # Limit to 50 for demo
        
        logger.info("✅ Earnings data ingestion completed")
        return True


async def main():
    """Main function"""
    ingestion_service = EarningsDataIngestion()
    await ingestion_service.run_ingestion()


if __name__ == "__main__":
    asyncio.run(main())