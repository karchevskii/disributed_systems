class GameService {
  constructor(apiBaseUrl, gameApiUrl, onSocketMessage, onError) {
    // Use environment variables with fallbacks
    this.apiBaseUrl = process.env.VUE_APP_USERS_SERVICE_URL ;
    this.gameApiUrl = process.env.VUE_APP_GAME_SERVICE_URL;
    this.gameHistoryApiUrl = process.env.VUE_APP_HISTORY_SERVICE_URL;
    this.wsHost = process.env.VUE_APP_WS_HOST;
    
    this.onSocketMessage = onSocketMessage;
    this.onError = onError;
    this.socket = null;
  }

  // Auth methods
  async checkAuthStatus() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/auth/check-auth`, {
        method: 'GET',
        credentials: 'include', // Important for sending cookies
      });
      
      return response.ok;
    } catch (error) {
      console.error('Error checking auth status:', error);
      return false;
    }
  }

  async getUserInfo() {
    const response = await fetch(`${this.apiBaseUrl}/users/me`, {
      method: 'GET',
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error('Failed to get user info');
    }
    
    return await response.json();
  }

  async getGithubAuthUrl() {
    const response = await fetch(`${this.apiBaseUrl}/auth/github/authorize`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to get GitHub authorization URL');
    }
    
    const data = await response.json();
    return data.authorization_url;
  }

  async createGuestUser() {
    const response = await fetch(`${this.apiBaseUrl}/auth/create-guest`, {
      method: 'GET',
      credentials: 'include',
    });
    
    return response.ok;
  }

  async logout() {
    return await fetch(`${this.apiBaseUrl}/auth/logout`, {
      method: 'GET',
      credentials: 'include',
    });
  }

  // Game methods
  async createGame(gameMode, symbol) {
    const response = await fetch(`${this.gameApiUrl}/game/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: gameMode === 'human' ? 'multiplayer' : 'bot',
        symbol: symbol.toLowerCase() // Backend expects lowercase 'x' or 'o'
      }),
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Failed to create game: ' + response.statusText);
    }
    
    return await response.json();
  }

  async joinGame(gameId) {
    const response = await fetch(`${this.gameApiUrl}/game/join/${gameId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Failed to join game: ' + response.statusText);
    }
    
    return await response.json();
  }
  
  // Game history methods
  async getGameHistory() {
    try {
      const response = await fetch(`${this.gameHistoryApiUrl}/games`, {
        method: 'GET',
        credentials: 'include'
      });
      
      // For any HTTP error, just return empty games array
      // This includes 404, 403, 500, etc.
      if (!response.ok) {
        console.log(`Game history API returned status: ${response.status}`);
        // Return empty games array instead of throwing error
        return { games: [] };
      }
      
      // Get the raw text first
      const responseText = await response.text();
      
      // If response is empty, return empty array
      if (!responseText.trim()) {
        return { games: [] };
      }
      
      // Try to parse the JSON
      try {
        return JSON.parse(responseText);
      } catch (parseError) {
        console.error('Error parsing game history JSON:', parseError);
        console.log('Raw response:', responseText);
        
        // If there's a parsing error, return an empty data structure
        return {
          games: []
        };
      }
    } catch (error) {
      console.error('Error in getGameHistory:', error);
      // Return empty games array instead of throwing error
      return { games: [] };
    }
  }

  // WebSocket methods
  connectToGameSocket(gameId) {
    // Close any existing socket connection
    this.closeSocket();
    
    // Log connection attempt
    console.log(`Attempting to connect to game ${gameId}`);
    
    // Determine the appropriate WebSocket protocol
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    
    // Create WebSocket connection
    this.socket = new WebSocket(`${wsProtocol}${this.wsHost}/ws/game/${gameId}`);
    
    // Set up event handlers
    this.socket.onopen = () => {
      console.log('WebSocket connection established');
      // Notify the application that connection is established
      if (this.onSocketMessage) {
        this.onSocketMessage({
          type: 'connection_status',
          status: 'connected'
        });
      }
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (this.onError) {
        this.onError('Error connecting to game server', 'error');
      }
      
      // Notify about connection status
      if (this.onSocketMessage) {
        this.onSocketMessage({
          type: 'connection_status',
          status: 'error',
          message: 'Connection error'
        });
      }
    };
    
    this.socket.onclose = (event) => {
      console.log(`WebSocket connection closed: ${event.code} - ${event.reason}`);
      
      // Notify about disconnection
      if (this.onSocketMessage) {
        this.onSocketMessage({
          type: 'connection_status',
          status: 'disconnected',
          code: event.code,
          reason: event.reason
        });
      }
    };
    
    return this.socket;
  }

  closeSocket() {
    if (this.socket) {
      // Only attempt to close if the socket is not already closed
      if (this.socket.readyState !== WebSocket.CLOSED && 
          this.socket.readyState !== WebSocket.CLOSING) {
        console.log('Closing WebSocket connection');
        this.socket.close();
      }
      this.socket = null;
    }
  }

  sendMove(position) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'move',
        position: position
      }));
    } else {
      if (this.onError) {
        this.onError('Connection to game server lost', 'error');
      }
    }
  }
  
  sendChatMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'chat',
        message: message
      }));
    } else {
      if (this.onError) {
        this.onError('Connection to game server lost', 'error');
      }
    }
  }
  
  // Check if socket connection is active
  isSocketConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}

export default GameService;