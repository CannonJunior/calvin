#!/usr/bin/env python3
"""
Check current AAPL earnings data and source URLs
"""

import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_aapl_data():
    """Check current AAPL earnings data"""
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'calvin_earnings',
        'user': 'calvin_user',
        'password': 'calvin_pass'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check AAPL earnings data
        cursor.execute("""
            SELECT earnings_date, quarter, year, actual_eps, estimated_eps, 
                   beat_miss_meet, source_url, price_change_percent
            FROM earnings 
            WHERE symbol = 'AAPL' 
            ORDER BY earnings_date DESC
        """)
        
        earnings = cursor.fetchall()
        
        logger.info(f"📊 Found {len(earnings)} AAPL earnings records:")
        
        for earning in earnings:
            earnings_date, quarter, year, actual_eps, estimated_eps, beat_miss_meet, source_url, price_change = earning
            
            earnings_type = "PAST" if actual_eps else "FUTURE"
            url_status = "✅" if source_url and source_url != "#" else "❌ Missing/Invalid"
            price_status = "✅" if price_change is not None else "❌ Missing"
            
            logger.info(f"  {earnings_date} Q{quarter} {year} [{earnings_type}]")
            logger.info(f"    EPS: {actual_eps or 'N/A'} (est: {estimated_eps or 'N/A'}) | {beat_miss_meet or 'N/A'}")
            logger.info(f"    Price Change: {price_change or 'N/A'}% {price_status}")
            logger.info(f"    Source URL: {url_status} - {source_url or 'None'}")
            logger.info("")
        
        cursor.close()
        conn.close()
        
        return earnings
        
    except Exception as e:
        logger.error(f"❌ Error checking AAPL data: {e}")
        return []

if __name__ == "__main__":
    check_aapl_data()