from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from contextlib import asynccontextmanager

from app.api.endpoints import mcp_proxy
from app.mcp_client import get_mcp_client, shutdown_mcp_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MCP client
    await get_mcp_client()
    yield
    # Shutdown: Clean up MCP client
    await shutdown_mcp_client()

# Create FastAPI app with MCP integration
app = FastAPI(
    title="Calvin Stock Prediction API",
    description="AI-powered stock market prediction tool for S&P 500 earnings analysis with MCP servers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include MCP proxy router
app.include_router(mcp_proxy.router, prefix="/api/v1", tags=["MCP Services"])


@app.get("/")
async def root():
    return {"message": "Calvin Stock Prediction API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "calvin-api"}


@app.get("/api/v1/companies")
async def get_companies(limit: int = 5):
    """Get list of companies - minimal implementation for testing"""
    # Return mock data for now
    companies = [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
    ]
    return companies[:limit]


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )