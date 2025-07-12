#!/usr/bin/env python3
"""
Minimal HTTP server using only Python standard library
No external dependencies - should always work
"""
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

class CalvinHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if path == '/health':
            response = {"status": "healthy", "service": "calvin-minimal"}
        elif path == '/api/v1/companies':
            limit = int(params.get('limit', [5])[0])
            companies = [
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
            ]
            response = companies[:limit]
        elif path == '/':
            response = {"message": "Calvin Stock Prediction API", "version": "0.1.0", "status": "running"}
        else:
            response = {"error": "Not found", "path": path}
        
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == "__main__":
    PORT = 8080  # Use different port to avoid conflicts
    
    print(f"Starting Calvin API server on port {PORT}")
    print("Endpoints:")
    print(f"  http://localhost:{PORT}/")
    print(f"  http://localhost:{PORT}/health")
    print(f"  http://localhost:{PORT}/api/v1/companies?limit=5")
    
    with socketserver.TCPServer(("", PORT), CalvinHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")