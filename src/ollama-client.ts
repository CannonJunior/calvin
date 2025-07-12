import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { WebSocketClientTransport } from '@modelcontextprotocol/sdk/client/websocket.js';

interface OllamaConfig {
  model: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  repetition_penalty?: number;
  top_k?: number;
  seed?: number;
  system_prompt?: string;
  stream?: boolean;
}

interface MCPServer {
  name: string;
  command?: string;
  args?: string[];
  url?: string;
  transport: 'stdio' | 'websocket';
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

class OllamaClientWithMCP {
  private ollamaBaseUrl: string;
  private mcpClients: Map<string, Client> = new Map();
  private mcpServers: MCPServer[] = [];
  private chatHistory: ChatMessage[] = [];

  constructor(ollamaBaseUrl: string = 'http://localhost:11434') {
    this.ollamaBaseUrl = ollamaBaseUrl;
  }

  // Initialize MCP servers
  async initializeMCPServers(servers: MCPServer[]): Promise<void> {
    this.mcpServers = servers;
    
    for (const server of servers) {
      try {
        let transport;
        
        if (server.transport === 'stdio' && server.command) {
          // For local Python MCP servers
          transport = new StdioClientTransport({
            command: server.command,
            args: server.args || []
          });
        } else if (server.transport === 'websocket' && server.url) {
          // For WebSocket-based MCP servers
          transport = new WebSocketClientTransport(new URL(server.url));
        } else {
          console.warn(`Invalid server configuration for ${server.name}`);
          continue;
        }

        const client = new Client({
          name: `calvin-dashboard-${server.name}`,
          version: '1.0.0'
        }, {
          capabilities: {}
        });

        await client.connect(transport);
        this.mcpClients.set(server.name, client);
        console.log(`Connected to MCP server: ${server.name}`);
      } catch (error) {
        console.error(`Failed to connect to MCP server ${server.name}:`, error);
      }
    }
  }

  // Get available MCP tools
  async getAvailableTools(): Promise<Record<string, any[]>> {
    const allTools: Record<string, any[]> = {};
    
    for (const [serverName, client] of this.mcpClients) {
      try {
        const response = await client.listTools();
        allTools[serverName] = response.tools || [];
      } catch (error) {
        console.error(`Failed to get tools from ${serverName}:`, error);
        allTools[serverName] = [];
      }
    }
    
    return allTools;
  }

  // Call MCP tool
  async callMCPTool(serverName: string, toolName: string, arguments_: Record<string, any>): Promise<any> {
    const client = this.mcpClients.get(serverName);
    if (!client) {
      throw new Error(`MCP server ${serverName} not found`);
    }

    try {
      const response = await client.callTool({
        name: toolName,
        arguments: arguments_
      });
      return response;
    } catch (error) {
      console.error(`Failed to call tool ${toolName} on ${serverName}:`, error);
      throw error;
    }
  }

