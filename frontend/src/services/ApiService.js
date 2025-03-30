/**
 * API service for interacting with the Anthropic Agent API
 */
class ApiService {
  constructor(baseUrl = 'http://localhost:8000', apiKey = '') {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }
  
  setBaseUrl(baseUrl) {
    this.baseUrl = baseUrl;
  }
  
  setApiKey(apiKey) {
    this.apiKey = apiKey;
  }
  
  // Helper method for making API requests
  async fetchApi(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      ...options.headers
    };
    
    const config = {
      ...options,
      headers
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API error:', error);
      throw error;
    }
  }
  
  // Conversation endpoints
  async getConversations() {
    return await this.fetchApi('/conversations');
  }
  
  async getConversation(conversationId) {
    return await this.fetchApi(`/conversations/${conversationId}`);
  }
  
  async deleteConversation(conversationId) {
    return await this.fetchApi(`/conversations/${conversationId}`, {
      method: 'DELETE'
    });
  }
  
  // Message endpoints
  async sendMessage(message, conversationId = null, model = null, useRag = false) {
    return await this.fetchApi('/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        model,
        use_rag: useRag,
        stream: false
      })
    });
  }
  
  // WebSocket connection for streaming
  createWebSocketConnection(conversationId) {
    const protocol = this.baseUrl.startsWith('https') ? 'wss' : 'ws';
    const baseWsUrl = this.baseUrl.replace(/^https?:\/\//, `${protocol}://`);
    
    const ws = new WebSocket(`${baseWsUrl}/message/stream/${conversationId}`);
    
    // Add authentication to WebSocket connection
    ws.onopen = () => {
      ws.send(JSON.stringify({
        apiKey: this.apiKey
      }));
    };
    
    return ws;
  }
  
  // Image endpoints
  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = `${this.baseUrl}/upload/image`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey
      },
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
  }
  
  async sendMessageWithImage(message, imagePath, conversationId = null, model = null, useRag = false) {
    return await this.fetchApi('/message/image', {
      method: 'POST',
      body: JSON.stringify({
        message,
        image_path: imagePath,
        conversation_id: conversationId,
        model,
        use_rag: useRag
      })
    });
  }
  
  // Tool endpoints
  async getTools(category = null) {
    const endpoint = category ? `/tools?category=${category}` : '/tools';
    return await this.fetchApi(endpoint);
  }
  
  async executeTool(toolName, parameters, conversationId = null) {
    return await this.fetchApi('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({
        tool_name: toolName,
        parameters,
        conversation_id: conversationId
      })
    });
  }
  
  // RAG endpoints
  async getRagDocuments() {
    return await this.fetchApi('/rag/documents');
  }
  
  async getRagDocument(documentId) {
    return await this.fetchApi(`/rag/documents/${documentId}`);
  }
  
  async addRagDocument(content, metadata = {}, chunkStrategy = 'tokens') {
    return await this.fetchApi('/rag/documents', {
      method: 'POST',
      body: JSON.stringify({
        content,
        metadata,
        chunk_strategy: chunkStrategy
      })
    });
  }
  
  async uploadRagDocument(file, metadata = {}, chunkStrategy = 'tokens') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));
    formData.append('chunk_strategy', chunkStrategy);
    
    const url = `${this.baseUrl}/rag/documents/file`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey
      },
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
  }
  
  async deleteRagDocument(documentId) {
    return await this.fetchApi(`/rag/documents/${documentId}`, {
      method: 'DELETE'
    });
  }
  
  async queryRag(query, topK = 5, filters = null) {
    return await this.fetchApi('/rag/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        top_k: topK,
        filters
      })
    });
  }
  
  async getRagStats() {
    return await this.fetchApi('/rag/stats');
  }
  
  // Model endpoints
  async getModels() {
    return await this.fetchApi('/models');
  }
  
  // Health check endpoint
  async healthCheck() {
    return await this.fetchApi('/health');
  }
}

export default ApiService;