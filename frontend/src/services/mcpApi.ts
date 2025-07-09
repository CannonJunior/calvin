/**
 * MCP-powered API client for Calvin Stock Prediction Tool
 * Replaces direct HTTP calls with MCP server interactions
 */
import axios from 'axios';
import type {
  Company,
  EarningsEvent,
  EarningsCalendarItem,
  Prediction,
  AgentResponse,
  DashboardStats,
} from '@/types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const mcpApi = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
mcpApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('MCP API Error:', error);
    return Promise.reject(error);
  }
);

// MCP Server Management
export const mcpServerApi = {
  getStatus: () => mcpApi.get('/mcp/status'),
  getHealth: () => mcpApi.get('/mcp/health'),
  getAvailableTools: () => mcpApi.get('/mcp/tools'),
  getAvailableResources: () => mcpApi.get('/mcp/resources'),
  
  // Generic MCP tool call
  callTool: (serverName: string, toolName: string, arguments: any) =>
    mcpApi.post('/mcp/tool', { server_name: serverName, tool_name: toolName, arguments }),
  
  // Generic MCP resource request
  getResource: (serverName: string, resourceUri: string) =>
    mcpApi.post('/mcp/resource', { server_name: serverName, resource_uri: resourceUri }),
};

// Companies API (via MCP company-data server)
export const companiesApi = {
  getAll: (params?: {
    limit?: number;
    sector?: string;
  }) => mcpApi.get('/companies', { params }),

  getBySymbol: (symbol: string) =>
    mcpApi.get(`/companies/${symbol}`),

  getSectors: () =>
    mcpApi.get('/companies/sectors/list'),

  search: (query: string, limit = 10) =>
    mcpServerApi.callTool('company-data', 'search_companies', { query, limit }),

  add: (companyData: any) =>
    mcpServerApi.callTool('company-data', 'add_company', { company_data: companyData }),
};

// Financial Data API (via MCP finance-data server)
export const financeApi = {
  getStockPrice: (symbol: string) =>
    mcpApi.get(`/finance/stock/${symbol}`),

  getMarketData: (symbol: string, period = '1mo') =>
    mcpApi.get(`/finance/market-data/${symbol}`, { params: { period } }),

  getCompanyInfo: (symbol: string) =>
    mcpApi.get(`/finance/company-info/${symbol}`),

  getMarketIndices: () =>
    mcpApi.get('/finance/market-indices'),

  searchStocks: (query: string, limit = 10) =>
    mcpServerApi.callTool('finance-data', 'search_stocks', { query, limit }),
};

