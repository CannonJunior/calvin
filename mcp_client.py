#!/usr/bin/env python3
"""
Calvin Stock Prediction Tool - MCP Client
Uses FastMCP Client pattern with proper mcpServers configuration
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastmcp import Client
import logging

logger = logging.getLogger(__name__)

class CalvinMCPClient:
    """Calvin Stock Prediction Tool MCP Client using proper FastMCP Client pattern"""
    
    def __init__(self):
        self.client = None
        self.config = self._create_mcp_config()
        
    def _create_mcp_config(self) -> Dict[str, Any]:
        """Create MCP configuration with all Calvin servers"""
        # Get the project root directory
        project_root = Path(__file__).parent
        
        return {
            "mcpServers": {
                "company": {
                    "command": "python3",
                    "args": [str(project_root / "packages/mcp-company-server/server.py")]
                },
                "earnings": {
                    "command": "python3", 
                    "args": [str(project_root / "packages/mcp-earnings-server/server.py")]
                },
                "prediction": {
                    "command": "python3",
                    "args": [str(project_root / "packages/mcp-prediction-server/server.py")]
                },
                "finance": {
                    "command": "python3",
                    "args": [str(project_root / "packages/mcp-finance-server/server.py")]
                },
                "sentiment": {
                    "command": "python3",
                    "args": [str(project_root / "packages/mcp-sentiment-server/server.py")]
                }
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = Client(self.config)
        await self.client.__aenter__()
        logger.info("Calvin MCP Client initialized successfully")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
        logger.info("Calvin MCP Client shut down")
    
    async def list_all_tools(self) -> Dict[str, List[str]]:
        """List all available tools from all servers"""
        try:
            tools = await self.client.list_tools()
            
            # Group tools by server
            tools_by_server = {}
            for tool in tools:
                # Extract server name from tool name or use a default grouping
                server_name = getattr(tool, 'server_name', 'unknown')
                if server_name not in tools_by_server:
                    tools_by_server[server_name] = []
                tools_by_server[server_name].append(tool.name)
            
            return tools_by_server
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return {}
    
    async def list_all_resources(self) -> List[str]:
        """List all available resources from all servers"""
        try:
            resources = await self.client.list_resources()
            return [r.name for r in resources]
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            return []
    
    async def list_all_prompts(self) -> List[str]:
        """List all available prompts from all servers"""
        try:
            prompts = await self.client.list_prompts()
            return [p.name for p in prompts]
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            return []
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool with the given arguments"""
        try:
            result = await self.client.call_tool(tool_name, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def read_resource(self, resource_uri: str) -> str:
        """Read a resource by URI"""
        try:
            result = await self.client.read_resource(resource_uri)
            return result
        except Exception as e:
            logger.error(f"Failed to read resource {resource_uri}: {e}")
            return f"Error: {e}"
    
    async def get_prompt(self, prompt_name: str, **arguments) -> str:
        """Get a prompt with arguments"""
        try:
            result = await self.client.get_prompt(prompt_name, arguments=arguments)
            if result.messages and len(result.messages) > 0:
                return result.messages[0].content.text
            return "No content in prompt response"
        except Exception as e:
            logger.error(f"Failed to get prompt {prompt_name}: {e}")
            return f"Error: {e}"
    
    # Calvin-specific convenience methods
    
    async def get_companies(self, limit: int = 100, sector: Optional[str] = None) -> Dict[str, Any]:
        """Get companies using the company server"""
        return await self.call_tool("get_companies", limit=limit, sector=sector, sp500_only=True)
    
    async def search_companies(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search companies by name or symbol"""
        return await self.call_tool("search_companies", query=query, limit=limit)
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price and metrics"""
        return await self.call_tool("get_stock_price", symbol=symbol)
    
    async def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive company information"""
        return await self.call_tool("get_company_info", symbol=symbol)
    
    async def get_earnings_calendar(self, start_date: Optional[str] = None, 
                                  end_date: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get earnings calendar"""
        return await self.call_tool("get_earnings_calendar", 
                                  start_date=start_date, end_date=end_date, limit=limit)
    
    async def analyze_earnings_surprise(self, symbol: str, actual_eps: float, 
                                      expected_eps: float, actual_revenue: Optional[float] = None,
                                      expected_revenue: Optional[float] = None) -> Dict[str, Any]:
        """Analyze earnings surprise"""
        return await self.call_tool("analyze_earnings_surprise",
                                  symbol=symbol, actual_eps=actual_eps, expected_eps=expected_eps,
                                  actual_revenue=actual_revenue, expected_revenue=expected_revenue)
    
    async def predict_next_day_performance(self, symbol: str, earnings_data: Dict[str, Any],
                                         market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Predict next-day stock performance"""
        return await self.call_tool("predict_next_day_performance",
                                  symbol=symbol, earnings_data=earnings_data, market_context=market_context)
    
    async def get_top_predictions(self, confidence_threshold: float = 0.7, limit: int = 10) -> Dict[str, Any]:
        """Get top recent predictions"""
        return await self.call_tool("get_top_predictions",
                                  confidence_threshold=confidence_threshold, limit=limit)
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        return await self.call_tool("analyze_sentiment", text=text)
    
    async def analyze_earnings_sentiment(self, earnings_text: str, 
                                       context: Optional[str] = "earnings_call") -> Dict[str, Any]:
        """Analyze earnings-specific sentiment"""
        return await self.call_tool("analyze_earnings_sentiment", 
                                  earnings_text=earnings_text, context=context)
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        try:
            # Try to list tools to check if servers are responsive
            tools = await self.list_all_tools()
            resources = await self.list_all_resources()
            prompts = await self.list_all_prompts()
            
            return {
                "status": "healthy",
                "servers": list(self.config["mcpServers"].keys()),
                "tools_count": sum(len(tool_list) for tool_list in tools.values()),
                "resources_count": len(resources),
                "prompts_count": len(prompts),
                "tools_by_server": tools
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "servers": list(self.config["mcpServers"].keys())
            }

# Convenience function for quick usage
async def create_calvin_client():
    """Create and return a Calvin MCP client"""
    return CalvinMCPClient()

# Example usage and testing
async def main():
    """Example usage of Calvin MCP Client"""
    async with CalvinMCPClient() as client:
        # Test server status
        status = await client.get_server_status()
        print(f"Server Status: {json.dumps(status, indent=2)}")
        
        # List available tools
        tools = await client.list_all_tools()
        print(f"Available Tools: {json.dumps(tools, indent=2)}")
        
        # Test company search
        companies = await client.search_companies("Apple")
        print(f"Company Search Results: {json.dumps(companies, indent=2)}")
        
        # Test stock price
        stock_data = await client.get_stock_price("AAPL")
        print(f"Stock Data: {json.dumps(stock_data, indent=2)}")
        
        # Test sentiment analysis
        sentiment = await client.analyze_sentiment("The company beat earnings expectations significantly!")
        print(f"Sentiment Analysis: {json.dumps(sentiment, indent=2)}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run example
    asyncio.run(main())