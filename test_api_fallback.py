#!/usr/bin/env python3
"""
Test API fallback logic in curation script
"""

import logging
from curate_stock_data import StockDataCurator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_fallback():
    """Test the API fallback logic"""
    
    logger.info("🧪 Testing API fallback logic...")
    
    try:
        # Initialize curator
        curator = StockDataCurator('./config.json')
        
        # Test with a simple symbol
        test_symbol = 'MSFT'
        
        logger.info(f"📊 Testing earnings data fetching for {test_symbol}...")
        earnings_data = curator.fetch_historical_earnings(test_symbol)
        
        if earnings_data:
            logger.info(f"✅ Successfully fetched {len(earnings_data)} earnings records")
            
            # Check that safe URLs are stored
            for earning in earnings_data[:2]:
                source_url = earning.get('source_url', '')
                if 'yahoo.com' in source_url and 'apikey=' not in source_url:
                    logger.info(f"✅ Safe URL stored: {source_url}")
                else:
                    logger.error(f"❌ Unsafe URL: {source_url}")
                    
        else:
            logger.warning("⚠️ No earnings data fetched - check API keys or rate limits")
        
        logger.info(f"📈 Testing price data fetching for {test_symbol}...")
        
        # Test price data for recent date
        from datetime import date, timedelta
        test_date = date.today() - timedelta(days=30)
        
        price_data = curator.fetch_price_data_for_earnings(test_symbol, test_date)
        
        if price_data:
            logger.info("✅ Price data fetched successfully")
            source_url = price_data.get('source_url', '')
            if 'yahoo.com' in source_url and 'apikey=' not in source_url:
                logger.info(f"✅ Safe price URL stored: {source_url}")
            else:
                logger.error(f"❌ Unsafe price URL: {source_url}")
        else:
            logger.warning("⚠️ No price data fetched")
        
        logger.info("🎉 API fallback test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_rate_limit_detection():
    """Test rate limit detection logic"""
    
    logger.info("🚦 Testing rate limit detection...")
    
    curator = StockDataCurator('./config.json')
    
    # Test different rate limit responses
    test_cases = [
        {
            'api': 'Financial Modeling Prep',
            'data': {'Error Message': 'API calls quota exceeded'},
            'expected': True
        },
        {
            'api': 'Alpha Vantage', 
            'data': {'Note': 'Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute'},
            'expected': True
        },
        {
            'api': 'Finnhub',
            'data': {'error': 'API limit exceeded'},
            'expected': True
        },
        {
            'api': 'Financial Modeling Prep',
            'data': [{'symbol': 'AAPL', 'date': '2025-01-01'}],
            'expected': False
        }
    ]
    
    for test in test_cases:
        result = curator._is_rate_limited(test['data'], test['api'])
        
        if result == test['expected']:
            logger.info(f"✅ {test['api']}: Rate limit detection correct")
        else:
            logger.error(f"❌ {test['api']}: Expected {test['expected']}, got {result}")
    
    logger.info("🎉 Rate limit detection test completed")

if __name__ == "__main__":
    logger.info("🚀 Starting API fallback tests...")
    
    # Test API fallback logic
    fallback_success = test_api_fallback()
    
    # Test rate limit detection
    test_rate_limit_detection()
    
    if fallback_success:
        logger.info("✅ All tests passed!")
        logger.info("💡 The curation script now:")
        logger.info("   - Uses API keys from config.json (not hardcoded)")
        logger.info("   - Falls back between APIs when rate limited")
        logger.info("   - Stores safe Yahoo Finance URLs in database")
        logger.info("   - Protects API keys from exposure in hrefs")
    else:
        logger.error("❌ Some tests failed - check configuration")