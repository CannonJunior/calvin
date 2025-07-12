# Earnings Dashboard with Ollama & MCP Integration

## Overview
The earnings dashboard now includes functional Ollama chat integration with MCP (Model Context Protocol) server support for enhanced financial analysis.

## Features Added

### 1. Ollama Client Integration
- **TypeScript-based client** (`src/ollama-client.ts`) with full Ollama API support
- **Configurable parameters**: temperature, top-p, max tokens, etc.
- **Chat history management** with persistent conversation context
- **Error handling** and connection status monitoring

### 2. MCP Server Support
- **Local Python MCP servers** via stdio transport
- **WebSocket MCP servers** for remote connections
- **Tool discovery** and automatic integration
- **Context-aware responses** using MCP data

### 3. Enhanced Chat Interface
- **Real-time chat** with loading indicators
- **Message formatting** with financial data highlighting
- **Quick action buttons** for common queries
- **Configuration modal** for Ollama settings

## Setup Instructions

### Prerequisites
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (e.g., Llama 3.1)
ollama pull llama3.1
```

### Dashboard Setup
```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Start the dashboard
./start-dashboard.sh
```

### Testing the Integration

1. **Open the dashboard**: http://localhost:8080/earnings_dashboard.html

2. **Test basic chat**:
   - Type: "Hello, analyze AAPL"
   - The system will attempt to connect to MCP servers and provide enhanced responses

3. **Test MCP tools**:
   - Click on "📊 Sentiment Analysis" button
   - Try asking: "What's the sentiment for AAPL?"

4. **Test configuration**:
   - Click "⚙️ Configure Model" 
   - Adjust temperature, max tokens, etc.
   - Save and test with different settings

## MCP Server Configuration

### Current Test Server
The system includes a test MCP server (`test-mcp-server.py`) with:
- **Stock information** mock data (AAPL, MSFT, GOOGL)
- **Sentiment analysis** with randomized but realistic responses
- **JSON-RPC 2.0** compliant protocol

### Adding More Servers
Edit `src/mcp-config.ts` to add servers:

```typescript
export const MCP_SERVERS: MCPServer[] = [
  {
    name: 'your-server',
    command: 'python3',
    args: ['/path/to/your/server.py'],
    transport: 'stdio'
  }
];
```

## File Structure
```
src/
├── ollama-client.ts          # Core Ollama + MCP client
├── dashboard-integration.ts  # Dashboard UI integration
├── mcp-config.ts            # MCP server configurations
dist/                        # Compiled JavaScript
earnings_dashboard.html      # Main dashboard with integration
test-mcp-server.py          # Test MCP server
```

## Troubleshooting

### Common Issues

1. **"Cannot connect to Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check if localhost:11434 is accessible
   - Verify model is installed: `ollama list`

2. **MCP servers not working**
   - Check console for connection errors
   - Verify Python path and server script exists
   - Test server manually: `python3 test-mcp-server.py`

3. **Chat not responding**
   - Open browser console (F12) for error messages
   - Check if dashboard-integration.js loaded properly
   - Verify TypeScript compilation succeeded

### Debug Mode
Open browser console to see:
- MCP server connection status
- Ollama API requests/responses
- Chat message processing
- Error details

## Next Steps

### Production Enhancements
1. **Real MCP servers** for live financial data
2. **Authentication** for secure API access
3. **WebSocket connections** for real-time updates
4. **Persistent chat history** across sessions
5. **Advanced error recovery** and retry logic

### Additional Features
1. **Voice input** for chat interface
2. **Export chat** conversations
3. **Custom prompts** for different analysis types
4. **Portfolio integration** with MCP tools
5. **Real-time notifications** from MCP servers