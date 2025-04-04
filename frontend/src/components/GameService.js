class GameService {
  constructor(apiBaseUrl, gameApiUrl, onSocketMessage, onError) {
    // For development outside Docker
    if (window.location.hostname === 'localhost') {
      this.apiBaseUrl = 'http://tictactoe.local/users-service';
      this.gameApiUrl = 'http://tictactoe.local/game-service';
      this.gameHistoryApiUrl = 'http://tictactoe.local/game-history';
      this.wsHost = 'tictactoe.local/game-service';
    } else {
      // For production/Docker environment
      this.apiBaseUrl = 'http://tictactoe.local/users-service';
      this.gameApiUrl = 'http://tictactoe.local/game-service';
      this.gameHistoryApiUrl = 'http://tictactoe.local/game-history';
      this.wsHost = 'tictactoe.local/game-service';
    }
    
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
    const response = await fetch(`${this.gameHistoryApiUrl}/games`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Failed to get game history: ' + response.statusText);
    }
    
    return await response.json();
  }

  // WebSocket methods
  connectToGameSocket(gameId) {
    // Close any existing socket connection
    this.closeSocket();
    
    // Determine the appropriate WebSocket protocol
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    
    // Create WebSocket connection
    this.socket = new WebSocket(`${wsProtocol}${this.wsHost}/ws/game/${gameId}`);
    
    // Set up event handlers
    this.socket.onopen = () => {
      console.log('WebSocket connection established');
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
    };
    
    this.socket.onclose = () => {
      console.log('WebSocket connection closed');
    };
  }

  closeSocket() {
    if (this.socket) {
      this.socket.close();
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
}

export default GameService;