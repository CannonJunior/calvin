import { OllamaClientWithMCP, OllamaConfig, ChatMessage } from './ollama-client.js';
import { MCP_SERVERS, DEFAULT_OLLAMA_CONFIG } from './mcp-config.js';

class DashboardIntegration {
  private ollamaClient: OllamaClientWithMCP;
  private chatContainer: HTMLElement | null = null;
  private chatInput: HTMLInputElement | null = null;
  private chatHistory: HTMLElement | null = null;
  private configModal: HTMLElement | null = null;
  private currentConfig: OllamaConfig;

  constructor() {
    this.ollamaClient = new OllamaClientWithMCP();
    this.currentConfig = { ...DEFAULT_OLLAMA_CONFIG };
    this.initialize();
  }

  private async initialize(): Promise<void> {
    // Initialize DOM elements
    this.initializeDOMElements();
    
    // Initialize MCP servers
    await this.initializeMCPServers();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Check Ollama health
    await this.checkOllamaConnection();
    
    // Load available models
    await this.loadAvailableModels();
    
    console.log('Dashboard integration initialized successfully');
  }

  private initializeDOMElements(): void {
    this.chatInput = document.getElementById('chat-input') as HTMLInputElement;
    this.chatContainer = document.querySelector('.chat-container');
    this.configModal = document.getElementById('config-modal');
    
    // Create chat history element if it doesn't exist
    if (!document.getElementById('chat-history')) {
      this.createChatHistory();
    }
    this.chatHistory = document.getElementById('chat-history');
  }

  private createChatHistory(): void {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;

    const historyDiv = document.createElement('div');
    historyDiv.id = 'chat-history';
    historyDiv.className = 'chat-history';
    historyDiv.style.cssText = `
      flex: 1;
      overflow-y: auto;
      padding: 10px;
      background: #2a2a2a;
      border-radius: 8px;
      margin-bottom: 15px;
      min-height: 100px;
      max-height: 200px;
    `;

    const gettingStarted = document.querySelector('.getting-started');
    if (gettingStarted) {
      chatContainer.insertBefore(historyDiv, gettingStarted);
    }
  }

  private async initializeMCPServers(): Promise<void> {
    try {
      await this.ollamaClient.initializeMCPServers(MCP_SERVERS);
      
      // Update MCP tools display
      const availableTools = await this.ollamaClient.getAvailableTools();
      this.updateMCPToolsDisplay(availableTools);
      
      console.log('MCP servers initialized:', Object.keys(availableTools));
    } catch (error) {
      console.error('Failed to initialize MCP servers:', error);
      this.showMessage('Warning: Some MCP analysis tools may not be available', 'warning');
    }
  }

  private updateMCPToolsDisplay(tools: Record<string, any[]>): void {
    const mcpToolsContainer = document.querySelector('.mcp-tools');
    if (!mcpToolsContainer) return;

    // Add status indicator for each tool
    const toolElements = mcpToolsContainer.querySelectorAll('.mcp-tool');
    toolElements.forEach(element => {
      const toolName = element.textContent?.toLowerCase() || '';
      let isAvailable = false;

      // Check if any server has tools available
      for (const [serverName, serverTools] of Object.entries(tools)) {
        if (serverTools.length > 0) {
          if (
            (toolName.includes('sentiment') && serverName === 'sentiment') ||
            (toolName.includes('similar') && serverName === 'company') ||
            (toolName.includes('earnings') && serverName === 'earnings') ||
            (toolName.includes('correlation') && serverName === 'company')
          ) {
            isAvailable = true;
            break;
          }
        }
      }

      // Add visual indicator
      const indicator = document.createElement('span');
      indicator.style.cssText = `
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-left: 8px;
        background-color: ${isAvailable ? '#6bcf7f' : '#ff6b6b'};
      `;
      element.appendChild(indicator);
    });
  }

  private setupEventListeners(): void {
    // Chat input handler
    if (this.chatInput) {
      this.chatInput.addEventListener('keypress', this.handleChatInput.bind(this));
    }

    // Quick action buttons
    const quickActions = document.querySelectorAll('.quick-action');
    quickActions.forEach(action => {
      action.addEventListener('click', () => {
        const question = action.textContent?.replace(/^📊|🏭|📅|📈/, '').trim() || '';
        this.handleQuickAction(question);
      });
    });

    // Configuration modal
    this.setupConfigurationModal();

    // MCP tool buttons
    this.setupMCPToolButtons();
  }

