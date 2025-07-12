#!/usr/bin/env python3
"""
Test script for the new MCP client pattern
"""

import asyncio
import sys
import logging
from mcp_client import CalvinMCPClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_pattern():
    """Test the new MCP client pattern"""
    print("🧪 Testing Calvin MCP Client Pattern...")
    
    try:
        async with CalvinMCPClient() as client:
            print("✅ MCP Client initialized successfully")
            
            # Test 1: Get server status
            print("\n📊 Testing server status...")
            status = await client.get_server_status()
            print(f"Server Status: {status['status']}")
            print(f"Servers: {status.get('servers', [])}")
            print(f"Tools: {status.get('tools_count', 0)}")
            print(f"Resources: {status.get('resources_count', 0)}")
            
            # Test 2: List available tools
            print("\n🔧 Testing tool listing...")
            tools = await client.list_all_tools()
            print(f"Available tools by server: {tools}")
            
            # Test 3: Test company search
            print("\n🏢 Testing company search...")
            companies = await client.search_companies("Apple", limit=3)
            print(f"Company search results: {companies}")
            
            # Test 4: Test stock price (if yfinance is available)
            print("\n📈 Testing stock price...")
            try:
                stock_data = await client.get_stock_price("AAPL")
                if "error" in stock_data:
                    print(f"Stock price error: {stock_data['error']}")
                else:
                    print(f"AAPL price: ${stock_data.get('price', 'N/A')}")
            except Exception as e:
                print(f"Stock price test failed: {e}")
            
            # Test 5: Test sentiment analysis
            print("\n💭 Testing sentiment analysis...")
            try:
                sentiment = await client.analyze_sentiment("The company beat earnings expectations significantly!")
                print(f"Sentiment: {sentiment.get('sentiment', 'N/A')} (polarity: {sentiment.get('polarity', 'N/A')})")
            except Exception as e:
                print(f"Sentiment analysis test failed: {e}")
            
            # Test 6: Test earnings calendar
            print("\n📅 Testing earnings calendar...")
            try:
                earnings = await client.get_earnings_calendar(limit=3)
                print(f"Earnings calendar: {len(earnings.get('earnings_calendar', []))} entries")
            except Exception as e:
                print(f"Earnings calendar test failed: {e}")
            
            # Test 7: Test predictions
            print("\n🎯 Testing predictions...")
            try:
                predictions = await client.get_top_predictions(confidence_threshold=0.3, limit=3)
                print(f"Top predictions: {len(predictions.get('top_predictions', []))} entries")
            except Exception as e:
                print(f"Predictions test failed: {e}")
            
            print("\n🎉 All tests completed successfully!")
            
    except Exception as e:
        print(f"❌ MCP Client test failed: {e}")
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
    
    return True

async def main():
    """Main test function"""
    success = await test_mcp_pattern()
    
    if success:
        print("\n✅ MCP Pattern test passed!")
        sys.exit(0)
    else:
        print("\n❌ MCP Pattern test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())