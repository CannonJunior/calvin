#!/usr/bin/env python3
"""
MCP Proxy API Endpoints
Provides HTTP endpoints that proxy requests to MCP servers
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel
import asyncio
import logging

from app.mcp_client import get_mcp_client, MCPClient

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response models
class MCPToolRequest(BaseModel):
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]

class MCPResourceRequest(BaseModel):
    server_name: str
    resource_uri: str

class SentimentAnalysisRequest(BaseModel):
    text: str
    context: Optional[str] = "general"

class StockPredictionRequest(BaseModel):
    symbol: str
    earnings_data: Dict[str, Any]
    market_context: Optional[Dict[str, Any]] = None

class BatchAnalysisRequest(BaseModel):
    symbol: str

# MCP Server Status and Management
@router.get("/mcp/status")
async def get_mcp_status(client: MCPClient = Depends(get_mcp_client)):
    """Get status of all MCP servers"""
    try:
        return client.get_server_status()
    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/tools")
async def get_available_tools(client: MCPClient = Depends(get_mcp_client)):
    """Get list of available tools for each MCP server"""
    try:
        return client.get_available_tools()
    except Exception as e:
        logger.error(f"Failed to get available tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/resources")
async def get_available_resources(client: MCPClient = Depends(get_mcp_client)):
    """Get list of available resources for each MCP server"""
    try:
        return client.get_available_resources()
    except Exception as e:
        logger.error(f"Failed to get available resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Generic MCP Tool and Resource Endpoints
@router.post("/mcp/tool")
async def call_mcp_tool(
    request: MCPToolRequest,
    client: MCPClient = Depends(get_mcp_client)
):
    """Call a tool on an MCP server"""
    try:
        result = await client.call_tool(
            request.server_name,
            request.tool_name,
            request.arguments
        )
        return result
    except Exception as e:
        logger.error(f"MCP tool call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/resource")
async def get_mcp_resource(
    request: MCPResourceRequest,
    client: MCPClient = Depends(get_mcp_client)
):
    """Get a resource from an MCP server"""
    try:
        result = await client.get_resource(
            request.server_name,
            request.resource_uri
        )
        return {"content": result}
    except Exception as e:
        logger.error(f"MCP resource request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Company Data Endpoints (via MCP)
@router.get("/companies")
async def get_companies(
    limit: int = Query(10, ge=1, le=500),
    sector: Optional[str] = Query(None),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get list of companies via MCP company-data server"""
    try:
        result = await client.get_companies(limit=limit, sector=sector)
        return result
    except Exception as e:
        logger.error(f"Failed to get companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/{symbol}")
async def get_company_by_symbol(
    symbol: str,
    client: MCPClient = Depends(get_mcp_client)
):
    """Get company details by symbol via MCP"""
    try:
        result = await client.call_tool("company-data", "get_company_by_symbol", {
            "symbol": symbol.upper()
        })
        return result
    except Exception as e:
        logger.error(f"Failed to get company {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/sectors/list")
