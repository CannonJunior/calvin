#!/usr/bin/env python3
"""
Calvin Stock Prediction Tool - Main Client (Updated MCP Pattern)
Uses proper FastMCP Client pattern with mcpServers configuration
"""

import asyncio
import json
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

from mcp_client import CalvinMCPClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
mcp_client = None
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
    
    global mcp_client
    
    # Initialize MCP client with proper pattern
    mcp_client = CalvinMCPClient()
    # Note: We don't enter the context here as it will be managed per request
    
    # Initialize AI agent
    await ai_agent.initialize()
    
    logger.info("Calvin Stock Prediction Tool started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Calvin Stock Prediction Tool...")
    await ai_agent.cleanup()

# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    async with CalvinMCPClient() as client:
        status = await client.get_server_status()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "mcp_servers": status
        }

@app.get("/api/servers")
async def get_servers():
    """Get status of all MCP servers"""
    async with CalvinMCPClient() as client:
        return await client.get_server_status()

@app.post("/api/tools/{tool_name}")
async def call_tool(tool_name: str, payload: Dict[str, Any]):
    """Call a tool on MCP servers"""
    async with CalvinMCPClient() as client:
        return await client.call_tool(tool_name, **payload)

@app.get("/api/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get a resource from MCP servers"""
    async with CalvinMCPClient() as client:
        return await client.read_resource(resource_uri)

@app.get("/api/prompts/{prompt_name}")
async def get_prompt(prompt_name: str, arguments: Dict[str, Any] = None):
    """Get a prompt from MCP servers"""
    async with CalvinMCPClient() as client:
        return await client.get_prompt(prompt_name, **(arguments or {}))

# Convenience endpoints for common operations
@app.get("/api/companies")
async def get_companies(limit: int = 100, sector: str = None):
    """Get S&P 500 companies"""
    async with CalvinMCPClient() as client:
        return await client.get_companies(limit=limit, sector=sector)

@app.get("/api/companies/search")
async def search_companies(query: str, limit: int = 10):
    """Search companies by name or symbol"""
    async with CalvinMCPClient() as client:
        return await client.search_companies(query=query, limit=limit)

@app.get("/api/stocks/{symbol}")
async def get_stock_data(symbol: str):
    """Get comprehensive stock data"""
    async with CalvinMCPClient() as client:
        # Get multiple data points in parallel
        stock_price = await client.get_stock_price(symbol)
        company_info = await client.get_company_info(symbol)
        
        return {
            "symbol": symbol,
            "price_data": stock_price,
            "company_info": company_info,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/earnings/calendar")
async def get_earnings_calendar(start_date: str = None, end_date: str = None, limit: int = 50):
    """Get earnings calendar"""
    async with CalvinMCPClient() as client:
        return await client.get_earnings_calendar(start_date=start_date, end_date=end_date, limit=limit)

@app.get("/api/predictions/top")
async def get_top_predictions(confidence_threshold: float = 0.7, limit: int = 10):
    """Get top predictions"""
    async with CalvinMCPClient() as client:
        return await client.get_top_predictions(confidence_threshold=confidence_threshold, limit=limit)

@app.post("/api/predictions/analyze")
async def analyze_stock_prediction(payload: Dict[str, Any]):
    """Generate stock prediction analysis"""
    symbol = payload.get("symbol")
    earnings_data = payload.get("earnings_data", {})
    market_context = payload.get("market_context")
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    async with CalvinMCPClient() as client:
        # Get current stock data
        stock_data = await client.get_stock_price(symbol)
        
        # Generate prediction
        prediction = await client.predict_next_day_performance(
            symbol=symbol,
            earnings_data=earnings_data,
            market_context=market_context
        )
        
        return {
            "symbol": symbol,
            "stock_data": stock_data,
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/sentiment/analyze")
async def analyze_sentiment(payload: Dict[str, Any]):
    """Analyze sentiment of text"""
    text = payload.get("text")
    earnings_context = payload.get("earnings_context", False)
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    async with CalvinMCPClient() as client:
        if earnings_context:
            return await client.analyze_earnings_sentiment(text)
        else:
            return await client.analyze_sentiment(text)

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
                async with CalvinMCPClient() as client:
                    status = await client.get_server_status()
                    await websocket.send_text(json.dumps({
                        "type": "server_status",
                        "status": status
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
                
            elif message.get("type") == "mcp_call":
                # Allow WebSocket clients to call MCP tools
                tool_name = message.get("tool_name")
                args = message.get("args", {})
                
                if tool_name:
                    async with CalvinMCPClient() as client:
                        result = await client.call_tool(tool_name, **args)
                        await websocket.send_text(json.dumps({
                            "type": "mcp_response",
                            "tool_name": tool_name,
                            "result": result
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
            <p>Main client is running with proper MCP pattern.</p>
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