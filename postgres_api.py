#!/usr/bin/env python3
"""
PostgreSQL API Service for Earnings Data
Serves real earnings data from PostgreSQL database to the dashboard
"""

import json
import logging
from datetime import datetime, date
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgresEarningsAPI:
    def __init__(self):
        """Initialize PostgreSQL API service"""
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for dashboard
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'calvin_earnings',
            'user': 'calvin_user',
            'password': 'calvin_pass'
        }
        
        # Setup Flask routes
        self.setup_routes()
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'status': 'unhealthy', 'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM companies")
                companies_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM earnings")
                earnings_count = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'companies_count': companies_count,
                    'earnings_count': earnings_count,
                    'source': 'postgresql'
                })
            except Exception as e:
                return jsonify({'status': 'error', 'error': str(e)}), 500
        
        @self.app.route('/api/companies', methods=['GET'])
        def get_companies():
            """Get all companies from database"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Optional filtering
                sector = request.args.get('sector')
                limit = request.args.get('limit', type=int)
                
                query = "SELECT * FROM companies"
                params = []
                
                if sector:
                    query += " WHERE gics_sector ILIKE %s"
                    params.append(f"%{sector}%")
                
                query += " ORDER BY symbol"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, params)
                companies = [dict(row) for row in cursor.fetchall()]
                
                # Convert dates to ISO format
                for company in companies:
                    if company.get('date_added'):
                        company['date_added'] = company['date_added'].isoformat()
                    if company.get('created_at'):
                        company['created_at'] = company['created_at'].isoformat()
                    if company.get('updated_at'):
                        company['updated_at'] = company['updated_at'].isoformat()
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'companies': companies,
                    'total_count': len(companies),
                    'source': 'postgresql'
                })
                
            except Exception as e:
                logger.error(f"Error fetching companies: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/earnings', methods=['GET'])
        def get_earnings():
            """Get earnings data from database"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Optional filtering
                symbol = request.args.get('symbol')
                earnings_type = request.args.get('type')  # 'past', 'future'
                limit = request.args.get('limit', type=int, default=1000)
                
                # Use the earnings calendar view for easy querying
                query = """
                    SELECT 
                        id, symbol, company_name, gics_sector,
                        earnings_date, quarter, year,
                        estimated_eps, actual_eps,
                        beat_miss_meet, surprise_percent, confidence_score,
                        consensus_rating, announcement_time,
                        earnings_type_timeline, days_from_today
                    FROM earnings_calendar
                    WHERE 1=1
                """
                params = []
                
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol.upper())
                
                if earnings_type == 'past':
                    query += " AND earnings_type_timeline = 'past'"
                elif earnings_type == 'future':
                    query += " AND earnings_type_timeline = 'future'"
                
                query += " ORDER BY earnings_date DESC"
                query += f" LIMIT {limit}"
                
                cursor.execute(query, params)
                earnings = [dict(row) for row in cursor.fetchall()]
                
                # Convert dates to ISO format
                for earning in earnings:
                    if earning.get('earnings_date'):
                        earning['earnings_date'] = earning['earnings_date'].isoformat()
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'earnings': earnings,
                    'total_count': len(earnings),
                    'source': 'postgresql'
                })
                
            except Exception as e:
                logger.error(f"Error fetching earnings: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/earnings/timeline', methods=['GET'])
        def get_earnings_timeline():
            """Get earnings data specifically formatted for timeline visualization"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get earnings data with additional fields for timeline
                query = """
                    SELECT 
                        e.id,
                        e.symbol,
                        c.company_name,
                        c.gics_sector,
                        e.earnings_date,
                        e.quarter,
                        e.year,
                        e.estimated_eps,
                        e.actual_eps,
                        e.beat_miss_meet,
                        e.surprise_percent,
                        e.confidence_score,
                        e.consensus_rating,
                        e.announcement_time,
                        e.price_change_percent,
                        e.volume,
                        CASE 
                            WHEN e.earnings_date < CURRENT_DATE THEN 'past'
                            ELSE 'future'
                        END as type,
                        CASE 
                            WHEN e.earnings_date < CURRENT_DATE THEN e.surprise_percent
                            ELSE (
                                CASE e.beat_miss_meet
                                    WHEN 'BEAT' THEN 5
                                    WHEN 'MISS' THEN -5
                                    ELSE 0
                                END
                            )
                        END as timeline_y_value
                    FROM earnings e
                    JOIN companies c ON e.company_id = c.id
                    ORDER BY e.earnings_date
                """
                
                cursor.execute(query)
                earnings = [dict(row) for row in cursor.fetchall()]
                
                # Format data for timeline
                timeline_data = []
                for earning in earnings:
                    # Calculate realistic market cap based on sector and company
                    sector_market_caps = {
                        'Information Technology': {'min': 50, 'max': 3000},
                        'Health Care': {'min': 30, 'max': 500},
                        'Financials': {'min': 20, 'max': 600},
                        'Consumer Discretionary': {'min': 15, 'max': 1200},
                        'Communication Services': {'min': 25, 'max': 1800},
                        'Industrials': {'min': 10, 'max': 400},
                        'Consumer Staples': {'min': 20, 'max': 300},
                        'Energy': {'min': 5, 'max': 500},
                        'Utilities': {'min': 15, 'max': 150},
                        'Real Estate': {'min': 5, 'max': 100},
                        'Materials': {'min': 8, 'max': 200}
                    }
                    
                    sector = earning.get('gics_sector', 'Information Technology')
                    sector_caps = sector_market_caps.get(sector, {'min': 20, 'max': 500})
                    
                    # Use symbol hash for consistent market cap per company
                    symbol_hash = hash(earning['symbol']) % 1000
                    market_cap_range = sector_caps['max'] - sector_caps['min']
                    market_cap = sector_caps['min'] + (symbol_hash / 1000) * market_cap_range
                    
                    timeline_item = {
                        'id': earning['id'],
                        'symbol': earning['symbol'],
                        'company_name': earning['company_name'],
                        'date': earning['earnings_date'].isoformat() if earning['earnings_date'] else None,
                        'type': earning['type'],
                        'sector': earning['gics_sector'],
                        
                        # Timeline-specific fields
                        'priceChange': earning.get('price_change_percent', 0),
                        'predictionAccuracy': earning.get('confidence_score', 0.5),
                        'marketCap': round(market_cap, 1),  # Realistic market cap based on sector
                        'volume': earning.get('volume', 50000000),
                        
                        # Earnings data
                        'actualEPS': earning.get('actual_eps'),
                        'expectedEPS': earning.get('estimated_eps'),
                        'beat_miss_meet': earning.get('beat_miss_meet'),
                        'surprise_percent': earning.get('surprise_percent'),
                        
                        # Future earnings
                        'analystExpectation': earning.get('beat_miss_meet', '').lower() if earning['type'] == 'future' and earning.get('beat_miss_meet') else None,
                        'confidence': earning.get('confidence_score', 0.5),
                        'consensusRating': earning.get('consensus_rating'),
                        'announcement_time': earning.get('announcement_time')
                    }
                    timeline_data.append(timeline_item)
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'timeline_data': timeline_data,
                    'total_count': len(timeline_data),
                    'source': 'postgresql'
                })
                
            except Exception as e:
                logger.error(f"Error fetching timeline data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/earnings/company/<symbol>', methods=['GET'])
        def get_company_earnings(symbol):
            """Get earnings data for a specific company"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                query = """
                    SELECT 
                        e.*,
                        c.company_name,
                        c.gics_sector
                    FROM earnings e
                    JOIN companies c ON e.company_id = c.id
                    WHERE e.symbol = %s
                    ORDER BY e.earnings_date DESC
                """
                
                cursor.execute(query, (symbol.upper(),))
                earnings = [dict(row) for row in cursor.fetchall()]
                
                # Convert dates to ISO format
                for earning in earnings:
                    if earning.get('earnings_date'):
                        earning['earnings_date'] = earning['earnings_date'].isoformat()
                    if earning.get('created_at'):
                        earning['created_at'] = earning['created_at'].isoformat()
                    if earning.get('updated_at'):
                        earning['updated_at'] = earning['updated_at'].isoformat()
                
                cursor.close()
                conn.close()
                
                if not earnings:
                    return jsonify({'error': 'Company earnings not found'}), 404
                
                return jsonify({
                    'symbol': symbol.upper(),
                    'company_name': earnings[0]['company_name'],
                    'earnings': earnings,
                    'total_count': len(earnings)
                })
                
            except Exception as e:
                logger.error(f"Error fetching company earnings: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/sectors', methods=['GET'])
        def get_sectors():
            """Get sector summary data"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                query = """
                    SELECT 
                        gics_sector as sector_name,
                        COUNT(*) as company_count,
                        ARRAY_AGG(
                            JSON_BUILD_OBJECT(
                                'symbol', symbol,
                                'company_name', company_name
                            )
                        ) as companies
                    FROM companies
                    WHERE gics_sector IS NOT NULL
                    GROUP BY gics_sector
                    ORDER BY company_count DESC
                """
                
                cursor.execute(query)
                sectors = [dict(row) for row in cursor.fetchall()]
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'sectors': sectors,
                    'total_sectors': len(sectors),
                    'source': 'postgresql'
                })
                
            except Exception as e:
                logger.error(f"Error fetching sectors: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/symbols', methods=['GET'])
        def get_symbols():
            """Get list of all symbols"""
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                cursor.execute("SELECT symbol FROM companies ORDER BY symbol")
                symbols = [row[0] for row in cursor.fetchall()]
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'symbols': symbols,
                    'count': len(symbols),
                    'source': 'postgresql'
                })
                
            except Exception as e:
                logger.error(f"Error fetching symbols: {e}")
                return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=5002, debug=False):
        """Run the Flask API server"""
        logger.info(f"🚀 Starting PostgreSQL Earnings API server on {host}:{port}")
        logger.info(f"📡 API endpoints available:")
        logger.info(f"  GET  /api/health                   - Health check")
        logger.info(f"  GET  /api/companies                - All companies")
        logger.info(f"  GET  /api/earnings                 - All earnings data")
        logger.info(f"  GET  /api/earnings/timeline        - Timeline formatted data")
        logger.info(f"  GET  /api/earnings/company/<symbol> - Company specific earnings")
        logger.info(f"  GET  /api/sectors                  - Sector summary")
        logger.info(f"  GET  /api/symbols                  - Symbol list")
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main function"""
    api_service = PostgresEarningsAPI()
    
    try:
        api_service.run(port=5002, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down PostgreSQL API service...")


if __name__ == "__main__":
    main()