// Earnings API (via MCP earnings-analysis server)
export const earningsApi = {
  getCalendar: (params?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => mcpApi.get('/earnings/calendar', { params }),

  getHistory: (symbol: string, quartersBack = 8) =>
    mcpApi.get(`/earnings/history/${symbol}`, { params: { quarters_back: quartersBack } }),

  analyzeSurprise: (
    symbol: string,
    actualEps: number,
    expectedEps: number,
    actualRevenue?: number,
    expectedRevenue?: number
  ) => mcpServerApi.callTool('earnings-analysis', 'analyze_earnings_surprise', {
    symbol,
    actual_eps: actualEps,
    expected_eps: expectedEps,
    actual_revenue: actualRevenue,
    expected_revenue: expectedRevenue,
  }),

  saveResult: (earningsData: any) =>
    mcpServerApi.callTool('earnings-analysis', 'save_earnings_result', { earnings_data: earningsData }),

  getSentimentSummary: (symbol: string, earningsDate: string) =>
    mcpServerApi.callTool('earnings-analysis', 'get_earnings_sentiment_summary', { symbol, earnings_date: earningsDate }),

  findSimilarPatterns: (targetCompany: string, surpriseType: string, lookbackDays = 365) =>
    mcpServerApi.callTool('earnings-analysis', 'find_similar_earnings_patterns', {
      target_company: targetCompany,
      surprise_type: surpriseType,
      lookback_days: lookbackDays,
    }),
};

// Sentiment Analysis API (via MCP sentiment-analysis server)
export const sentimentApi = {
  analyze: (text: string, context = 'general') =>
    mcpApi.post('/sentiment/analyze', { text, context }),

  analyzeEarnings: (earningsText: string, context = 'earnings_call') =>
    mcpServerApi.callTool('sentiment-analysis', 'analyze_earnings_sentiment', {
      earnings_text: earningsText,
      context,
    }),

  batchAnalysis: (texts: string[], labels?: string[]) =>
    mcpApi.post('/sentiment/batch', texts, { params: { labels } }),

  trendAnalysis: (timeSeriesTexts: Array<{ timestamp: string; text: string }>) =>
    mcpServerApi.callTool('sentiment-analysis', 'sentiment_trend_analysis', {
      time_series_texts: timeSeriesTexts,
    }),

  extractKeySentiments: (text: string, minSentenceLength = 10) =>
    mcpServerApi.callTool('sentiment-analysis', 'extract_key_sentiments', {
      text,
      min_sentence_length: minSentenceLength,
    }),

  getFinancialKeywords: () =>
    mcpServerApi.getResource('sentiment-analysis', 'sentiment://financial-keywords'),
};

// Predictions API (via MCP stock-predictions server)
export const predictionsApi = {
  predictNextDay: (symbol: string, earningsData: any, marketContext?: any) =>
    mcpApi.post('/predictions/next-day', {
      symbol,
      earnings_data: earningsData,
      market_context: marketContext,
    }),

  getHistory: (symbol: string, daysBack = 30) =>
    mcpApi.get(`/predictions/history/${symbol}`, { params: { days_back: daysBack } }),

  getTop: (confidenceThreshold = 0.7, limit = 10) =>
    mcpApi.get('/predictions/top', {
      params: { confidence_threshold: confidenceThreshold, limit },
    }),

  analyzeAccuracy: (symbol: string, actualResults: any[]) =>
    mcpServerApi.callTool('stock-predictions', 'analyze_prediction_accuracy', {
      symbol,
      actual_results: actualResults,
    }),

  getBatchPredictions: (earningsCalendar: any[], marketContext?: any) =>
    mcpServerApi.callTool('stock-predictions', 'get_batch_predictions', {
      earnings_calendar: earningsCalendar,
      market_context: marketContext,
    }),

  save: (predictionData: any) =>
    mcpServerApi.callTool('stock-predictions', 'save_prediction', { prediction_data: predictionData }),
};

// Comprehensive Analysis API
export const analysisApi = {
  batchAnalysis: (symbol: string) =>
    mcpApi.post('/analysis/batch', { symbol }),

  // Combined analysis using multiple MCP servers
  fullStockAnalysis: async (symbol: string) => {
    try {
      const [
        stockPrice,
        companyInfo,
        companyDetails,
        earningsHistory,
        predictionHistory,
      ] = await Promise.all([
        financeApi.getStockPrice(symbol),
        financeApi.getCompanyInfo(symbol),
        companiesApi.getBySymbol(symbol),
        earningsApi.getHistory(symbol, 4),
        predictionsApi.getHistory(symbol, 30),
      ]);

      return {
        symbol,
        stock_price: stockPrice.data,
        company_info: companyInfo.data,
        company_details: companyDetails.data,
        earnings_history: earningsHistory.data,
        prediction_history: predictionHistory.data,
        analysis_timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Full stock analysis failed:', error);
      throw error;
    }
  },

  // Earnings impact analysis
  earningsImpactAnalysis: async (symbol: string, earningsText: string) => {
    try {
      const [
        sentimentAnalysis,
        stockPrice,
        earningsHistory,
      ] = await Promise.all([
        sentimentApi.analyzeEarnings(earningsText),
        financeApi.getStockPrice(symbol),
        earningsApi.getHistory(symbol, 1),
      ]);

      // Generate prediction based on sentiment and earnings data
      const prediction = await predictionsApi.predictNextDay(
        symbol,
        earningsHistory.data,
        { sentiment: sentimentAnalysis.data }
      );

      return {
        symbol,
        sentiment: sentimentAnalysis.data,
        current_price: stockPrice.data,
        recent_earnings: earningsHistory.data,
        prediction: prediction.data,
        analysis_timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Earnings impact analysis failed:', error);
      throw error;
    }
  },
};

// Dashboard API that aggregates data from multiple MCP servers
export const dashboardApi = {
  getOverview: async () => {
    try {
      const [
        mcpStatus,
        marketIndices,
        topPredictions,
        earningsCalendar,
      ] = await Promise.all([
        mcpServerApi.getStatus(),
        financeApi.getMarketIndices(),
        predictionsApi.getTop(0.6, 5),
        earningsApi.getCalendar(),
      ]);

      return {
        mcp_status: mcpStatus.data,
        market_indices: marketIndices.data,
        top_predictions: topPredictions.data,
        upcoming_earnings: earningsCalendar.data,
        dashboard_timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Dashboard overview failed:', error);
      throw error;
    }
  },

  getMarketSentiment: async () => {
    try {
      // Get recent earnings calendar and analyze sentiment for each
      const earningsCalendar = await earningsApi.getCalendar();
      const earnings = earningsCalendar.data.earnings_calendar || [];

      const sentimentPromises = earnings.slice(0, 10).map(async (earning: any) => {
        try {
          const sentiment = await sentimentApi.analyze(
            `${earning.symbol} earnings announcement scheduled`,
            'earnings'
          );
          return {
            symbol: earning.symbol,
            sentiment: sentiment.data,
            earnings_date: earning.earnings_date,
          };
        } catch (error) {
          return {
            symbol: earning.symbol,
            sentiment: { error: 'Analysis failed' },
            earnings_date: earning.earnings_date,
          };
        }
      });

      const sentiments = await Promise.all(sentimentPromises);

      return {
        market_sentiment: sentiments,
        analysis_timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Market sentiment analysis failed:', error);
      throw error;
    }
  },
};

// Export the main API object
export const mcpApiClient = {
  server: mcpServerApi,
  companies: companiesApi,
  finance: financeApi,
  earnings: earningsApi,
  sentiment: sentimentApi,
  predictions: predictionsApi,
  analysis: analysisApi,
  dashboard: dashboardApi,
};

export default mcpApiClient;