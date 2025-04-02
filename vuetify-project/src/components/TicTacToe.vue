<template>
  <v-app>
    <v-main>
      <v-container class="fill-height">
        <v-row justify="center">
          <v-col cols="12" sm="8" md="6" lg="4">
            
            <!-- Initial Login Screen (shown if not logged in) -->
            <v-card v-if="!isLoggedIn" elevation="10" class="pa-4">
              <v-card-title class="text-center text-h4 mb-4">Welcome to Tic Tac Toe</v-card-title>

              <v-card-text class="text-center">
                Please login or continue as a guest to play
              </v-card-text>
              
              <div class="d-flex flex-column align-center mb-4">
                <!-- Login with GitHub -->
                <v-btn 
                  color="primary" 
                  class="mb-3" 
                  block
                  @click="loginWithGithub"
                >
                  <v-icon left>mdi-github</v-icon>
                  Login with GitHub
                </v-btn>
                
                <!-- Login as Guest -->
                <v-btn 
                  color="secondary" 
                  block
                  @click="continueAsGuest"
                >
                  <v-icon left>mdi-account-outline</v-icon>
                  Continue as Guest
                </v-btn>
              </div>
            </v-card>
            
            <!-- Main Menu -->
            <v-card v-else elevation="10" class="pa-4">
              <v-card-title class="text-center text-h4 mb-4">Tic Tac Toe</v-card-title>
              
              <!-- User Info - Only show logout on main menu -->
              <div class="d-flex justify-space-between align-center mb-4">
                <div>
                  <v-chip :color="userType === 'github' ? 'primary' : 'secondary'" outlined>
                    <v-avatar left>
                      <v-icon>{{ userType === 'github' ? 'mdi-github' : 'mdi-account-outline' }}</v-icon>
                    </v-avatar>
                    {{ username }}
                  </v-chip>
                </div>

                <v-btn v-if="!inGame" small text color="grey" @click="logout">
                  <v-icon small left>mdi-logout</v-icon>
                  Logout
                </v-btn>
              </div>
              
              <!-- Game Mode Selection (if not in a game) -->
              <div v-if="!inGame" class="mb-4">
                <v-card-subtitle class="text-center pb-0">
                  How would you like to play?
                </v-card-subtitle>
                
                <div class="d-flex flex-column mt-3">
                  <!-- Create New Game -->
                  <v-btn 
                    color="primary" 
                    class="mb-3" 
                    block
                    @click="showGameModeDialog = true"
                  >
                    <v-icon left>mdi-plus-circle</v-icon>
                    Create New Game
                  </v-btn>
                  
                  <!-- Join Game -->
                  <v-btn 
                    color="secondary" 
                    class="mb-3" 
                    block 
                    @click="showJoinDialog = true"
                  >
                    <v-icon left>mdi-account-multiple</v-icon>
                    Join Game
                  </v-btn>
                </div>
              </div>
              
              <!-- Game View (when in a game) -->
              <div v-else>
                <!-- Game Info - Simplified based on game mode -->
                <div class="d-flex justify-space-between align-center mb-3">
                  <div>
                    <!-- Only show game code for human multiplayer games -->
                    <v-chip v-if="gameMode === 'human'" color="success" small>
                      Game #{{ gameCode }}
                    </v-chip>
                    
                    <!-- Opponent icon (Human/Bot) -->
                    <v-chip :color="gameMode === 'bot' ? 'info' : 'warning'" x-small>
                      <v-icon left x-small>{{ gameMode === 'bot' ? 'mdi-robot' : 'mdi-account' }}</v-icon>
                      {{ gameMode === 'bot' ? 'Bot' : 'Human' }}
                    </v-chip>
                  </div>
                  
                  <!-- Only show invite link option for human multiplayer games -->
                  <v-btn v-if="gameMode === 'human'" x-small text color="primary" @click="copyGameLink">
                    <v-icon x-small left>mdi-content-copy</v-icon>
                    Copy Invite Link
                  </v-btn>
                </div>
                
                <!-- Game/Turn Status (shows whos turn it's right now) -->
                <v-card-subtitle class="text-center text-h6 mb-2">
                  {{ gameStatus }}
                </v-card-subtitle>
                
                <!-- Game Board -->
                <v-row class="mb-4">
                  <v-col cols="12">
                    <div class="game-board">
                      <div v-for="(row, rowIndex) in board" :key="'row-' + rowIndex" class="game-row">
                        <div 
                          v-for="(cell, colIndex) in row" 
                          :key="'cell-' + rowIndex + '-' + colIndex"
                          class="game-cell"
                          @click="makeMove(rowIndex, colIndex)"
                          :class="{ 'disabled': cell !== '' || gameOver || currentPlayer !== playerSymbol }"
                        >
                          <span v-if="cell === 'X'" class="x-mark">X</span>
                          <span v-else-if="cell === 'O'" class="o-mark">O</span>
                        </div>
                      </div>
                    </div>
                  </v-col>
                </v-row>
                
                <!-- Game Control Buttons -->
                <div class="text-center">
                  <!-- Only show "Back to Menu" button when game is over -->
                  <v-btn v-if="gameOver" color="success" @click="leaveGame">
                    <v-icon left>mdi-exit-to-app</v-icon>
                    Back to Menu
                  </v-btn>
                  
                  <!-- Only show "Leave Game" when game is in progress -->
                  <v-btn v-if="!gameOver" color="error" @click="leaveGame">
                    <v-icon left>mdi-exit-to-app</v-icon>
                    Leave Game
                  </v-btn>
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
      
      <!-- Game Mode Selection Dialog (Human/Bot) -->
      <v-dialog v-model="showGameModeDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Choose Game Mode</v-card-title>

          <v-card-text>
            <p class="mb-4">Who would you like to play against?</p>
            
            <v-list>
              <!-- Play against Human -->
              <v-list-item @click="createNewGame('human')" link>
                <v-list-item-icon>
                  <v-icon>mdi-account</v-icon>
                </v-list-item-icon>

                <v-list-item-content>
                  <v-list-item-title>Play against a Human</v-list-item-title>

                  <v-list-item-subtitle>Create a game and invite a friend</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
              
              <!-- Play against Bot -->
              <v-list-item @click="createNewGame('bot')" link>
                <v-list-item-icon>
                  <v-icon>mdi-robot</v-icon>
                </v-list-item-icon>

                <v-list-item-content>
                  <v-list-item-title>Play against the Bot</v-list-item-title>

                  <v-list-item-subtitle>Challenge our AI opponent</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card-text>
          
          <!-- Cancel Button -->
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="grey" text @click="showGameModeDialog = false">Cancel</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- Symbol Selection Dialog (X or O) -->
      <v-dialog v-model="showSymbolDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Choose Your Symbol</v-card-title>

          <v-card-text>
            <p class="mb-4">Which symbol would you like to play with?</p>
            
            <v-list>
              <!-- Choose X -->
              <v-list-item @click="confirmCreateGame('X')" link>
                <v-list-item-icon>
                  <v-icon color="red">mdi-alpha-x</v-icon>
                </v-list-item-icon>

                <v-list-item-content>
                  <v-list-item-title>Play as X</v-list-item-title>

                  <v-list-item-subtitle>X always goes first</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
              
              <!-- Choose O -->
              <v-list-item @click="confirmCreateGame('O')" link>
                <v-list-item-icon>
                  <v-icon color="blue">mdi-alpha-o</v-icon>
                </v-list-item-icon>

                <v-list-item-content>
                  <v-list-item-title>Play as O</v-list-item-title>

                  <v-list-item-subtitle>O goes second</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card-text>
          
          <!-- Cancel Button -->
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="grey" text @click="showSymbolDialog = false">Cancel</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- Join Game Dialog -->
      <v-dialog v-model="showJoinDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Join a Game</v-card-title>

          <!-- Textfield for Game-Code -->
          <v-card-text>
            <v-form @submit.prevent="joinGame">
              <v-text-field
                label="Game ID"
                v-model="joinGameCode"
                prepend-icon="mdi-pound"
                placeholder="Enter game ID or paste invite link"
                required
              ></v-text-field>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>

            <!-- Cancel Button -->
            <v-btn color="grey" text @click="showJoinDialog = false">Cancel</v-btn>

            <!-- Join Button -->
            <v-btn color="primary" @click="joinGame" :disabled="!joinGameCode">Join</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- Snackbar for notifications -->
      <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
        {{ snackbar.text }}
        <template v-slot:action="{ attrs }">
          <v-btn text v-bind="attrs" @click="snackbar.show = false">
            Close
          </v-btn>
        </template>
      </v-snackbar>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'TicTacToe',
  
  mounted() {
    // Check if user is already logged in (via API)
    this.checkLoginStatus();
    
    // Check if the URL contains a game code (for direct joining)
    this.checkUrlForGameCode();
  },
  
  data() {
    return {
      // Auth related
      isLoggedIn: false,
      userType: null, // 'github' or 'guest'
      username: '',
      userId: null,
      userEmail: '',
      
      // Game state
      inGame: false,
      gameCode: null,
      gameMode: null, // 'human' or 'bot'
      playerSymbol: null,
      board: [
        ['', '', ''],
        ['', '', ''],
        ['', '', '']
      ],
      currentPlayer: 'X',
      winner: null,
      gameOver: false,
      movesCount: 0,
      
      // UI controls
      showGameModeDialog: false,
      showJoinDialog: false,
      joinGameCode: '',
      showSymbolDialog: false, // New dialog for selecting X or O
      selectedSymbol: null, // For storing selected symbol
      
      // Notifications
      snackbar: {
        show: false,
        text: '',
        color: 'info'
      },
      
      // API endpoints
      apiBaseUrl: 'http://localhost:8000',
      gameApiUrl: 'http://localhost:8001',
      
      // WebSocket connection
      socket: null,
    };
  },
  
  methods: {
    // Authentication methods
    async checkLoginStatus() {
      try {
        // Call backend to check authentication status
        const response = await fetch(`${this.apiBaseUrl}/auth/check-auth`, {
          method: 'GET',
          credentials: 'include', // Important for sending cookies
        });
        
        if (response.ok) {
          // User is authenticated - get user info
          await this.getUserInfo();
        } else {
          // Clear any stored session data
          this.clearUserSession();
        }
      } catch (error) {
        console.error('Error checking authentication status:', error);
        // Assume not logged in on error
        this.clearUserSession();
      }
    },
    
    async getUserInfo() {
      try {
        // Call backend to get user info
        const response = await fetch(`${this.apiBaseUrl}/users/me`, {
          method: 'GET',
          credentials: 'include',
        });
        
        if (response.ok) {
          const userData = await response.json();
          
          // Determine if GitHub user based on OAuth accounts
          const isGithubUser = userData.email && userData.email.includes('@guest.');
          
          this.isLoggedIn = true;
          this.userType = isGithubUser ? 'guest' : 'github';
          this.userEmail = userData.email;
          this.userId = userData.id;
          
          // Extract username from email or use email as username
          if (isGithubUser && userData.oauth_accounts[0].account_id) {
            // Use GitHub username if available
            this.username = userData.oauth_accounts[0].account_id;
          } else {
            // For guest users, use part of the email before @ or generate a guest name
            if (userData.oauth_accounts && userData.oauth_accounts.length > 0) {
              this.username = userData.oauth_accounts[0].account_id || 'GitHub User';
            } else {
              // Fallback to emailusername part
              this.username = userData.email.split('@')[0] || 'User';
            }
          }
        } else {
          this.clearUserSession();
        }
      } catch (error) {
        console.error('Error getting user info:', error);
        this.clearUserSession();
      }
    },
    
    async loginWithGithub() {
      try {
        // This is the correct endpoint for GitHub login based on the backend code
        const response = await fetch(`${this.apiBaseUrl}/auth/github/authorize`, {
          method: 'GET',
          credentials: 'include',
        });
    
        if (response.ok) {
          const data = await response.json();
          // Redirect to GitHub authorization URL
          window.location.href = data.authorization_url;
        } else {
          this.showNotification('Failed to get GitHub authorization URL', 'error');
        }
      } catch (error) {
        console.error('Error in GitHub login:', error);
        this.showNotification('Error connecting to server', 'error');
      }
    },

    async continueAsGuest() {
      try {
        // Call backend to create a guest user - using the correct endpoint from api.py
        const response = await fetch(`${this.apiBaseUrl}/auth/create-guest`, {
          method: 'GET',
          credentials: 'include',
        });
        
        if (response.ok) {
          // Guest user created successfully
          this.showNotification('Continuing as guest', 'info');
          // Get user info after guest creation
          await this.getUserInfo();
        } else {
          this.showNotification('Failed to create guest account', 'error');
        }
      } catch (error) {
        console.error('Error creating guest user:', error);
        this.showNotification('Error connecting to server', 'error');
      }
    },
    
    async logout() {
      try {
        // If in a game, leave it first
        if (this.inGame) {
          this.leaveGame();
        }
        
        // Call backend logout endpoint - using the correct path from main.py
        await fetch(`${this.apiBaseUrl}/auth/logout`, {
          method: 'GET',  // Changed from POST to GET based on the backend implementation
          credentials: 'include',
        });
        
        // Clear local session state
        this.clearUserSession();
        this.showNotification('Logged out successfully', 'info');
      } catch (error) {
        console.error('Error during logout:', error);
        // Clear session anyway
        this.clearUserSession();
      }
    },
    
    clearUserSession() {
      // Clear app state
      this.isLoggedIn = false;
      this.userType = null;
      this.username = '';
      this.userId = null;
      this.userEmail = '';
      
      // If in a game, leave it
      if (this.inGame) {
        this.leaveGame();
      }
    },
    
    // Check for game code in URL
    checkUrlForGameCode() {
      // Check if the URL has a game code parameter
      const urlParams = new URLSearchParams(window.location.search);
      const gameCode = urlParams.get('game');
      
      if (gameCode && this.isLoggedIn) {
        // Auto-join the game
        this.joinGameCode = gameCode;
        this.joinGame();
      } else if (gameCode && !this.isLoggedIn) {
        // Store game code for after login
        this.joinGameCode = gameCode;
        // Show a notification to log in first
        this.showNotification('Please log in to join the game', 'info');
      }
    },
    
    // UPDATED: Create New Game method
    async createNewGame(mode) {
      this.gameMode = mode;
      this.showGameModeDialog = false;
      
      // Show symbol selection dialog
      this.showSymbolDialog = true;
    },
    
    // NEW: Method to select symbol and create game
    async confirmCreateGame(symbol) {
      this.showSymbolDialog = false;
      
      try {
        // First, ensure we've properly ended any previous game
        if (this.inGame && this.gameCode) {
          this.leaveGame();
        }
        
        // Call the game API to create a new game
        const response = await fetch(`${this.gameApiUrl}/game/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: this.gameMode === 'human' ? 'multiplayer' : 'bot',
            symbol: symbol.toLowerCase() // Backend expects lowercase 'x' or 'o'
          }),
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to create game: ' + response.statusText);
        }
        
        const gameData = await response.json();
        
        // Determine player symbol
        const playerSymbol = symbol;
        
        // Initialize the game
        this.startGame(gameData.id, playerSymbol, this.gameMode);
        
        // If multiplayer game, show the invite message
        if (this.gameMode === 'human') {
          this.showNotification(`Game created! Share the Game ID: ${gameData.id} with a friend.`, 'success');
        } else {
          this.showNotification('Game against bot started!', 'success');
          
          // Connect to WebSocket for game updates
          this.connectToGameSocket(gameData.id);
        }
      } catch (error) {
        console.error('Error creating game:', error);
        this.showNotification('Error creating game: ' + error.message, 'error');
      }
    },
    
    // UPDATED: Join Game method
    async joinGame() {
      if (!this.joinGameCode) return;
      
      try {
        // Clean up input (may be full URL or just code)
        let gameId = this.joinGameCode.trim();
        
        // Check if it's a URL and extract the code
        if (gameId.includes('?game=')) {
          gameId = gameId.split('?game=')[1].split('&')[0];
        }
        
        // Call the game API to join the game
        const response = await fetch(`${this.gameApiUrl}/game/join/${gameId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to join game: ' + response.statusText);
        }
        
        const gameData = await response.json();
        
        // Determine player symbol based on the game data
        // The player who joins gets the symbol that's not taken yet
        const currentUserId = this.userId;
        let playerSymbol;
        
        if (gameData.players.x === currentUserId) {
          playerSymbol = 'X';
        } else if (gameData.players.o === currentUserId) {
          playerSymbol = 'O';
        } else {
          throw new Error('Player not found in game data');
        }
        
        // Initialize the game
        this.startGame(gameId, playerSymbol, gameData.type === 'bot' ? 'bot' : 'human');
        
        // Connect to WebSocket for game updates
        this.connectToGameSocket(gameId);
        
        this.showNotification(`Joined game successfully`, 'success');
      } catch (error) {
        console.error('Error joining game:', error);
        this.showNotification('Error joining game: ' + error.message, 'error');
      }
      
      this.showJoinDialog = false;
      this.joinGameCode = '';
    },
    
    // NEW: Connect to WebSocket for game updates
    connectToGameSocket(gameId) {
      // Close any existing socket connection
      if (this.socket) {
        this.socket.close();
      }
      
      // Create WebSocket connection
      this.socket = new WebSocket(`ws://localhost:8001/ws/game/${gameId}`);
      
      // Set up event handlers
      this.socket.onopen = () => {
        console.log('WebSocket connection established');
      };
      
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleSocketMessage(data);
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.showNotification('Error connecting to game server', 'error');
      };
      
      this.socket.onclose = () => {
        console.log('WebSocket connection closed');
      };
    },
    
    // NEW: Handle WebSocket messages
    handleSocketMessage(data) {
      if (data.type === 'game_state') {
        // Update the game state
        const gameData = data.game;
        
        // Update the board
        // Convert backend's flat array to frontend's 2D array
        for (let i = 0; i < 3; i++) {
          for (let j = 0; j < 3; j++) {
            const index = i * 3 + j;
            this.board[i][j] = gameData.board[index] ? gameData.board[index].toUpperCase() : '';
          }
        }
        
        // Update game status
        if (gameData.status === 'completed') {
          this.gameOver = true;
          if (gameData.winner === 'draw') {
            this.winner = null; // Draw
          } else if (gameData.winner) {
            this.winner = gameData.winner.toUpperCase();
          }
        }
        
        // Update current player
        if (gameData.current_player === this.userId) {
          this.currentPlayer = this.playerSymbol;
        } else {
          this.currentPlayer = this.playerSymbol === 'X' ? 'O' : 'X';
        }
        
        // Update move count
        this.movesCount = gameData.board.filter(cell => cell !== '').length;
      } else if (data.type === 'error') {
        this.showNotification(data.message, 'error');
      } else if (data.type === 'chat') {
        // Handle chat messages if needed
        console.log('Chat message:', data);
      } else if (data.type === 'player_connected' || data.type === 'player_disconnected') {
        // Handle player connection status
        console.log('Player status changed:', data);
      }
    },
    
    // UPDATED: Make Move method to work with the WebSocket connection
    makeMove(row, col) {
      // Check if the move is valid
      if (this.board[row][col] !== '' || this.gameOver) {
        return;
      }
      
      // If in a game, check if it's the player's turn
      if (this.currentPlayer !== this.playerSymbol) {
        return;
      }
      
      // Calculate position index (convert 2D index to flat index)
      const position = row * 3 + col;
      
      // Send move to server via WebSocket
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: 'move',
          position: position
        }));
      } else {
        this.showNotification('Connection to game server lost', 'error');
      }
    },
    
    // UPDATED: Start Game method
    startGame(gameId, playerSymbol, gameMode) {
      // Reset the game state
      this.resetGame();
      
      // Set up the game
      this.inGame = true;
      this.gameCode = gameId;
      this.playerSymbol = playerSymbol;
      this.gameMode = gameMode;
      
      // Connect to WebSocket
      this.connectToGameSocket(gameId);
    },
    
    // UPDATED: Leave Game method
    leaveGame() {
      // Don't do anything if not in a game
      if (!this.inGame || !this.gameCode) {
        return;
      }
      
      // Close WebSocket connection
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      
      // Clear game state before starting a new one
      this.inGame = false;
      this.gameCode = null;
      this.playerSymbol = null;
      this.gameMode = null;
      this.resetGame();
    },
    
    // Utility methods
    showNotification(text, color = 'info') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },
    
    copyGameLink() {
      if (!this.inviteLink) return;
      
      navigator.clipboard.writeText(this.inviteLink)
        .then(() => {
          this.showNotification('Invite link copied to clipboard!', 'success');
        })
        .catch(err => {
          console.error('Could not copy text: ', err);
        });
    },
    
    resetGame() {
      this.board = [
        ['', '', ''],
        ['', '', ''],
        ['', '', '']
      ];
      this.currentPlayer = 'X';
      this.winner = null;
      this.gameOver = false;
      this.movesCount = 0;
    },
    
    checkWin() {
      const board = this.board;
      const player = this.currentPlayer;
      
      // Check rows
      for (let i = 0; i < 3; i++) {
        if (board[i][0] === player && board[i][1] === player && board[i][2] === player) {
          return true;
        }
      }
      
      // Check columns
      for (let i = 0; i < 3; i++) {
        if (board[0][i] === player && board[1][i] === player && board[2][i] === player) {
          return true;
        }
      }
      
      // Check diagonals
      if (board[0][0] === player && board[1][1] === player && board[2][2] === player) {
        return true;
      }
      if (board[0][2] === player && board[1][1] === player && board[2][0] === player) {
        return true;
      }
      
      return false;
    }
  }
};
</script>

<style scoped>
.game-board {
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  max-width: 300px;
}

.game-row {
  display: flex;
}

.game-cell {
  width: 100px;
  height: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 2.5rem;
  font-weight: bold;
  cursor: pointer;
  border: 2px solid #ccc;
  transition: background-color 0.3s;
}

.game-cell:hover:not(.disabled) {
  background-color: #f5f5f5;
}

.game-cell.disabled {
  cursor: not-allowed;
}

.x-mark {
  color: #f44336; /* Red */
}

.o-mark {
  color: #2196f3; /* Blue */
}
</style>