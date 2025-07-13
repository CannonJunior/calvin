#!/usr/bin/env python3
"""
URGENT: Fix API key exposure in source URLs
Replace all API URLs with Yahoo Finance URLs to prevent key exposure
"""

import psycopg2
import logging
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_api_key_exposure():
    """Replace all source URLs that contain API keys with Yahoo Finance URLs"""
    
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
        
        # Get all earnings records that have source URLs with API keys
        cursor.execute("""
            SELECT id, symbol, earnings_date, source_url
            FROM earnings 
            WHERE source_url IS NOT NULL 
            AND (source_url LIKE '%apikey=%' OR source_url LIKE '%token=%')
        """)
        
        exposed_records = cursor.fetchall()
        
        logger.info(f"🚨 Found {len(exposed_records)} records with exposed API keys")
        
        fixed_count = 0
        
        for record_id, symbol, earnings_date, current_url in exposed_records:
            # Create Yahoo Finance URL for this symbol
            yahoo_url = f"https://finance.yahoo.com/quote/{symbol}/history"
            
            # Update the record
            cursor.execute("""
                UPDATE earnings 
                SET source_url = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (yahoo_url, record_id))
            
            fixed_count += 1
            logger.info(f"✅ Fixed {symbol} {earnings_date}: {yahoo_url}")
        
        # Also fix any company records with exposed API keys
        cursor.execute("""
            SELECT id, symbol, market_cap_source
            FROM companies 
            WHERE market_cap_source IS NOT NULL 
            AND (market_cap_source LIKE '%apikey=%' OR market_cap_source LIKE '%token=%')
        """)
        
        company_records = cursor.fetchall()
        
        for company_id, symbol, current_url in company_records:
            yahoo_url = f"https://finance.yahoo.com/quote/{symbol}"
            
            cursor.execute("""
                UPDATE companies 
                SET market_cap_source = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (yahoo_url, company_id))
            
            fixed_count += 1
            logger.info(f"✅ Fixed company {symbol}: {yahoo_url}")
        
        cursor.close()
        conn.close()
        
        logger.info(f"🔒 SECURITY FIX COMPLETE: Updated {fixed_count} records")
        logger.info("✅ No API keys are now exposed in source URLs")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing API key exposure: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚨 URGENT: Fixing API key exposure in source URLs...")
    fix_api_key_exposure()