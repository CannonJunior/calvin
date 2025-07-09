#!/usr/bin/env python3
"""
Standalone test server - run this manually to test if FastAPI works
Usage: python3 test_server.py
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="Calvin Test Server")
    
    @app.get("/")
    async def root():
        return {"message": "Test server working", "status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "test-server"}
    
    @app.get("/api/v1/companies")
    async def companies(limit: int = 5):
        test_data = [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
        ]
        return test_data[:limit]
    
    if __name__ == "__main__":
        print("Starting test server on http://localhost:8000")
        print("Test endpoints:")
        print("  http://localhost:8000/")
        print("  http://localhost:8000/health")
        print("  http://localhost:8000/api/v1/companies?limit=5")
        print("\nPress Ctrl+C to stop")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install fastapi uvicorn")
except Exception as e:
    print(f"Error starting server: {e}")