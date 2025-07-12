import { MCPServer } from './ollama-client.js';

// MCP Server configurations for local Python servers
export const MCP_SERVERS: MCPServer[] = [
  {
    name: 'test-server',
    command: 'python3',
    args: ['/home/junior/src/calvin/test-mcp-server.py'],
    transport: 'stdio'
  }
  // Add more servers as needed:
  // {
  //   name: 'sentiment',
  //   command: 'python3',
  //   args: ['/home/junior/src/calvin/deprecated/sentiment_analysis_server.py'],
  //   transport: 'stdio'
  // }
];

// Alternative WebSocket-based server configurations
export const MCP_WEBSOCKET_SERVERS: MCPServer[] = [
  {
    name: 'sentiment-ws',
    url: 'ws://localhost:3001/mcp',
    transport: 'websocket'
  },
  {
    name: 'company-ws',
    url: 'ws://localhost:3002/mcp',
    transport: 'websocket'
  },
  {
    name: 'earnings-ws',
    url: 'ws://localhost:3003/mcp',
    transport: 'websocket'
  }
];

// Default Ollama configuration
export const DEFAULT_OLLAMA_CONFIG = {
  model: 'llama3.1',
  temperature: 0.7,
  max_tokens: 2048,
  top_p: 0.9,
  repetition_penalty: 1.1,
  top_k: 40,
  system_prompt: `You are an expert financial analyst assistant with deep knowledge of stock markets, earnings analysis, and investment strategies. 

You have access to real-time market data and analysis tools through MCP (Model Context Protocol) servers that can provide:
- Sentiment analysis from news and social media
- Company financial information and metrics
- Earnings data and historical performance
- Market correlation analysis
- Prediction models and forecasts

Provide accurate, actionable insights while maintaining a professional tone. When referencing specific data from MCP tools, cite the source and explain the relevance to the user's query.

If asked about specific stocks, always try to provide current data when available. Format financial data clearly and highlight key insights.`,
  stream: false
};