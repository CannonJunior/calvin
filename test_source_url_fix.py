#!/usr/bin/env python3
"""
Test script to verify source URL functionality
"""

import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_aapl_source_urls():
    """Test that AAPL earnings have proper source URLs"""
    
    try:
        # Test the PostgreSQL API
        response = requests.get('http://localhost:5002/api/earnings/timeline', timeout=5)
        response.raise_for_status()
        
        data = response.json()
        timeline_data = data.get('timeline_data', [])
        
        # Find AAPL earnings
        aapl_earnings = [item for item in timeline_data if item.get('symbol') == 'AAPL']
        
        logger.info(f"📊 Found {len(aapl_earnings)} AAPL earnings records")
        
        source_url_count = 0
        valid_url_count = 0
        
        for earning in aapl_earnings:
            source_url = earning.get('source_url')
            
            if source_url:
                source_url_count += 1
                
                # Check if it's a real API URL (not just # or nasdaq.com)
                if 'financialmodelingprep.com' in source_url and 'apikey=' in source_url:
                    valid_url_count += 1
                    logger.info(f"✅ {earning['date']}: Valid API URL")
                else:
                    logger.warning(f"⚠️  {earning['date']}: Invalid URL - {source_url}")
            else:
                logger.error(f"❌ {earning['date']}: No source URL")
        
        logger.info(f"📈 Results:")
        logger.info(f"   Total AAPL earnings: {len(aapl_earnings)}")
        logger.info(f"   With source URLs: {source_url_count}")
        logger.info(f"   With valid API URLs: {valid_url_count}")
        
        if valid_url_count == len(aapl_earnings):
            logger.info("🎉 All AAPL earnings have valid source URLs!")
            return True
        else:
            logger.error("❌ Some AAPL earnings are missing valid source URLs")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing source URLs: {e}")
        return False

def test_dashboard_access():
    """Test if dashboard can access the earnings data"""
    
    try:
        # Test the same endpoint the dashboard uses
        response = requests.get('http://localhost:5002/api/earnings/timeline', timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if 'timeline_data' in data and len(data['timeline_data']) > 0:
            logger.info("✅ Dashboard API endpoint is working")
            
            # Check if any earnings have source URLs
            earnings_with_urls = [item for item in data['timeline_data'] if item.get('source_url')]
            
            logger.info(f"📊 Found {len(earnings_with_urls)} earnings with source URLs out of {len(data['timeline_data'])} total")
            
            return True
        else:
            logger.error("❌ No earnings data returned from API")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing dashboard access: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Testing source URL fixes...")
    
    # Test AAPL specifically
    aapl_success = test_aapl_source_urls()
    
    # Test dashboard access
    dashboard_success = test_dashboard_access()
    
    if aapl_success and dashboard_success:
        logger.info("🎉 All tests passed! Source URL fix is working correctly.")
        logger.info("💡 Now AAPL earnings-icons and pinned-info will have working Data Source links!")
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")