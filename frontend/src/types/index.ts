export interface Company {
  id: string;
  symbol: string;
  name: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  description?: string;
  sp500_constituent: boolean;
  pe_ratio?: number;
  eps?: number;
  revenue?: number;
  created_at: string;
  updated_at?: string;
}

export interface EarningsEvent {
  id: string;
  company_symbol: string;
  earnings_date: string;
  quarter: string;
  year: number;
  actual_eps?: number;
  expected_eps?: number;
  surprise_percentage?: number;
  actual_revenue?: number;
  expected_revenue?: number;
  revenue_surprise_percentage?: number;
  stock_price_before?: number;
  stock_price_after_1d?: number;
  stock_price_after_5d?: number;
  return_1d?: number;
  return_5d?: number;
  sp500_return_1d?: number;
  sector_return_1d?: number;
  relative_return_1d?: number;
  volume_before?: number;
  volume_after?: number;
  created_at: string;
  updated_at?: string;
}

export interface EarningsCalendarItem {
  company_symbol: string;
  earnings_date: string;
  quarter: string;
  year: number;
  expected_eps?: number;
  expected_revenue?: number;
  has_prediction: boolean;
  prediction_confidence?: number;
  predicted_direction?: 'UP' | 'DOWN' | 'NEUTRAL';
  historical_beat_rate?: number;
}

export interface Prediction {
  id: string;
  company_symbol: string;
  prediction_date: string;
  target_date: string;
  predicted_return: number;
  confidence_score: number;
  direction: 'UP' | 'DOWN' | 'NEUTRAL';
  model_version: string;
  features_used?: Record<string, any>;
  reasoning?: string;
  similar_scenarios?: SimilarScenario[];
  actual_return?: number;
  prediction_accuracy?: number;
  created_at: string;
  updated_at?: string;
}

export interface SimilarScenario {
  company_symbol: string;
  date: string;
  similarity_score: number;
  scenario_description: string;
  outcome: Record<string, any>;
  key_factors: string[];
}

export interface AnalystRating {
  id: string;
  company_symbol: string;
  analyst_firm?: string;
  analyst_name?: string;
  rating_date: string;
  rating: string;
  target_price?: number;
  current_price?: number;
  target_date?: string;
  actual_price_at_target?: number;
  accuracy_percentage?: number;
  created_at: string;
  updated_at?: string;
}

export interface InsiderTrading {
  id: string;
  company_symbol: string;
  insider_name: string;
  insider_title?: string;
  transaction_date: string;
  transaction_type: 'BUY' | 'SELL';
  shares: number;
  price_per_share: number;
  total_value: number;
  shares_owned_after?: number;
  filing_date?: string;
  created_at: string;
}

export interface AgentResponse {
  agent_type: string;
  response: string;
  confidence?: number;
  sources?: string[];
  metadata?: Record<string, any>;
  timestamp: string;
  processing_time?: number;
}

export interface ChatMessage {
  id: string;
  message: string;
  sender: 'user' | 'agent';
  timestamp: string;
  agent_type?: string;
  metadata?: Record<string, any>;
}

export interface DashboardStats {
  total_sp500_companies: number;
  upcoming_earnings_7d: number;
  recent_prediction_accuracy: number;
  market_sentiment: {
    overall_score: number;
    bullish_percentage: number;
    bearish_percentage: number;
    neutral_percentage: number;
  };
  last_updated: string;
}

export interface EarningsPerformance {
  symbol: string;
  total_earnings_events: number;
  beats: number;
  misses: number;
  meets: number;
  beat_rate: number;
  positive_return_rate: number;
  average_1d_return: number;
  average_surprise_percentage: number;
}

export interface PredictionPerformance {
  period: {
    start: string;
    end: string;
    days: number;
  };
  total_predictions: number;
  direction_accuracy: number;
  average_accuracy: number;
  by_confidence: {
    high: {
      count: number;
      direction_accuracy: number;
    };
    medium: {
      count: number;
      direction_accuracy: number;
    };
    low: {
      count: number;
      direction_accuracy: number;
    };
  };
}

export type TimeFrame = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y';
export type ChartType = 'line' | 'candlestick' | 'volume';
export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'all';