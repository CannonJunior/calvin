#!/usr/bin/env python3
"""
Update earnings table schema to add source_url field
"""

import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_earnings_schema():
    """Add source_url field to earnings table"""
    
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
        
        # Check if source_url column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'earnings' AND column_name = 'source_url'
        """)
        
        if cursor.fetchone():
            logger.info("✅ source_url column already exists in earnings table")
        else:
            # Add source_url column
            cursor.execute("""
                ALTER TABLE earnings 
                ADD COLUMN source_url VARCHAR(500)
            """)
            logger.info("✅ Added source_url column to earnings table")
        
        # Check if data_verified_date column exists (from AAPL script)
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'earnings' AND column_name = 'data_verified_date'
        """)
        
        if cursor.fetchone():
            logger.info("✅ data_verified_date column already exists")
        else:
            # Add data_verified_date column
            cursor.execute("""
                ALTER TABLE earnings 
                ADD COLUMN data_verified_date DATE
            """)
            logger.info("✅ Added data_verified_date column to earnings table")
        
        # Also check companies table for additional market cap fields
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'companies' AND column_name = 'market_cap_billions'
        """)
        
        if cursor.fetchone():
            logger.info("✅ market_cap_billions column already exists in companies table")
        else:
            cursor.execute("""
                ALTER TABLE companies 
                ADD COLUMN market_cap_billions DECIMAL(10, 3),
                ADD COLUMN market_cap_date DATE,
                ADD COLUMN market_cap_source VARCHAR(500)
            """)
            logger.info("✅ Added market cap fields to companies table")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 Database schema updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating schema: {e}")
        return False

if __name__ == "__main__":
    update_earnings_schema()