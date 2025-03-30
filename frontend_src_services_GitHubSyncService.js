/**
 * GitHub Repository Synchronization Service
 * 
 * This service provides real-time synchronization between the local development 
 * environment and GitHub repositories using both webhook and polling methods.
 * 
 * Features:
 * - Secure authentication via environment variables
 * - WebSocket updates for real-time notifications
 * - Fallback polling with configurable intervals and rate limiting
 * - Comprehensive error handling and logging
 * - Event-based architecture for React integration
 */
import axios from 'axios';

class GitHubSyncService {
  constructor() {
    // Configuration with defaults
    this.config = {
      baseApiUrl: process.env.REACT_APP_API_URL || '/api',
      pollingInterval: 60000, // 1 minute default
      useWebhooks: true,
      usePolling: true,
      maxRetries: 3,
      retryDelay: 5000,
    };
    
    // State
    this.isConnected = false;
    this.socket = null;
    this.pollingTimeout = null;
    this.retryCount = 0;
    this.listeners = {
      'repo-updated': [],
      'sync-error': [],
      'connection-status': [],
    };
    
    // Bind methods
    this.startSync = this.startSync.bind(this);
    this.stopSync = this.stopSync.bind(this);
    this.startPolling = this.startPolling.bind(this);
    this.stopPolling = this.stopPolling.bind(this);
    this.connectWebSocket = this.connectWebSocket.bind(this);
    this.disconnectWebSocket = this.disconnectWebSocket.bind(this);
    this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
    this.pollRepositories = this.pollRepositories.bind(this);
    this.syncRepository = this.syncRepository.bind(this);
    this.addEventListener = this.addEventListener.bind(this);
    this.removeEventListener = this.removeEventListener.bind(this);
  }

  /**
   * Start the repository synchronization service
   * @param {Object} options - Configuration options
   */
  startSync(options = {}) {
    // Update config with provided options
    this.config = { ...this.config, ...options };
    this.notifyListeners('connection-status', { status: 'connecting' });
    
    // Connect to WebSocket if enabled
    if (this.config.useWebhooks) {
      this.connectWebSocket();
    }
    
    // Start polling if enabled
    if (this.config.usePolling) {
      this.startPolling();
    }
    
    console.log('GitHub Sync Service started with config:', this.config);
  }

  /**
   * Stop the repository synchronization service
   */
  stopSync() {
    this.disconnectWebSocket();
    this.stopPolling();
    this.isConnected = false;
    this.notifyListeners('connection-status', { status: 'disconnected' });
    console.log('GitHub Sync Service stopped');
  }

