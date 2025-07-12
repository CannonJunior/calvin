#!/usr/bin/env python3
"""
Simple test MCP server for earnings dashboard integration
"""

import json
import sys
import asyncio
from typing import Any, Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMCPServer:
    def __init__(self):
        self.tools = {
            "get_stock_info": {
                "name": "get_stock_info",
                "description": "Get basic stock information including price and market cap",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            "analyze_sentiment": {
                "name": "analyze_sentiment", 
                "description": "Analyze market sentiment for a given text or stock symbol",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze for sentiment"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to get sentiment for"
                        }
                    }
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            logger.debug(f"Handling request: {method}")

            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "test-earnings-server",
                            "version": "1.0.0"
                        }
                    }
                }

            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "get_stock_info":
                    result = self.get_stock_info(arguments.get("symbol", ""))
                elif tool_name == "analyze_sentiment":
                    result = self.analyze_sentiment(arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")

                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }

            else:
                raise ValueError(f"Unknown method: {method}")

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Mock stock information"""
        # Mock data - in real implementation, this would fetch from APIs
        mock_data = {
            "AAPL": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 185.92,
                "change": 2.34,
                "change_percent": 1.28,
                "market_cap": 2850000000000,
                "volume": 45234567,
                "pe_ratio": 28.5,
                "sector": "Technology"
            },
            "MSFT": {
                "symbol": "MSFT", 
                "name": "Microsoft Corporation",
                "price": 378.91,
                "change": -1.23,
                "change_percent": -0.32,
                "market_cap": 2810000000000,
                "volume": 23456789,
                "pe_ratio": 34.2,
                "sector": "Technology"
            },
            "GOOGL": {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "price": 138.45,
                "change": 0.87,
                "change_percent": 0.63,
                "market_cap": 1750000000000,
                "volume": 18765432,
                "pe_ratio": 25.8,
                "sector": "Technology"
            }
        }

        symbol = symbol.upper()
        if symbol in mock_data:
            return mock_data[symbol]
        else:
            return {
                "symbol": symbol,
                "name": f"Unknown Company ({symbol})",
                "price": 100.00,
                "change": 0.00,
                "change_percent": 0.00,
                "market_cap": 1000000000,
                "volume": 1000000,
                "pe_ratio": 20.0,
                "sector": "Unknown"
            }

    def analyze_sentiment(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mock sentiment analysis"""
        text = arguments.get("text", "")
        symbol = arguments.get("symbol", "")
        
        # Mock sentiment analysis - in real implementation, this would use NLP
        import random
        
        sentiment_score = random.uniform(-1, 1)  # -1 (very negative) to 1 (very positive)
        
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": round(sentiment_score, 3),
            "confidence": round(random.uniform(0.6, 0.95), 3),
            "text_analyzed": text or f"Market sentiment for {symbol}",
            "symbol": symbol,
            "factors": [
                "Earnings expectations",
                "Market volatility", 
                "Sector performance",
                "News sentiment"
            ]
        }

    async def run(self):
        """Main server loop"""
        logger.info("Test MCP Server starting...")
        
        try:
            while True:
                # Read JSON-RPC message from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue

                logger.debug(f"Received: {line}")

                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # Send response to stdout
                    response_json = json.dumps(response)
                    print(response_json)
                    sys.stdout.flush()
                    
                    logger.debug(f"Sent: {response_json}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")

if __name__ == "__main__":
    server = TestMCPServer()
    asyncio.run(server.run())