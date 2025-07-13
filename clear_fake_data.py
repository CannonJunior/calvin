#!/usr/bin/env python3
"""
Clear all fake/generated earnings data and start fresh with real data
"""

import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_all_earnings_data():
    """Clear all earnings data from database"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'calvin_earnings',
        'user': 'calvin_user',
        'password': 'calvin_pass'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Delete all earnings data
        cursor.execute("DELETE FROM earnings")
        deleted_earnings = cursor.rowcount
        
        # Reset market cap data in companies table
        cursor.execute("""
            UPDATE companies 
            SET market_cap_billions = NULL,
                market_cap_date = NULL, 
                market_cap_source = NULL,
                updated_at = CURRENT_TIMESTAMP
        """)
        updated_companies = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Cleared {deleted_earnings} fake earnings records")
        logger.info(f"✅ Reset market cap data for {updated_companies} companies")
        logger.info("🔄 Database is now clean and ready for real data")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing data: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧹 Clearing all fake earnings data...")
    clear_all_earnings_data()