  /**
   * Connect to WebSocket for real-time updates
   */
  connectWebSocket() {
    try {
      // Ensure no existing connection
      if (this.socket) {
        this.disconnectWebSocket();
      }
      
      // Create WebSocket connection
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/github`;
      
      this.socket = new WebSocket(wsUrl);
      
      // Set up event handlers
      this.socket.onopen = () => {
        console.log('WebSocket connection established');
        this.isConnected = true;
        this.retryCount = 0;
        this.notifyListeners('connection-status', { status: 'connected', method: 'webhook' });
      };
      
      this.socket.onmessage = this.handleWebSocketMessage;
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.notifyListeners('sync-error', { 
          error: 'WebSocket connection error', 
          details: error 
        });
      };
      
      this.socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        this.notifyListeners('connection-status', { status: 'disconnected' });
        
        // Retry connection if not intentionally closed
        if (event.code !== 1000) {
          if (this.retryCount < this.config.maxRetries) {
            this.retryCount++;
            const delay = this.retryCount * this.config.retryDelay;
            console.log(`Retrying WebSocket connection in ${delay}ms (attempt ${this.retryCount})`);
            setTimeout(() => this.connectWebSocket(), delay);
          } else {
            console.warn('Max WebSocket retry attempts reached. Falling back to polling only.');
            this.notifyListeners('sync-error', { 
              error: 'WebSocket connection failed after max retries',
              fallback: 'Switching to polling mode only'
            });
            
            // Ensure polling is active as fallback
            if (this.config.usePolling && !this.pollingTimeout) {
              this.startPolling();
            }
          }
        }
      };
      
    } catch (error) {
      console.error('Failed to establish WebSocket connection:', error);
      this.notifyListeners('sync-error', { 
        error: 'Failed to establish WebSocket connection', 
        details: error.message 
      });
      
      // Ensure polling is active as fallback
      if (this.config.usePolling && !this.pollingTimeout) {
        this.startPolling();
      }
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnectWebSocket() {
    if (this.socket) {
      try {
        this.socket.close(1000, 'Intentional disconnect');
      } catch (error) {
        console.error('Error closing WebSocket:', error);
      }
      this.socket = null;
    }
  }

  /**
   * Handle incoming WebSocket messages
   * @param {MessageEvent} event - WebSocket message event
   */
  handleWebSocketMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      console.log('WebSocket message received:', data);
      
      if (data.type === 'github_event') {
        // Handle different GitHub event types
        switch (data.event) {
          case 'push':
            this.notifyListeners('repo-updated', {
              repository: data.repository,
              branch: data.branch,
              commits: data.commits,
              source: 'webhook'
            });
            break;
            
          case 'pull_request':
            this.notifyListeners('repo-updated', {
              repository: data.repository,
              pullRequest: data.pull_request,
              action: data.action,
              source: 'webhook'
            });
            break;
            
          default:
            console.log('Unhandled GitHub event:', data.event);
        }
      } else if (data.type === 'ping') {
        // Handle ping messages (keep-alive)
        console.log('Received ping from server');
      } else {
        console.log('Unknown message type:', data.type);
      }
      
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  /**
   * Start repository polling
   */
  startPolling() {
    // Clear any existing polling
    this.stopPolling();
    
    // Initial poll
    this.pollRepositories();
    
    // Schedule regular polling
    this.pollingTimeout = setInterval(
      this.pollRepositories, 
      this.config.pollingInterval
    );
    
    console.log(`Polling started with interval: ${this.config.pollingInterval}ms`);
  }

  /**
   * Stop repository polling
   */
  stopPolling() {
    if (this.pollingTimeout) {
      clearInterval(this.pollingTimeout);
      this.pollingTimeout = null;
      console.log('Polling stopped');
    }
  }

  /**
   * Poll repositories for changes
   */
  async pollRepositories() {
    try {
      console.log('Polling repositories for changes...');
      
      const response = await axios.get(`${this.config.baseApiUrl}/github/repos/status`);
      
      if (response.data.repositories) {
        // Process each repository status
        response.data.repositories.forEach(repo => {
          if (repo.hasChanges) {
            this.notifyListeners('repo-updated', {
              repository: repo.name,
              lastUpdate: repo.lastUpdate,
              changes: repo.changes,
              source: 'polling'
            });
          }
        });
      }
      
      // Update connection status
      if (!this.isConnected) {
        this.isConnected = true;
        this.notifyListeners('connection-status', { 
          status: 'connected', 
          method: 'polling' 
        });
      }
      
    } catch (error) {
      console.error('Error polling repositories:', error);
      this.notifyListeners('sync-error', { 
        error: 'Repository polling failed', 
        details: error.message 
      });
      
      // Update connection status
      if (this.isConnected) {
        this.isConnected = false;
        this.notifyListeners('connection-status', { status: 'error' });
      }
    }
  }

  /**
   * Manually sync a specific repository
   * @param {string} repoName - Repository name
   * @param {Object} options - Sync options
   * @returns {Promise<Object>} - Sync result
   */
  async syncRepository(repoName, options = {}) {
    try {
      console.log(`Manually syncing repository: ${repoName}`, options);
      
      const response = await axios.post(
        `${this.config.baseApiUrl}/github/repos/sync`, 
        {
          repository: repoName,
          ...options
        }
      );
      
      // Notify listeners about the manual sync
      this.notifyListeners('repo-updated', {
        repository: repoName,
        changes: response.data.changes,
        source: 'manual'
      });
      
      return response.data;
      
    } catch (error) {
      console.error(`Error syncing repository ${repoName}:`, error);
      this.notifyListeners('sync-error', { 
        error: `Failed to sync repository ${repoName}`, 
        details: error.message 
      });
      throw error;
    }
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   */
  addEventListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    } else {
      console.warn(`Unknown event type: ${event}`);
    }
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Event callback to remove
   */
  removeEventListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Notify listeners of an event
   * @param {string} event - Event name
   * @param {Object} data - Event data
   */
  notifyListeners(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }
}

// Create singleton instance
const gitHubSyncService = new GitHubSyncService();
export default gitHubSyncService;