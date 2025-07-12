#!/usr/bin/env python3
"""
Simple HTTP API to serve S&P 500 data from JSON file
This serves as an intermediary between the JSON file and the dashboard
"""

import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SP500API:
    def __init__(self):
        """Initialize Flask app and load S&P 500 data"""
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for dashboard
        
        # Data storage
        self.companies_data = {}
        self.sectors_data = {}
        self.last_update = None
        
        # Load data from JSON file
        self.load_sp500_data()
        
        # Setup Flask routes
        self.setup_routes()
    
    def load_sp500_data(self):
        """Load S&P 500 data from JSON file"""
        try:
            with open('sp500_companies.json', 'r', encoding='utf-8') as f:
                companies_list = json.load(f)
            
            # Convert to dictionary for faster lookups
            for company in companies_list:
                symbol = company.get('symbol')
                if symbol:
                    self.companies_data[symbol] = company
            
            # Calculate sector statistics
            sectors = {}
            for company in companies_list:
                sector = company.get('gics_sector', 'Unknown')
                if sector not in sectors:
                    sectors[sector] = {
                        'sector_name': sector,
                        'company_count': 0,
                        'companies': []
                    }
                sectors[sector]['company_count'] += 1
                sectors[sector]['companies'].append({
                    'symbol': company.get('symbol'),
                    'company_name': company.get('company_name')
                })
            
            self.sectors_data = sectors
            self.last_update = datetime.now().isoformat()
            
            logger.info(f"📊 Loaded {len(self.companies_data)} S&P 500 companies")
            logger.info(f"🏭 Processed {len(self.sectors_data)} sectors")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load S&P 500 data: {e}")
            return False
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'companies_loaded': len(self.companies_data),
                'sectors_loaded': len(self.sectors_data),
                'last_update': self.last_update,
                'source': 'json_file'
            })
        
        @self.app.route('/api/companies', methods=['GET'])
        def get_companies():
            """Get all S&P 500 companies"""
            # Optional filtering
            sector = request.args.get('sector')
            limit = request.args.get('limit', type=int)
            
            companies = list(self.companies_data.values())
            
            # Filter by sector if specified
            if sector:
                companies = [c for c in companies if c.get('gics_sector', '').lower() == sector.lower()]
            
            # Limit results if specified
            if limit:
                companies = companies[:limit]
            
            return jsonify({
                'companies': companies,
                'total_count': len(companies),
                'last_update': self.last_update,
                'source': 'json_file'
            })
        
        @self.app.route('/api/companies/<symbol>', methods=['GET'])
        def get_company(symbol):
            """Get specific company by symbol"""
            symbol = symbol.upper()
            
            if symbol in self.companies_data:
                return jsonify({
                    'company': self.companies_data[symbol],
                    'last_update': self.last_update
                })
            else:
                return jsonify({'error': 'Company not found'}), 404
        
        @self.app.route('/api/sectors', methods=['GET'])
        def get_sectors():
            """Get sector summary data"""
            return jsonify({
                'sectors': list(self.sectors_data.values()),
                'total_sectors': len(self.sectors_data),
                'last_update': self.last_update
            })
        
        @self.app.route('/api/sectors/<sector_name>', methods=['GET'])
        def get_sector(sector_name):
            """Get specific sector data"""
            if sector_name in self.sectors_data:
                return jsonify({
                    'sector': self.sectors_data[sector_name],
                    'last_update': self.last_update
                })
            else:
                return jsonify({'error': 'Sector not found'}), 404
        
        @self.app.route('/api/symbols', methods=['GET'])
        def get_symbols():
            """Get just the list of symbols (for quick access)"""
            symbols = list(self.companies_data.keys())
            return jsonify({
                'symbols': sorted(symbols),
                'count': len(symbols),
                'last_update': self.last_update
            })
        
        @self.app.route('/api/search', methods=['GET'])
        def search_companies():
            """Search companies by name or symbol"""
            query = request.args.get('q', '').lower()
            
            if not query:
                return jsonify({'error': 'Query parameter "q" is required'}), 400
            
            matches = []
            for company in self.companies_data.values():
                if (query in company.get('symbol', '').lower() or 
                    query in company.get('company_name', '').lower()):
                    matches.append(company)
            
            return jsonify({
                'matches': matches,
                'query': query,
                'count': len(matches)
            })
        
        @self.app.route('/api/refresh', methods=['POST'])
        def refresh_data():
            """Refresh data from JSON file"""
            if self.load_sp500_data():
                return jsonify({
                    'status': 'success',
                    'message': 'Data refreshed successfully',
                    'companies_loaded': len(self.companies_data),
                    'last_update': self.last_update
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to refresh data'
                }), 500
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the Flask API server"""
        logger.info(f"🚀 Starting S&P 500 API server on {host}:{port}")
        logger.info(f"📡 API endpoints available:")
        logger.info(f"  GET  /api/health         - Health check")
        logger.info(f"  GET  /api/companies      - All companies (supports ?sector=X&limit=Y)")
        logger.info(f"  GET  /api/companies/<symbol> - Specific company")
        logger.info(f"  GET  /api/sectors        - All sectors")
        logger.info(f"  GET  /api/symbols        - Just symbol list")
        logger.info(f"  GET  /api/search?q=X     - Search companies")
        logger.info(f"  POST /api/refresh        - Refresh data from JSON")
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main function"""
    api_service = SP500API()
    
    try:
        api_service.run(port=5001, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down API service...")


if __name__ == "__main__":
    main()