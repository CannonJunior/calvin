#!/usr/bin/env python3
"""
Kafka Producer Service for S&P 500 Company Data
Reads sp500_companies.json and streams data to Kafka topics
"""

import json
import time
import logging
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import schedule
import threading


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SP500KafkaProducer:
    def __init__(self, bootstrap_servers='localhost:9092'):
        """Initialize Kafka producer"""
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.sp500_data = []
        self.topic_companies = 'sp500-companies'
        self.topic_sectors = 'sp500-sectors'
        self.topic_updates = 'sp500-updates'
        
        self.connect_to_kafka()
        self.load_sp500_data()
    
    def connect_to_kafka(self):
        """Connect to Kafka cluster"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=5,
                retry_backoff_ms=1000,
                max_in_flight_requests_per_connection=1,
                acks='all'
            )
            logger.info(f"✅ Connected to Kafka at {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            return False
    
    def load_sp500_data(self):
        """Load S&P 500 data from JSON file"""
        try:
            with open('sp500_companies.json', 'r', encoding='utf-8') as f:
                self.sp500_data = json.load(f)
            logger.info(f"📊 Loaded {len(self.sp500_data)} S&P 500 companies")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load S&P 500 data: {e}")
            return False
    
    def send_all_companies(self):
        """Send all company data to Kafka topic"""
        if not self.producer or not self.sp500_data:
            logger.error("Producer not ready or no data loaded")
            return False
        
        try:
            logger.info("🚀 Streaming all S&P 500 companies to Kafka...")
            
            for i, company in enumerate(self.sp500_data):
                # Add streaming metadata
                message = {
                    **company,
                    'stream_timestamp': datetime.now().isoformat(),
                    'sequence_number': i + 1,
                    'total_count': len(self.sp500_data),
                    'message_type': 'company_data'
                }
                
                # Send to companies topic
                future = self.producer.send(
                    self.topic_companies,
                    key=company['symbol'],
                    value=message
                )
                
                # Optional: Add callback for delivery confirmation
                future.add_callback(self.on_send_success)
                future.add_errback(self.on_send_error)
                
                # Small delay to avoid overwhelming consumers
                time.sleep(0.01)
            
            # Flush to ensure all messages are sent
            self.producer.flush()
            logger.info(f"✅ Successfully streamed {len(self.sp500_data)} companies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error streaming companies: {e}")
            return False
    
    def send_sector_summary(self):
        """Send sector summary data"""
        if not self.sp500_data:
            return False
        
        try:
            # Calculate sector statistics
            sectors = {}
            for company in self.sp500_data:
                sector = company['gics_sector']
                if sector not in sectors:
                    sectors[sector] = {
                        'sector_name': sector,
                        'company_count': 0,
                        'companies': []
                    }
                sectors[sector]['company_count'] += 1
                sectors[sector]['companies'].append({
                    'symbol': company['symbol'],
                    'company_name': company['company_name']
                })
            
            # Send sector summaries
            for sector_name, sector_data in sectors.items():
                message = {
                    **sector_data,
                    'stream_timestamp': datetime.now().isoformat(),
                    'message_type': 'sector_summary'
                }
                
                future = self.producer.send(
                    self.topic_sectors,
                    key=sector_name,
                    value=message
                )
                future.add_callback(self.on_send_success)
                future.add_errback(self.on_send_error)
            
            self.producer.flush()
            logger.info(f"✅ Sent sector summary for {len(sectors)} sectors")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending sector summary: {e}")
            return False
    
    def send_update_notification(self):
        """Send update notification"""
        try:
            message = {
                'message_type': 'update_notification',
                'timestamp': datetime.now().isoformat(),
                'total_companies': len(self.sp500_data),
                'status': 'data_refreshed',
                'source': 'wikipedia'
            }
            
            future = self.producer.send(
                self.topic_updates,
                key='update',
                value=message
            )
            future.add_callback(self.on_send_success)
            future.add_errback(self.on_send_error)
            
            self.producer.flush()
            logger.info("📢 Sent update notification")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending update notification: {e}")
            return False
    
    def on_send_success(self, record_metadata):
        """Callback for successful message delivery"""
        logger.debug(f"Message delivered to {record_metadata.topic} [{record_metadata.partition}] at offset {record_metadata.offset}")
    
    def on_send_error(self, excp):
        """Callback for failed message delivery"""
        logger.error(f"Message delivery failed: {excp}")
    
    def stream_complete_dataset(self):
        """Stream complete dataset (companies + sectors + notification)"""
        logger.info("🔄 Starting complete S&P 500 data stream...")
        
        success = True
        success &= self.send_update_notification()
        success &= self.send_all_companies()
        success &= self.send_sector_summary()
        
        if success:
            logger.info("✅ Complete dataset streaming finished successfully!")
        else:
            logger.error("❌ Some errors occurred during streaming")
        
        return success
    
    def schedule_periodic_updates(self):
        """Schedule periodic data updates"""
        # Stream immediately on startup
        self.stream_complete_dataset()
        
        # Schedule regular updates
        schedule.every(1).hours.do(self.stream_complete_dataset)
        schedule.every().day.at("09:00").do(self.refresh_and_stream)  # Market open
        schedule.every().day.at("16:00").do(self.refresh_and_stream)  # Market close
        
        logger.info("📅 Scheduled periodic updates (hourly, 9 AM, 4 PM)")
    
    def refresh_and_stream(self):
        """Refresh data from source and stream"""
        logger.info("🔄 Refreshing S&P 500 data from Wikipedia...")
        
        # Re-fetch data (you could call the fetch script here)
        # For now, just reload from file
        if self.load_sp500_data():
            self.stream_complete_dataset()
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_streaming_service(self):
        """Start the streaming service"""
        logger.info("🚀 Starting S&P 500 Kafka Streaming Service...")
        
        # Schedule periodic updates
        self.schedule_periodic_updates()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("✅ Streaming service started! Press Ctrl+C to stop.")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down streaming service...")
            if self.producer:
                self.producer.close()
            logger.info("👋 Service stopped.")


def main():
    """Main function"""
    producer_service = SP500KafkaProducer()
    
    # Option 1: Stream once and exit
    if "--once" in __import__('sys').argv:
        producer_service.stream_complete_dataset()
        producer_service.producer.close()
        return
    
    # Option 2: Run as continuous service
    producer_service.start_streaming_service()


if __name__ == "__main__":
    main()