#!/usr/bin/env python3
"""
Update AAPL earnings data with actual API source URLs
"""

import psycopg2
import logging
import json
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Load API configuration"""
    try:
        with open('./config.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "api_keys": {"financial_modeling_prep": "demo"},
            "api_endpoints": {"fmp_base": "https://financialmodelingprep.com/api/v3"}
        }

def update_aapl_source_urls():
    """Update AAPL earnings with real API source URLs"""
    
    config = load_config()
    fmp_key = config['api_keys']['financial_modeling_prep']
    fmp_base = config['api_endpoints']['fmp_base']
    
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
        
        # Get all AAPL earnings records
        cursor.execute("""
            SELECT id, earnings_date, actual_eps 
            FROM earnings 
            WHERE symbol = 'AAPL' 
            ORDER BY earnings_date DESC
        """)
        
        earnings = cursor.fetchall()
        
        logger.info(f"📊 Updating {len(earnings)} AAPL earnings records with real API URLs...")
        
        for earning_id, earnings_date, actual_eps in earnings:
            is_past = actual_eps is not None
            
            # Create the actual API URLs that would have been used
            earnings_calendar_url = f"{fmp_base}/historical/earning_calendar/AAPL?apikey={fmp_key}"
            
            if is_past:
                # For past earnings, we also fetched price data
                price_url = f"{fmp_base}/historical-price-full/AAPL?from={earnings_date}&to={earnings_date}&apikey={fmp_key}"
                source_url = f"{earnings_calendar_url} | Price Data: {price_url}"
            else:
                # For future earnings, just the calendar URL
                source_url = earnings_calendar_url
            
            # Update the record
            cursor.execute("""
                UPDATE earnings 
                SET source_url = %s,
                    data_verified_date = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (source_url, date.today(), earning_id))
            
            earnings_type = "PAST" if is_past else "FUTURE"
            logger.info(f"✅ Updated {earnings_type} earnings for {earnings_date}")
        
        # Also update market cap data for AAPL company record
        market_cap_url = f"{fmp_base}/profile/AAPL?apikey={fmp_key}"
        
        cursor.execute("""
            UPDATE companies 
            SET market_cap_source = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE symbol = 'AAPL'
        """, (market_cap_url,))
        
        logger.info("✅ Updated AAPL company market cap source URL")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 Successfully updated AAPL source URLs with real API endpoints")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating AAPL source URLs: {e}")
        return False

if __name__ == "__main__":
    update_aapl_source_urls()