  // Enhanced chat with MCP context
  async chat(message: string, config: Partial<OllamaConfig> = {}): Promise<string> {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    this.chatHistory.push(userMessage);

    // Check if message contains MCP tool requests
    const mcpContext = await this.processMCPRequests(message);
    
    // Prepare enhanced prompt with MCP context
    let enhancedMessage = message;
    if (mcpContext.length > 0) {
      enhancedMessage = `${message}\n\nAdditional context from MCP tools:\n${mcpContext.join('\n')}`;
    }

    const defaultConfig = {
      model: 'llama3.1',
      temperature: 0.7,
      max_tokens: 2048,
      stream: false,
      ...config
    };

    try {
      const response = await fetch(`${this.ollamaBaseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: defaultConfig.model,
          prompt: enhancedMessage,
          system: defaultConfig.system_prompt || 'You are an expert financial analyst assistant with access to real-time market data and analysis tools.',
          options: {
            temperature: defaultConfig.temperature,
            top_p: defaultConfig.top_p,
            top_k: defaultConfig.top_k,
            repeat_penalty: defaultConfig.repetition_penalty,
            seed: defaultConfig.seed
          },
          stream: defaultConfig.stream
        })
      });

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: result.response,
        timestamp: new Date()
      };
      this.chatHistory.push(assistantMessage);

      return result.response;
    } catch (error) {
      console.error('Ollama API error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Error: Could not connect to Ollama server. ${errorMessage}`;
    }
  }

  // Process potential MCP requests in the message
  private async processMCPRequests(message: string): Promise<string[]> {
    const mcpResponses: string[] = [];
    
    // Simple keyword-based MCP tool detection
    const lowerMessage = message.toLowerCase();
    
    try {
      // Sentiment analysis
      if (lowerMessage.includes('sentiment') || lowerMessage.includes('feeling') || lowerMessage.includes('mood')) {
        if (this.mcpClients.has('sentiment')) {
          const response = await this.callMCPTool('sentiment', 'analyze_sentiment', { text: message });
          mcpResponses.push(`Sentiment Analysis: ${JSON.stringify(response)}`);
        }
      }

      // Company analysis
      const stockSymbols = this.extractStockSymbols(message);
      if (stockSymbols.length > 0 && this.mcpClients.has('company')) {
        for (const symbol of stockSymbols) {
          try {
            const response = await this.callMCPTool('company', 'get_company_info', { symbol });
            mcpResponses.push(`Company Info for ${symbol}: ${JSON.stringify(response)}`);
          } catch (error) {
            console.warn(`Failed to get company info for ${symbol}`);
          }
        }
      }

      // Earnings data
      if (lowerMessage.includes('earnings') || lowerMessage.includes('report')) {
        if (this.mcpClients.has('earnings') && stockSymbols.length > 0) {
          for (const symbol of stockSymbols) {
            try {
              const response = await this.callMCPTool('earnings', 'get_earnings_data', { symbol });
              mcpResponses.push(`Earnings Data for ${symbol}: ${JSON.stringify(response)}`);
            } catch (error) {
              console.warn(`Failed to get earnings for ${symbol}`);
            }
          }
        }
      }

      // Market correlation
      if (lowerMessage.includes('correlation') || lowerMessage.includes('relationship')) {
        if (this.mcpClients.has('correlation') && stockSymbols.length >= 2) {
          try {
            const response = await this.callMCPTool('correlation', 'analyze_correlation', { symbols: stockSymbols });
            mcpResponses.push(`Market Correlation: ${JSON.stringify(response)}`);
          } catch (error) {
            console.warn('Failed to analyze correlation');
          }
        }
      }

    } catch (error) {
      console.error('Error processing MCP requests:', error);
    }

    return mcpResponses;
  }

  // Extract stock symbols from message
  private extractStockSymbols(message: string): string[] {
    const symbolPattern = /\b[A-Z]{1,5}\b/g;
    const matches = message.match(symbolPattern) || [];
    
    // Filter common words that might match the pattern
    const commonWords = ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'];
    
    return matches.filter(symbol => !commonWords.includes(symbol) && symbol.length <= 5);
  }

  // Get chat history
  getChatHistory(): ChatMessage[] {
    return [...this.chatHistory];
  }

  // Clear chat history
  clearChatHistory(): void {
    this.chatHistory = [];
  }

  // Disconnect all MCP clients
  async disconnect(): Promise<void> {
    for (const [serverName, client] of this.mcpClients) {
      try {
        await client.close();
        console.log(`Disconnected from MCP server: ${serverName}`);
      } catch (error) {
        console.error(`Failed to disconnect from ${serverName}:`, error);
      }
    }
    this.mcpClients.clear();
  }

  // Check if Ollama is available
  async checkOllamaHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.ollamaBaseUrl}/api/tags`);
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  // Get available Ollama models
  async getAvailableModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.ollamaBaseUrl}/api/tags`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.models?.map((model: any) => model.name) || [];
    } catch (error) {
      console.error('Failed to get Ollama models:', error);
      return [];
    }
  }
}

export { OllamaClientWithMCP, type OllamaConfig, type MCPServer, type ChatMessage };