-- Initialize PostgreSQL database with pgvector extension
-- This script runs when the database container starts for the first time

-- Create the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main database user (if not exists)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'calvin_user') THEN

      CREATE ROLE calvin_user LOGIN PASSWORD 'calvin_password';
   END IF;
END
$do$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE stockprediction TO calvin_user;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);
CREATE INDEX IF NOT EXISTS idx_companies_sp500 ON companies(sp500_constituent);

CREATE INDEX IF NOT EXISTS idx_earnings_symbol ON earnings_events(company_symbol);
CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings_events(earnings_date);
CREATE INDEX IF NOT EXISTS idx_earnings_quarter_year ON earnings_events(quarter, year);

CREATE INDEX IF NOT EXISTS idx_analyst_ratings_symbol ON analyst_ratings(company_symbol);
CREATE INDEX IF NOT EXISTS idx_analyst_ratings_date ON analyst_ratings(rating_date);

CREATE INDEX IF NOT EXISTS idx_insider_trading_symbol ON insider_trading(company_symbol);
CREATE INDEX IF NOT EXISTS idx_insider_trading_date ON insider_trading(transaction_date);

CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(company_symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_target_date ON predictions(target_date);
CREATE INDEX IF NOT EXISTS idx_predictions_confidence ON predictions(confidence_score);

-- Vector indexes for embeddings (pgvector)
CREATE INDEX IF NOT EXISTS idx_earnings_embeddings_symbol ON earnings_embeddings(company_symbol);
CREATE INDEX IF NOT EXISTS idx_earnings_embeddings_date ON earnings_embeddings(earnings_date);

CREATE INDEX IF NOT EXISTS idx_news_embeddings_symbol ON news_embeddings(company_symbol);
CREATE INDEX IF NOT EXISTS idx_news_embeddings_date ON news_embeddings(published_date);

CREATE INDEX IF NOT EXISTS idx_analyst_report_embeddings_symbol ON analyst_report_embeddings(company_symbol);
CREATE INDEX IF NOT EXISTS idx_analyst_report_embeddings_date ON analyst_report_embeddings(report_date);

-- Vector similarity search indexes (HNSW for better performance)
-- These will be created after the tables are populated with embeddings
-- CREATE INDEX CONCURRENTLY earnings_embeddings_call_embedding_idx ON earnings_embeddings 
-- USING hnsw (call_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- CREATE INDEX CONCURRENTLY earnings_embeddings_combined_embedding_idx ON earnings_embeddings 
-- USING hnsw (combined_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- CREATE INDEX CONCURRENTLY news_embeddings_content_embedding_idx ON news_embeddings 
-- USING hnsw (content_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- CREATE INDEX CONCURRENTLY analyst_report_embeddings_content_embedding_idx ON analyst_report_embeddings 
-- USING hnsw (content_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Insert some sample S&P 500 companies for testing
INSERT INTO companies (symbol, name, sector, industry, sp500_constituent, market_cap) VALUES
('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics', true, 3000000),
('MSFT', 'Microsoft Corporation', 'Technology', 'Software', true, 2800000),
('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 'E-commerce', true, 1500000),
('GOOGL', 'Alphabet Inc.', 'Communication Services', 'Internet Services', true, 1700000),
('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'Electric Vehicles', true, 800000),
('META', 'Meta Platforms Inc.', 'Communication Services', 'Social Media', true, 750000),
('NVDA', 'NVIDIA Corporation', 'Technology', 'Semiconductors', true, 1800000),
('JPM', 'JPMorgan Chase & Co.', 'Financials', 'Banking', true, 450000),
('JNJ', 'Johnson & Johnson', 'Health Care', 'Pharmaceuticals', true, 420000),
('V', 'Visa Inc.', 'Financials', 'Payment Systems', true, 480000)
ON CONFLICT (symbol) DO NOTHING;

-- Insert sample earnings events for testing
INSERT INTO earnings_events (company_symbol, earnings_date, quarter, year, expected_eps, actual_eps, surprise_percentage) VALUES
('AAPL', '2024-01-25 16:30:00', 'Q1', 2024, 2.10, 2.18, 3.8),
('AAPL', '2023-10-26 16:30:00', 'Q4', 2023, 1.39, 1.46, 5.0),
('MSFT', '2024-01-24 16:30:00', 'Q2', 2024, 2.78, 2.93, 5.4),
('MSFT', '2023-10-24 16:30:00', 'Q1', 2024, 2.65, 3.05, 15.1),
('AMZN', '2024-02-01 16:30:00', 'Q4', 2023, 0.80, 1.00, 25.0),
('GOOGL', '2024-01-30 16:30:00', 'Q4', 2023, 1.34, 1.64, 22.4),
('TSLA', '2024-01-24 16:30:00', 'Q4', 2023, 0.73, 0.71, -2.7),
('NVDA', '2024-02-21 16:30:00', 'Q4', 2024, 4.56, 5.16, 13.2)
ON CONFLICT DO NOTHING;

-- Insert sample analyst ratings
INSERT INTO analyst_ratings (company_symbol, analyst_firm, rating, target_price, current_price, rating_date) VALUES
('AAPL', 'Morgan Stanley', 'Buy', 220.00, 190.00, '2024-01-15'),
('AAPL', 'Goldman Sachs', 'Hold', 200.00, 190.00, '2024-01-10'),
('MSFT', 'JP Morgan', 'Buy', 450.00, 420.00, '2024-01-12'),
('MSFT', 'Bank of America', 'Buy', 480.00, 420.00, '2024-01-08'),
('AMZN', 'Wells Fargo', 'Buy', 180.00, 155.00, '2024-01-20'),
('GOOGL', 'Citi', 'Buy', 165.00, 140.00, '2024-01-18'),
('TSLA', 'Deutsche Bank', 'Hold', 200.00, 185.00, '2024-01-22'),
('NVDA', 'Jefferies', 'Buy', 850.00, 750.00, '2024-02-15')
ON CONFLICT DO NOTHING;

-- Create a function for vector similarity search
CREATE OR REPLACE FUNCTION find_similar_earnings(
    target_embedding vector(1536),
    similarity_threshold float DEFAULT 0.8,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    company_symbol text,
    earnings_date timestamp,
    similarity_score float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.company_symbol::text,
        e.earnings_date,
        1 - (e.combined_embedding <=> target_embedding) as similarity_score
    FROM earnings_embeddings e
    WHERE e.combined_embedding IS NOT NULL
        AND 1 - (e.combined_embedding <=> target_embedding) >= similarity_threshold
    ORDER BY e.combined_embedding <=> target_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Create a function for earnings performance analysis
CREATE OR REPLACE FUNCTION get_earnings_performance_stats(company_sym text)
RETURNS TABLE (
    total_earnings int,
    beat_count int,
    miss_count int,
    meet_count int,
    beat_rate float,
    avg_surprise float,
    avg_return_1d float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::int as total_earnings,
        COUNT(CASE WHEN surprise_percentage > 0 THEN 1 END)::int as beat_count,
        COUNT(CASE WHEN surprise_percentage < 0 THEN 1 END)::int as miss_count,
        COUNT(CASE WHEN surprise_percentage = 0 THEN 1 END)::int as meet_count,
        (COUNT(CASE WHEN surprise_percentage > 0 THEN 1 END)::float / COUNT(*)::float) as beat_rate,
        AVG(surprise_percentage) as avg_surprise,
        AVG(return_1d) as avg_return_1d
    FROM earnings_events
    WHERE company_symbol = company_sym
        AND surprise_percentage IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for dashboard statistics
CREATE MATERIALIZED VIEW dashboard_stats AS
SELECT 
    COUNT(DISTINCT c.symbol) as total_companies,
    COUNT(DISTINCT CASE WHEN c.sp500_constituent THEN c.symbol END) as sp500_companies,
    COUNT(CASE WHEN e.earnings_date >= CURRENT_DATE AND e.earnings_date <= CURRENT_DATE + INTERVAL '7 days' THEN 1 END) as upcoming_earnings_7d,
    COUNT(CASE WHEN e.earnings_date >= CURRENT_DATE AND e.earnings_date <= CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as upcoming_earnings_30d,
    AVG(CASE WHEN e.surprise_percentage > 0 THEN 1.0 ELSE 0.0 END) as overall_beat_rate,
    COUNT(DISTINCT p.company_symbol) as companies_with_predictions
FROM companies c
LEFT JOIN earnings_events e ON c.symbol = e.company_symbol
LEFT JOIN predictions p ON c.symbol = p.company_symbol AND p.target_date >= CURRENT_DATE;

-- Refresh the materialized view
REFRESH MATERIALIZED VIEW dashboard_stats;

-- Create a trigger to refresh dashboard stats periodically
-- (In production, you'd use a scheduled job or cron)

COMMENT ON DATABASE stockprediction IS 'Calvin Stock Prediction Tool - S&P 500 Earnings Analysis Database';
COMMENT ON EXTENSION vector IS 'pgvector extension for vector similarity search and RAG functionality';

-- Create some helper views for common queries
CREATE VIEW recent_earnings AS
SELECT 
    e.*,
    c.name as company_name,
    c.sector
FROM earnings_events e
JOIN companies c ON e.company_symbol = c.symbol
WHERE e.earnings_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY e.earnings_date DESC;

CREATE VIEW upcoming_earnings AS
SELECT 
    e.*,
    c.name as company_name,
    c.sector,
    p.predicted_return,
    p.confidence_score,
    p.direction as predicted_direction
FROM earnings_events e
JOIN companies c ON e.company_symbol = c.symbol
LEFT JOIN predictions p ON e.company_symbol = p.company_symbol 
    AND p.target_date = e.earnings_date::date + INTERVAL '1 day'
WHERE e.earnings_date >= CURRENT_DATE
ORDER BY e.earnings_date ASC;

-- Grant permissions on views
GRANT SELECT ON recent_earnings TO calvin_user;
GRANT SELECT ON upcoming_earnings TO calvin_user;
GRANT SELECT ON dashboard_stats TO calvin_user;