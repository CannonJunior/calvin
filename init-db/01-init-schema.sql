-- Calvin Earnings Database Schema
-- Initialize database with tables for real earnings data

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create companies table (from S&P 500 data)
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    gics_sector VARCHAR(100),
    gics_sub_industry VARCHAR(100),
    headquarters VARCHAR(255),
    date_added DATE,
    cik VARCHAR(20),
    founded VARCHAR(20),
    market_cap BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create earnings table for historical and future earnings
CREATE TABLE earnings (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    earnings_date DATE NOT NULL,
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4)),
    year INTEGER NOT NULL,
    
    -- Actual earnings data (for past earnings)
    actual_eps DECIMAL(10, 4),
    actual_revenue BIGINT,
    
    -- Estimated/expected data
    estimated_eps DECIMAL(10, 4),
    estimated_revenue BIGINT,
    
    -- Analyst consensus
    consensus_rating VARCHAR(20), -- Buy, Hold, Sell
    num_analysts INTEGER,
    
    -- Performance metrics
    price_change_percent DECIMAL(8, 4), -- Price change after earnings
    volume BIGINT,
    
    -- Prediction/confidence metrics
    beat_miss_meet VARCHAR(10), -- BEAT, MISS, MEET
    surprise_percent DECIMAL(8, 4), -- (actual - estimated) / estimated * 100
    confidence_score DECIMAL(3, 2), -- 0.00 to 1.00
    
    -- Metadata
    earnings_type VARCHAR(10) DEFAULT 'quarterly', -- quarterly, annual
    is_guidance BOOLEAN DEFAULT FALSE,
    announcement_time VARCHAR(10), -- BMO (before market open), AMC (after market close)
    
    -- Vector embedding for similarity analysis
    earnings_embedding vector(384), -- 384-dimensional vector for embeddings
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, earnings_date, quarter, year)
);

-- Create market data table for real-time stock data
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    
    -- Current market data
    current_price DECIMAL(10, 4),
    previous_close DECIMAL(10, 4),
    day_change DECIMAL(10, 4),
    day_change_percent DECIMAL(8, 4),
    day_high DECIMAL(10, 4),
    day_low DECIMAL(10, 4),
    volume BIGINT,
    
    -- Extended data
    market_cap BIGINT,
    pe_ratio DECIMAL(8, 4),
    dividend_yield DECIMAL(6, 4),
    
    -- 52-week data
    week_52_high DECIMAL(10, 4),
    week_52_low DECIMAL(10, 4),
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'API'
);

-- Create sectors performance table
CREATE TABLE sector_performance (
    id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL,
    performance_date DATE DEFAULT CURRENT_DATE,
    
    -- Performance metrics
    avg_change_percent DECIMAL(8, 4),
    total_companies INTEGER,
    positive_companies INTEGER,
    negative_companies INTEGER,
    
    -- Volume metrics
    total_volume BIGINT,
    avg_volume BIGINT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sector_name, performance_date)
);

-- Create earnings calendar view for easy querying
CREATE VIEW earnings_calendar AS
SELECT 
    e.id,
    c.symbol,
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
    CASE 
        WHEN e.earnings_date < CURRENT_DATE THEN 'past'
        ELSE 'future'
    END as earnings_type_timeline,
    ABS(EXTRACT(DAYS FROM (e.earnings_date - CURRENT_DATE))) as days_from_today
FROM earnings e
JOIN companies c ON e.company_id = c.id
ORDER BY e.earnings_date;

-- Create indexes for performance
CREATE INDEX idx_earnings_symbol_date ON earnings(symbol, earnings_date);
CREATE INDEX idx_earnings_date ON earnings(earnings_date);
CREATE INDEX idx_earnings_quarter_year ON earnings(quarter, year);
CREATE INDEX idx_companies_symbol ON companies(symbol);
CREATE INDEX idx_companies_sector ON companies(gics_sector);
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_sector_performance_date ON sector_performance(performance_date);

-- Create index for vector similarity search (will be created after data insertion)
-- CREATE INDEX ON earnings USING ivfflat (earnings_embedding vector_cosine_ops);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON companies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_earnings_updated_at 
    BEFORE UPDATE ON earnings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial notification
INSERT INTO companies (symbol, company_name, gics_sector) 
VALUES ('INFO', 'Database Initialized', 'System') 
ON CONFLICT (symbol) DO NOTHING;