  private async handleChatInput(event: KeyboardEvent): Promise<void> {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      const message = (event.target as HTMLInputElement).value.trim();
      
      if (message) {
        await this.sendMessage(message);
        (event.target as HTMLInputElement).value = '';
      }
    }
  }

  private async handleQuickAction(question: string): Promise<void> {
    if (this.chatInput) {
      this.chatInput.value = question;
    }
    await this.sendMessage(question);
  }

  private async sendMessage(message: string): Promise<void> {
    // Show user message
    this.addMessageToHistory(message, 'user');
    
    // Show loading indicator
    const loadingId = this.addLoadingMessage();
    
    try {
      // Send to Ollama with MCP integration
      const response = await this.ollamaClient.chat(message, this.currentConfig);
      
      // Remove loading indicator
      this.removeLoadingMessage(loadingId);
      
      // Show assistant response
      this.addMessageToHistory(response, 'assistant');
      
    } catch (error) {
      this.removeLoadingMessage(loadingId);
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      this.addMessageToHistory(`Error: ${errorMessage}`, 'error');
    }
  }

  private addMessageToHistory(message: string, type: 'user' | 'assistant' | 'error'): void {
    if (!this.chatHistory) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    messageDiv.style.cssText = `
      margin-bottom: 10px;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 13px;
      line-height: 1.4;
      ${type === 'user' ? 'background: #4a90e2; color: white; margin-left: 20px;' : ''}
      ${type === 'assistant' ? 'background: #3a3a3a; color: #e0e0e0; margin-right: 20px;' : ''}
      ${type === 'error' ? 'background: #ff4444; color: white;' : ''}
    `;

    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 4px;">
        ${type === 'user' ? 'You' : type === 'assistant' ? 'Assistant' : 'Error'} 
        <span style="font-weight: normal; font-size: 11px; opacity: 0.7;">${timestamp}</span>
      </div>
      <div>${this.formatMessage(message)}</div>
    `;

    this.chatHistory.appendChild(messageDiv);
    this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
  }

  private formatMessage(message: string): string {
    // Basic formatting for financial data
    return message
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
      .replace(/\n/g, '<br>') // Line breaks
      .replace(/(\$[\d,]+\.?\d*)/g, '<span style="color: #6bcf7f;">$1</span>') // Money
      .replace(/([+-]?\d+\.?\d*%)/g, '<span style="color: #64ffda;">$1</span>'); // Percentages
  }

  private addLoadingMessage(): string {
    if (!this.chatHistory) return '';

    const loadingId = `loading-${Date.now()}`;
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'chat-message loading';
    loadingDiv.style.cssText = `
      margin-bottom: 10px;
      padding: 8px 12px;
      border-radius: 8px;
      background: #3a3a3a;
      color: #e0e0e0;
      margin-right: 20px;
      font-size: 13px;
    `;

    loadingDiv.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 4px;">Assistant</div>
      <div style="display: flex; align-items: center;">
        <div style="margin-right: 8px;">Thinking</div>
        <div class="loading-dots" style="display: flex; gap: 4px;">
          <div style="width: 4px; height: 4px; border-radius: 50%; background: #64ffda; animation: bounce 1.4s infinite ease-in-out both;"></div>
          <div style="width: 4px; height: 4px; border-radius: 50%; background: #64ffda; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;"></div>
          <div style="width: 4px; height: 4px; border-radius: 50%; background: #64ffda; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;"></div>
        </div>
      </div>
    `;

    this.chatHistory.appendChild(loadingDiv);
    this.chatHistory.scrollTop = this.chatHistory.scrollHeight;

    return loadingId;
  }

  private removeLoadingMessage(loadingId: string): void {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
      loadingElement.remove();
    }
  }

  private setupConfigurationModal(): void {
    // Load current configuration into modal
    this.loadConfigurationModal();

    // Save configuration handler
    const saveButton = document.querySelector('.btn-save');
    if (saveButton) {
      saveButton.addEventListener('click', this.saveConfiguration.bind(this));
    }
  }

  private loadConfigurationModal(): void {
    const elements = {
      temperature: document.getElementById('temperature') as HTMLInputElement,
      topP: document.getElementById('top-p') as HTMLInputElement,
      maxTokens: document.getElementById('max-tokens') as HTMLInputElement,
      repPenalty: document.getElementById('rep-penalty') as HTMLInputElement,
      topK: document.getElementById('top-k') as HTMLInputElement,
      seed: document.getElementById('seed') as HTMLInputElement,
      systemPrompt: document.getElementById('system-prompt') as HTMLTextAreaElement
    };

    if (elements.temperature) elements.temperature.value = this.currentConfig.temperature?.toString() || '0.7';
    if (elements.topP) elements.topP.value = this.currentConfig.top_p?.toString() || '0.9';
    if (elements.maxTokens) elements.maxTokens.value = this.currentConfig.max_tokens?.toString() || '2048';
    if (elements.repPenalty) elements.repPenalty.value = this.currentConfig.repetition_penalty?.toString() || '1.1';
    if (elements.topK) elements.topK.value = this.currentConfig.top_k?.toString() || '40';
    if (elements.seed) elements.seed.value = this.currentConfig.seed?.toString() || '-1';
    if (elements.systemPrompt) elements.systemPrompt.value = this.currentConfig.system_prompt || DEFAULT_OLLAMA_CONFIG.system_prompt;
  }

  private saveConfiguration(): void {
    const config: OllamaConfig = {
      model: (document.getElementById('model-select') as HTMLSelectElement)?.value || 'llama3.1',
      temperature: parseFloat((document.getElementById('temperature') as HTMLInputElement)?.value || '0.7'),
      top_p: parseFloat((document.getElementById('top-p') as HTMLInputElement)?.value || '0.9'),
      max_tokens: parseInt((document.getElementById('max-tokens') as HTMLInputElement)?.value || '2048'),
      repetition_penalty: parseFloat((document.getElementById('rep-penalty') as HTMLInputElement)?.value || '1.1'),
      top_k: parseInt((document.getElementById('top-k') as HTMLInputElement)?.value || '40'),
      seed: parseInt((document.getElementById('seed') as HTMLInputElement)?.value || '-1'),
      system_prompt: (document.getElementById('system-prompt') as HTMLTextAreaElement)?.value || DEFAULT_OLLAMA_CONFIG.system_prompt
    };

    this.currentConfig = config;
    this.showMessage('Configuration saved successfully!', 'success');
    
    // Close modal
    if (this.configModal) {
      (this.configModal as any).style.display = 'none';
    }
  }

  private setupMCPToolButtons(): void {
    const mcpTools = document.querySelectorAll('.mcp-tool');
    mcpTools.forEach(tool => {
      tool.addEventListener('click', async () => {
        const toolText = tool.textContent || '';
        await this.handleMCPTool(toolText);
      });
    });
  }

  private async handleMCPTool(toolText: string): Promise<void> {
    let message = '';

    if (toolText.includes('Sentiment Analysis')) {
      message = 'Analyze the current market sentiment for the visible stocks on the timeline';
    } else if (toolText.includes('Similar Companies')) {
      message = 'Find companies similar to the ones currently displayed';
    } else if (toolText.includes('IPO Companies')) {
      message = 'Show me recent and upcoming IPO companies with their earnings schedules';
    } else if (toolText.includes('Options Analysis')) {
      message = 'Analyze unusual options activity around upcoming earnings';
    } else if (toolText.includes('Market Correlation')) {
      message = 'Show correlations between different stocks and sectors';
    }

    if (message) {
      await this.sendMessage(message);
    }
  }

  private async checkOllamaConnection(): Promise<void> {
    const isHealthy = await this.ollamaClient.checkOllamaHealth();
    if (!isHealthy) {
      this.showMessage('Warning: Cannot connect to Ollama server. Make sure Ollama is running on localhost:11434', 'warning');
    }
  }

  private async loadAvailableModels(): Promise<void> {
    const models = await this.ollamaClient.getAvailableModels();
    const modelSelect = document.getElementById('model-select') as HTMLSelectElement;
    
    if (modelSelect && models.length > 0) {
      modelSelect.innerHTML = '';
      models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelect.appendChild(option);
      });
    }
  }

  private showMessage(message: string, type: 'success' | 'warning' | 'error'): void {
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      color: white;
      font-size: 14px;
      z-index: 10000;
      ${type === 'success' ? 'background: #6bcf7f;' : ''}
      ${type === 'warning' ? 'background: #ffd93d; color: #000;' : ''}
      ${type === 'error' ? 'background: #ff4444;' : ''}
    `;
    messageDiv.textContent = message;

    document.body.appendChild(messageDiv);

    setTimeout(() => {
      messageDiv.remove();
    }, 5000);
  }

  // Public methods for external use
  public async getChatHistory(): Promise<ChatMessage[]> {
    return this.ollamaClient.getChatHistory();
  }

  public clearChatHistory(): void {
    this.ollamaClient.clearChatHistory();
    if (this.chatHistory) {
      this.chatHistory.innerHTML = '';
    }
  }

  public async disconnect(): Promise<void> {
    await this.ollamaClient.disconnect();
  }
}

// Global instance
let dashboardIntegration: DashboardIntegration | undefined;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    dashboardIntegration = new DashboardIntegration();
    (window as any).dashboardIntegration = dashboardIntegration;
  });
} else {
  dashboardIntegration = new DashboardIntegration();
  (window as any).dashboardIntegration = dashboardIntegration;
}

export { DashboardIntegration };