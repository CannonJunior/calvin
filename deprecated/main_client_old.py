#!/usr/bin/env python3
"""
Calvin Stock Prediction Tool - Main Client
Orchestrates all MCP servers and provides unified interface with AI agent
"""

import asyncio
import json
import subprocess
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manages MCP server processes and connections"""
    
    def __init__(self):
        self.servers = {}
        self.processes = {}
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def start_server(self, name: str, package_path: str, port: int):
        """Start an MCP server process"""
        try:
            # Install the package if needed
            install_process = await asyncio.create_subprocess_exec(
                "pip", "install", "-e", package_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await install_process.wait()
            
            # Start the server
            server_process = await asyncio.create_subprocess_exec(
                "python", f"{package_path}/server.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "MCP_SERVER_PORT": str(port)}
            )
            
            self.processes[name] = server_process
            self.servers[name] = {
                "port": port,
                "url": f"http://localhost:{port}",
                "status": "starting"
            }
            
            logger.info(f"Started MCP server {name} on port {port}")
            
            # Give server time to start
            await asyncio.sleep(2)
            
            # Check if server is healthy
            try:
                response = await self.client.get(f"http://localhost:{port}/health")
                if response.status_code == 200:
                    self.servers[name]["status"] = "healthy"
                    logger.info(f"MCP server {name} is healthy")
                else:
                    self.servers[name]["status"] = "unhealthy"
                    logger.warning(f"MCP server {name} health check failed")
            except Exception as e:
                self.servers[name]["status"] = "unhealthy"
                logger.error(f"Health check failed for {name}: {e}")
                
        except Exception as e:
            logger.error(f"Failed to start MCP server {name}: {e}")
            self.servers[name] = {"status": "failed", "error": str(e)}
    
    async def call_tool(self, server_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool on a specific MCP server"""
        if server_name not in self.servers:
            raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
        
        server = self.servers[server_name]
        if server["status"] != "healthy":
            raise HTTPException(status_code=503, detail=f"Server {server_name} is not healthy")
        
        try:
            response = await self.client.post(
                f"{server['url']}/tools/{tool_name}",
                json=kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling {tool_name}: {str(e)}")
    
    async def get_resource(self, server_name: str, resource_name: str) -> str:
        """Get a resource from a specific MCP server"""
        if server_name not in self.servers:
            raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
        
        server = self.servers[server_name]
        if server["status"] != "healthy":
            raise HTTPException(status_code=503, detail=f"Server {server_name} is not healthy")
        
        try:
            response = await self.client.get(f"{server['url']}/resources/{resource_name}")
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting resource: {str(e)}")
    
    async def shutdown_all(self):
        """Shutdown all MCP servers"""
        for name, process in self.processes.items():
            try:
                process.terminate()
                await process.wait()
                logger.info(f"Shut down MCP server {name}")
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")
        
        await self.client.aclose()

class OllamaAgent:
    """AI Agent using Ollama for intelligent analysis"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.available_models = []
        
    async def initialize(self):
        """Initialize the Ollama agent and check available models"""
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model["name"] for model in models_data.get("models", [])]
                logger.info(f"Available Ollama models: {self.available_models}")
            else:
                logger.warning("Could not connect to Ollama - AI features will be limited")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama agent: {e}")
    
    async def analyze_stock_with_ai(self, symbol: str, market_data: Dict[str, Any], 
                                   earnings_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use AI to analyze stock data and provide insights"""
        if not self.available_models:
            return {"error": "No AI models available"}
        
        # Use the first available model
        model = self.available_models[0]
        
        # Create analysis prompt
        prompt = f"""
        Analyze the following stock data for {symbol} and provide insights:
        
        Market Data: {json.dumps(market_data, indent=2)}
        
        {"Earnings Data: " + json.dumps(earnings_data, indent=2) if earnings_data else ""}
        
        Please provide:
        1. Overall market sentiment analysis
        2. Key risk factors
        3. Price prediction confidence
        4. Investment recommendation
        5. Key metrics to watch
        
        Keep your response concise but comprehensive.
        """
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "analysis": result.get("response", ""),
                    "model": model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"AI analysis failed with status {response.status_code}"}
                
        except Exception as e:
            return {"error": f"AI analysis error: {str(e)}"}
    
    async def chat_with_ai(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Chat interface with AI agent"""
        if not self.available_models:
            return {"error": "No AI models available"}
        
        model = self.available_models[0]
        
        # Create chat prompt with context
        prompt = f"""
        You are Calvin, an AI assistant for stock market analysis and prediction.
        
        {f"Context: {json.dumps(context, indent=2)}" if context else ""}
        
        User message: {user_message}
        
        Please provide a helpful response based on your knowledge of stock market analysis,
        earnings predictions, and financial data interpretation.
        """
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "model": model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"Chat failed with status {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Chat error: {str(e)}"}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()

# Global instances
mcp_manager = MCPServerManager()
ai_agent = OllamaAgent()

# FastAPI app
app = FastAPI(title="Calvin Stock Prediction Tool")

# Serve static files (web UI)
if Path("web").exists():
    app.mount("/static", StaticFiles(directory="web"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    logger.info("Starting Calvin Stock Prediction Tool...")
    
    # Start MCP servers
    servers_config = [
        ("company", "packages/mcp-company-server", 8001),
        ("earnings", "packages/mcp-earnings-server", 8002),
        ("prediction", "packages/mcp-prediction-server", 8003),
        ("finance", "packages/mcp-finance-server", 8004),
        ("sentiment", "packages/mcp-sentiment-server", 8005)
    ]
    
    tasks = []
    for name, path, port in servers_config:
        task = asyncio.create_task(mcp_manager.start_server(name, path, port))
        tasks.append(task)
    
    # Start all servers concurrently
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Initialize AI agent
    await ai_agent.initialize()
    
    logger.info("Calvin Stock Prediction Tool started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Calvin Stock Prediction Tool...")
    await mcp_manager.shutdown_all()
    await ai_agent.cleanup()

# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "servers": mcp_manager.servers
    }

@app.get("/api/servers")
async def get_servers():
    """Get status of all MCP servers"""
    return {"servers": mcp_manager.servers}

@app.post("/api/tools/{server_name}/{tool_name}")
async def call_tool(server_name: str, tool_name: str, payload: Dict[str, Any]):
    """Call a tool on a specific MCP server"""
    return await mcp_manager.call_tool(server_name, tool_name, **payload)

@app.get("/api/resources/{server_name}/{resource_name}")
async def get_resource(server_name: str, resource_name: str):
    """Get a resource from a specific MCP server"""
    return await mcp_manager.get_resource(server_name, resource_name)

@app.post("/api/ai/analyze")
async def ai_analyze_stock(payload: Dict[str, Any]):
    """AI-powered stock analysis"""
    symbol = payload.get("symbol")
    market_data = payload.get("market_data")
    earnings_data = payload.get("earnings_data")
    
    if not symbol or not market_data:
        raise HTTPException(status_code=400, detail="Symbol and market_data are required")
    
    return await ai_agent.analyze_stock_with_ai(symbol, market_data, earnings_data)

@app.post("/api/ai/chat")
async def ai_chat(payload: Dict[str, Any]):
    """Chat with AI agent"""
    message = payload.get("message")
    context = payload.get("context")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    return await ai_agent.chat_with_ai(message, context)

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "server_status":
                await websocket.send_text(json.dumps({
                    "type": "server_status",
                    "servers": mcp_manager.servers
                }))
            elif message.get("type") == "ai_chat":
                response = await ai_agent.chat_with_ai(
                    message.get("message", ""),
                    message.get("context")
                )
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "response": response
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend application"""
    web_path = Path("web/index.html")
    if web_path.exists():
        with open(web_path, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Calvin Stock Prediction Tool</title>
        </head>
        <body>
            <h1>Calvin Stock Prediction Tool</h1>
            <p>Main client is running. Web UI not found.</p>
            <p>API is available at <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Handle shutdown signals
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Run the server
    uvicorn.run(
        "main_client:app",
        host="0.0.0.0",
        port=3000,
        log_level="info",
        reload=False
    )