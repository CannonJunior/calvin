#!/usr/bin/env python3
"""
Kafka Consumer API Service
Consumes S&P 500 data from Kafka and provides HTTP endpoints for the dashboard
"""

import json
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
from collections import defaultdict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SP500KafkaConsumerAPI:
    def __init__(self, bootstrap_servers='localhost:9092'):
        """Initialize Kafka consumer and Flask app"""
        self.bootstrap_servers = bootstrap_servers
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for dashboard
        
        # Data storage
        self.companies_data = {}
        self.sectors_data = {}
        self.last_update = None
        self.consumer_threads = []
        
        # Kafka topics
        self.topics = ['sp500-companies', 'sp500-sectors', 'sp500-updates']
        
        # Setup Flask routes
        self.setup_routes()
        
        # Start Kafka consumers
        self.start_consumers()
    
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
                'last_update': self.last_update
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
                'source': 'kafka_stream'
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
    
    def start_consumers(self):
        """Start Kafka consumer threads"""
        try:
            # Companies consumer
            companies_thread = threading.Thread(
                target=self.consume_companies,
                daemon=True
            )
            companies_thread.start()
            self.consumer_threads.append(companies_thread)
            
            # Sectors consumer  
            sectors_thread = threading.Thread(
                target=self.consume_sectors,
                daemon=True
            )
            sectors_thread.start()
            self.consumer_threads.append(sectors_thread)
            
            # Updates consumer
            updates_thread = threading.Thread(
                target=self.consume_updates,
                daemon=True
            )
            updates_thread.start()
            self.consumer_threads.append(updates_thread)
            
            logger.info("✅ Started Kafka consumer threads")
            
        except Exception as e:
            logger.error(f"❌ Failed to start consumers: {e}")
    
    def consume_companies(self):
        """Consume company data from Kafka"""
        try:
            consumer = KafkaConsumer(
                'sp500-companies',
                bootstrap_servers=self.bootstrap_servers,
                group_id='sp500-dashboard-companies',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            
            logger.info("📊 Started consuming company data...")
            
            for message in consumer:
                try:
                    company_data = message.value
                    symbol = company_data.get('symbol')
                    
                    if symbol:
                        self.companies_data[symbol] = company_data
                        logger.debug(f"Updated company data for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error processing company message: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Company consumer error: {e}")
    
    def consume_sectors(self):
        """Consume sector data from Kafka"""
        try:
            consumer = KafkaConsumer(
                'sp500-sectors',
                bootstrap_servers=self.bootstrap_servers,
                group_id='sp500-dashboard-sectors',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            
            logger.info("🏭 Started consuming sector data...")
            
            for message in consumer:
                try:
                    sector_data = message.value
                    sector_name = sector_data.get('sector_name')
                    
                    if sector_name:
                        self.sectors_data[sector_name] = sector_data
                        logger.debug(f"Updated sector data for {sector_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing sector message: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Sector consumer error: {e}")
    
    def consume_updates(self):
        """Consume update notifications from Kafka"""
        try:
            consumer = KafkaConsumer(
                'sp500-updates',
                bootstrap_servers=self.bootstrap_servers,
                group_id='sp500-dashboard-updates',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',  # Only get new updates
                enable_auto_commit=True
            )
            
            logger.info("📢 Started consuming update notifications...")
            
            for message in consumer:
                try:
                    update_data = message.value
                    self.last_update = update_data.get('timestamp')
                    logger.info(f"📅 Data update notification: {update_data.get('status')}")
                    
                except Exception as e:
                    logger.error(f"Error processing update message: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Updates consumer error: {e}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask API server"""
        logger.info(f"🚀 Starting S&P 500 API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main function"""
    # Create and start the consumer API service
    api_service = SP500KafkaConsumerAPI()
    
    # Give consumers a moment to start
    time.sleep(2)
    
    # Start the Flask API server
    try:
        api_service.run(port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down API service...")


if __name__ == "__main__":
    main()