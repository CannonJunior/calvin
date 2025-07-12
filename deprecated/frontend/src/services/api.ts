import axios from 'axios';
import type {
  Company,
  EarningsEvent,
  EarningsCalendarItem,
  Prediction,
  AgentResponse,
  DashboardStats,
  EarningsPerformance,
  PredictionPerformance,
} from '@/types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth (if needed)
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Companies API
export const companiesApi = {
  getAll: (params?: {
    skip?: number;
    limit?: number;
    sector?: string;
    sp500_only?: boolean;
  }) => api.get<Company[]>('/companies', { params }),

  getBySymbol: (symbol: string) =>
    api.get<Company>(`/companies/${symbol}`),

  getSectors: () =>
    api.get<{ sectors: string[] }>('/companies/sectors/list'),
};

// Earnings API
export const earningsApi = {
  getCalendar: (params?: {
    start_date?: string;
    end_date?: string;
    symbols?: string;
  }) => api.get<EarningsCalendarItem[]>('/earnings/calendar', { params }),

  getHistory: (symbol: string, limit?: number) =>
    api.get<EarningsEvent[]>(`/earnings/${symbol}/history`, {
      params: { limit },
    }),

  getNext: (symbol: string) =>
    api.get<EarningsEvent>(`/earnings/${symbol}/next`),

  getPerformance: (symbol: string) =>
    api.get<EarningsPerformance>(`/earnings/${symbol}/performance`),

  getUpcomingSummary: (days_ahead?: number) =>
    api.get('/earnings/upcoming/summary', { params: { days_ahead } }),
};

// Predictions API
export const predictionsApi = {
  getAll: (params?: {
    symbol?: string;
    start_date?: string;
    end_date?: string;
    confidence_threshold?: number;
    limit?: number;
  }) => api.get<Prediction[]>('/predictions', { params }),

  getLatest: (symbol: string) =>
    api.get<Prediction>(`/predictions/${symbol}/latest`),

  generate: (symbol: string, target_date?: string) =>
    api.post(`/predictions/${symbol}/generate`, { target_date }),

  getUpcoming: (params?: {
    days_ahead?: number;
    confidence_threshold?: number;
  }) => api.get('/predictions/upcoming/all', { params }),

  getPerformance: (params?: {
    days_back?: number;
    model_version?: string;
  }) => api.get<PredictionPerformance>('/predictions/performance/summary', { params }),
};

// Agents API
export const agentsApi = {
  query: (data: {
    query: string;
    agent_type?: string;
    context?: Record<string, any>;
  }) => api.post<AgentResponse>('/agents/query', data),

  analyze: (symbol: string, analysis_type = 'earnings_pattern') =>
    api.post(`/agents/analysis/${symbol}`, { analysis_type }),

  research: (symbol: string, research_focus?: string) =>
    api.post(`/agents/research/${symbol}`, { research_focus }),

  getStatus: () => api.get('/agents/status'),

  findSimilarScenarios: (
    symbol: string,
    scenario_type = 'earnings',
    limit = 5
  ) =>
    api.post(`/agents/similar-scenarios/${symbol}`, {
      scenario_type,
      limit,
    }),

  explainPrediction: (prediction_id: string) =>
    api.post(`/agents/explain-prediction/${prediction_id}`),
};

// Analytics API
export const analyticsApi = {
  getDashboardOverview: () =>
    api.get<DashboardStats>('/analytics/dashboard/overview'),

  getSectorPerformance: (params?: {
    days_back?: number;
    metric?: string;
  }) => api.get('/analytics/sector-performance', { params }),

  getEarningsCalendarAnalysis: (params?: {
    start_date?: string;
    end_date?: string;
  }) => api.get('/analytics/earnings-calendar/analysis', { params }),

  getCompanyProfile: (symbol: string) =>
    api.get(`/analytics/company/${symbol}/profile`),

  getInsiderTradingAnalysis: (params?: {
    symbol?: string;
    days_back?: number;
    transaction_type?: string;
  }) => api.get('/analytics/insider-trading/analysis', { params }),

  getAnalystAccuracyRankings: (params?: {
    days_back?: number;
    min_ratings?: number;
  }) => api.get('/analytics/analyst-accuracy/rankings', { params }),

  getMarketPatternsAnalysis: (params?: {
    pattern_type?: string;
    symbol?: string;
    days_back?: number;
  }) => api.get('/analytics/market-patterns/analysis', { params }),

  getVolatilityAnalysis: (params?: {
    symbol?: string;
    days_back?: number;
    event_type?: string;
  }) => api.get('/analytics/volatility/analysis', { params }),

  getBacktestingResults: (params?: {
    model_version?: string;
    start_date?: string;
    end_date?: string;
    confidence_threshold?: number;
  }) => api.get('/analytics/backtesting/results', { params }),
};

export default api;