async def get_sectors(client: MCPClient = Depends(get_mcp_client)):
    """Get list of all sectors via MCP"""
    try:
        result = await client.call_tool("company-data", "get_sectors", {})
        return result
    except Exception as e:
        logger.error(f"Failed to get sectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Financial Data Endpoints (via MCP)
@router.get("/finance/stock/{symbol}")
async def get_stock_price(
    symbol: str,
    client: MCPClient = Depends(get_mcp_client)
):
    """Get stock price via MCP finance-data server"""
    try:
        result = await client.get_stock_price(symbol)
        return result
    except Exception as e:
        logger.error(f"Failed to get stock price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finance/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get historical market data via MCP"""
    try:
        result = await client.call_tool("finance-data", "get_market_data", {
            "symbol": symbol,
            "period": period
        })
        return result
    except Exception as e:
        logger.error(f"Failed to get market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finance/company-info/{symbol}")
async def get_company_info(
    symbol: str,
    client: MCPClient = Depends(get_mcp_client)
):
    """Get company information via MCP"""
    try:
        result = await client.call_tool("finance-data", "get_company_info", {
            "symbol": symbol
        })
        return result
    except Exception as e:
        logger.error(f"Failed to get company info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finance/market-indices")
async def get_market_indices(client: MCPClient = Depends(get_mcp_client)):
    """Get market indices via MCP"""
    try:
        result = await client.call_tool("finance-data", "get_market_indices", {})
        return result
    except Exception as e:
        logger.error(f"Failed to get market indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Earnings Endpoints (via MCP)
@router.get("/earnings/calendar")
async def get_earnings_calendar(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get earnings calendar via MCP"""
    try:
        result = await client.get_earnings_calendar(start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"Failed to get earnings calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/earnings/history/{symbol}")
async def get_earnings_history(
    symbol: str,
    quarters_back: int = Query(8, ge=1, le=20),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get earnings history for a company via MCP"""
    try:
        result = await client.call_tool("earnings-analysis", "get_company_earnings_history", {
            "symbol": symbol,
            "quarters_back": quarters_back
        })
        return result
    except Exception as e:
        logger.error(f"Failed to get earnings history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sentiment Analysis Endpoints (via MCP)
@router.post("/sentiment/analyze")
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    client: MCPClient = Depends(get_mcp_client)
):
    """Analyze sentiment via MCP sentiment server"""
    try:
        if request.context == "earnings":
            result = await client.call_tool("sentiment-analysis", "analyze_earnings_sentiment", {
                "earnings_text": request.text,
                "context": request.context
            })
        else:
            result = await client.analyze_sentiment(request.text)
        return result
    except Exception as e:
        logger.error(f"Failed to analyze sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sentiment/batch")
async def batch_sentiment_analysis(
    texts: List[str] = Body(...),
    labels: Optional[List[str]] = Body(None),
    client: MCPClient = Depends(get_mcp_client)
):
    """Batch sentiment analysis via MCP"""
    try:
        result = await client.call_tool("sentiment-analysis", "batch_sentiment_analysis", {
            "texts": texts,
            "labels": labels
        })
        return result
    except Exception as e:
        logger.error(f"Failed to perform batch sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Prediction Endpoints (via MCP)
@router.post("/predictions/next-day")
async def predict_next_day_performance(
    request: StockPredictionRequest,
    client: MCPClient = Depends(get_mcp_client)
):
    """Predict next-day stock performance via MCP"""
    try:
        result = await client.predict_stock_performance(
            request.symbol,
            request.earnings_data
        )
        return result
    except Exception as e:
        logger.error(f"Failed to predict performance for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/history/{symbol}")
async def get_prediction_history(
    symbol: str,
    days_back: int = Query(30, ge=1, le=365),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get prediction history for a company via MCP"""
    try:
        result = await client.call_tool("stock-predictions", "get_prediction_history", {
            "symbol": symbol,
            "days_back": days_back
        })
        return result
    except Exception as e:
        logger.error(f"Failed to get prediction history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/top")
async def get_top_predictions(
    confidence_threshold: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get top predictions via MCP"""
    try:
        result = await client.call_tool("stock-predictions", "get_top_predictions", {
            "confidence_threshold": confidence_threshold,
            "limit": limit
        })
        return result
    except Exception as e:
        logger.error(f"Failed to get top predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Comprehensive Analysis Endpoint
@router.post("/analysis/batch")
async def batch_analysis(
    request: BatchAnalysisRequest,
    client: MCPClient = Depends(get_mcp_client)
):
    """Perform comprehensive analysis for a stock symbol via MCP"""
    try:
        result = await client.batch_analysis(request.symbol)
        return result
    except Exception as e:
        logger.error(f"Failed to perform batch analysis for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time MCP updates (if needed)
@router.get("/mcp/stream")
async def mcp_stream():
    """WebSocket endpoint for real-time MCP data (placeholder)"""
    return {"message": "WebSocket streaming not implemented yet"}

# Health check that includes MCP status
@router.get("/mcp/health")
async def mcp_health_check(client: MCPClient = Depends(get_mcp_client)):
    """Health check that includes MCP server status"""
    try:
        status = client.get_server_status()
        
        total_servers = status.get("total_servers", 0)
        connected_servers = status.get("connected_servers", 0)
        
        health_status = "healthy" if connected_servers == total_servers else "degraded"
        
        return {
            "status": health_status,
            "mcp_servers": {
                "total": total_servers,
                "connected": connected_servers,
                "connection_rate": connected_servers / total_servers if total_servers > 0 else 0
            },
            "details": status
        }
    except Exception as e:
        logger.error(f"MCP health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }