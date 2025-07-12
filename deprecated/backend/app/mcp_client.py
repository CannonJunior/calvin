#!/usr/bin/env python3
"""
MCP Client for Calvin Stock Prediction Tool
Manages connections to multiple MCP servers based on JSON configuration
"""
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerConnection:
    """Represents a connection to a single MCP server"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.process = None
        self.is_connected = False
        
    async def start(self) -> bool:
        """Start the MCP server process"""
        try:
            command = self.config.get("command", "python")
            args = self.config.get("args", [])
            env = self.config.get("env", {})
            
            # Build full command
            full_command = [command] + args
            
            # Start the process
            self.process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env or None
            )
            
            # Give it a moment to start
            await asyncio.sleep(1)
            
            # Check if process is still running
            if self.process.returncode is None:
                self.is_connected = True
                logger.info(f"MCP server '{self.name}' started successfully")
                return True
            else:
                logger.error(f"MCP server '{self.name}' failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP server '{self.name}': {e}")
            return False
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            
            self.is_connected = False
            logger.info(f"MCP server '{self.name}' stopped")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on this MCP server"""
        if not self.is_connected:
            return {"error": f"Server '{self.name}' is not connected"}
        
        # For now, simulate tool calls since we don't have full MCP client implementation
        # In a real implementation, this would use the MCP protocol
        logger.info(f"Calling tool '{tool_name}' on server '{self.name}' with args: {arguments}")
        
        return {
            "server": self.name,
            "tool": tool_name,
            "arguments": arguments,
            "result": "simulated_response",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_resource(self, resource_uri: str) -> str:
        """Get a resource from this MCP server"""
        if not self.is_connected:
            return f"Error: Server '{self.name}' is not connected"
        
        # Simulate resource retrieval
        logger.info(f"Getting resource '{resource_uri}' from server '{self.name}'")
        
        return f"Resource content from {self.name}: {resource_uri}"

class MCPClient:
    """Main MCP client that manages multiple server connections"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "mcp_servers.json"
        
        self.config_path = Path(config_path)
        self.servers: Dict[str, MCPServerConnection] = {}
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load MCP server configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Create server connection objects
            mcp_servers = self.config.get("mcpServers", {})
            for server_name, server_config in mcp_servers.items():
                self.servers[server_name] = MCPServerConnection(server_name, server_config)
            
            logger.info(f"Loaded configuration for {len(self.servers)} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to load MCP configuration: {e}")
            raise
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        results = {}
        
        for server_name, server in self.servers.items():
            results[server_name] = await server.start()
        
        connected_count = sum(1 for success in results.values() if success)
        logger.info(f"Started {connected_count}/{len(self.servers)} MCP servers successfully")
        
        return results
    
    async def stop_all_servers(self):
        """Stop all MCP servers"""
        for server in self.servers.values():
            await server.stop()
        
        logger.info("All MCP servers stopped")
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server"""
        if server_name not in self.servers:
            return {"error": f"Server '{server_name}' not found"}
        
        server = self.servers[server_name]
        return await server.call_tool(tool_name, arguments)
    
    async def get_resource(self, server_name: str, resource_uri: str) -> str:
        """Get a resource from a specific MCP server"""
        if server_name not in self.servers:
            return f"Error: Server '{server_name}' not found"
        
        server = self.servers[server_name]
        return await server.get_resource(resource_uri)
    
    async def get_companies(self, limit: int = 10, sector: Optional[str] = None) -> Dict[str, Any]:
        """Get companies using the company-data server"""
        return await self.call_tool("company-data", "get_companies", {
            "limit": limit,
            "sector": sector,
            "sp500_only": True
        })
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get stock price using the finance-data server"""
        return await self.call_tool("finance-data", "get_stock_price", {
            "symbol": symbol
        })
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using the sentiment-analysis server"""
        return await self.call_tool("sentiment-analysis", "analyze_sentiment", {
            "text": text
        })
    
    async def predict_stock_performance(self, symbol: str, earnings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict next-day stock performance using the predictions server"""
        return await self.call_tool("stock-predictions", "predict_next_day_performance", {
            "symbol": symbol,
            "earnings_data": earnings_data
        })
    
    async def get_earnings_calendar(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get earnings calendar using the earnings-analysis server"""
        return await self.call_tool("earnings-analysis", "get_earnings_calendar", {
            "start_date": start_date,
            "end_date": end_date,
            "limit": 50
        })
    
    async def batch_analysis(self, symbol: str) -> Dict[str, Any]:
        """Perform comprehensive analysis for a stock symbol"""
        try:
            # Get stock data
            stock_data = await self.get_stock_price(symbol)
            
            # Get company info
            company_info = await self.call_tool("finance-data", "get_company_info", {"symbol": symbol})
            
            # Get earnings calendar
            earnings_calendar = await self.call_tool("finance-data", "get_earnings_calendar", {"symbol": symbol})
            
            # Get company details
            company_details = await self.call_tool("company-data", "get_company_by_symbol", {"symbol": symbol})
            
            # Combine all data
            return {
                "symbol": symbol,
                "stock_data": stock_data,
                "company_info": company_info,
                "earnings_calendar": earnings_calendar,
                "company_details": company_details,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch analysis failed for {symbol}: {e}")
            return {"error": f"Batch analysis failed: {str(e)}"}
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        status = {}
        
        for server_name, server in self.servers.items():
            status[server_name] = {
                "connected": server.is_connected,
                "description": server.config.get("description", ""),
                "capabilities": server.config.get("capabilities", []),
                "tools": server.config.get("tools", []),
                "resources": server.config.get("resources", [])
            }
        
        return {
            "servers": status,
            "total_servers": len(self.servers),
            "connected_servers": sum(1 for s in self.servers.values() if s.is_connected),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get list of available tools for each server"""
        tools = {}
        
        for server_name, server in self.servers.items():
            if server.is_connected:
                tools[server_name] = server.config.get("tools", [])
        
        return tools
    
    def get_available_resources(self) -> Dict[str, List[str]]:
        """Get list of available resources for each server"""
        resources = {}
        
        for server_name, server in self.servers.items():
            if server.is_connected:
                resources[server_name] = server.config.get("resources", [])
        
        return resources

# Global MCP client instance
mcp_client = None

async def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client instance"""
    global mcp_client
    
    if mcp_client is None:
        mcp_client = MCPClient()
        await mcp_client.start_all_servers()
    
    return mcp_client

async def shutdown_mcp_client():
    """Shutdown the global MCP client"""
    global mcp_client
    
    if mcp_client:
        await mcp_client.stop_all_servers()
        mcp_client = None

# Example usage
if __name__ == "__main__":
    async def main():
        # Create and start MCP client
        client = MCPClient()
        
        # Start all servers
        results = await client.start_all_servers()
        print("Server start results:", results)
        
        # Get server status
        status = client.get_server_status()
        print("Server status:", json.dumps(status, indent=2))
        
        # Example tool calls
        companies = await client.get_companies(limit=5)
        print("Companies:", companies)
        
        stock_price = await client.get_stock_price("AAPL")
        print("AAPL stock price:", stock_price)
        
        sentiment = await client.analyze_sentiment("Apple reported strong quarterly earnings with revenue beating expectations")
        print("Sentiment analysis:", sentiment)
        
        # Batch analysis
        analysis = await client.batch_analysis("AAPL")
        print("Batch analysis:", json.dumps(analysis, indent=2))
        
        # Stop all servers
        await client.stop_all_servers()
    
    # Run the example
    asyncio.run(main())