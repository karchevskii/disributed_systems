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
                  
                  <!-- Create New Game -->
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
                          :class="{ 'disabled': cell !== '' || gameOver || (gameCode && currentPlayer !== playerSymbol) }"
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
                  <!-- MODIFIED: Only show "Back to Menu" button when game is over -->
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
      
      <!-- Join Game Dialog -->
      <v-dialog v-model="showJoinDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Join a Game</v-card-title>

          <!-- Textfield for Game-Code -->
          <v-card-text>
            <v-form @submit.prevent="joinGame">
              <v-text-field
                label="Game Code"
                v-model="joinGameCode"
                prepend-icon="mdi-pound"
                placeholder="Enter game code or paste invite link"
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
      
      // Notifications
      snackbar: {
        show: false,
        text: '',
        color: 'info'
      },
      
      // API endpoints
      apiBaseUrl: 'http://localhost:8000'
    };
  },
  computed: {
    gameStatus() {
      if (this.winner) {
        return `Player ${this.winner} wins!`;
      } else if (this.gameOver) {
        return "It's a draw!";
      } else if (this.gameCode && this.currentPlayer !== this.playerSymbol) {
        return `Waiting for opponent...`;
      } else {
        return `Your turn (${this.currentPlayer})`;
      }
    },
    
    // Generate the full invite link for the current game
    inviteLink() {
      if (!this.gameCode) return null;
      return `${window.location.origin}${window.location.pathname}?game=${this.gameCode}`;
    }
  },
  mounted() {
    // Check if user is already logged in (via API)
    this.checkLoginStatus();
    
    // Check if the URL contains a game code (for direct joining)
    this.checkUrlForGameCode();
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
          
          // Determine if GitHub user or guest based on email format
          const isGuestUser = userData.email && userData.email.includes('@guest.');
          
          this.isLoggedIn = true;
          this.userType = isGuestUser ? 'guest' : 'github';
          this.userEmail = userData.email;
          this.userId = userData.id;
          
          if (isGuestUser) {
            // For guest users, generate a friendly guest name
            const randomId = Math.floor(Math.random() * 1000);
            this.username = `Guest_${randomId}`;
          } else {
            // For GitHub users, use GitHub account_id from oauth_accounts if available
            if (userData.oauth_accounts && userData.oauth_accounts.length > 0) {
              this.username = userData.oauth_accounts[0].account_id || 'GitHub User';
            } else {
              // Fallback to email username part
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
          // Hier leiten wir zur GitHub-Autorisierungs-URL weiter
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
    
    // Game management methods
    createNewGame(mode) {
      this.gameMode = mode;
      this.showGameModeDialog = false;
      
      // First, ensure we've properly ended any previous game
      if (this.inGame && this.gameCode) {
        this.leaveGame();
      }
      
      if (mode === 'human') {
        // Call matchmaking service to create a new human vs human game
        // This would be an API call to your matchmaking microservice
        
        // Simulate response from matchmaking service
        setTimeout(() => {
          const gameCode = Math.random().toString(36).substring(2, 8).toUpperCase();
          
          // Initialize game
          this.startGame(gameCode, 'X', 'human'); // Creator plays as X
          this.showNotification(`Game created! Share the invite link with a friend.`, 'success');
        }, 300);
      } else if (mode === 'bot') {
        // Reset game state before creating a new one
        this.resetGame();
        
        // Call bot microservice API to create a new game against the bot
        fetch('http://localhost:5000/game/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: "bot",
            symbol: chosenSymbol,
            userId: this.userId || 'guest_' + Math.random().toString(36).substring(2, 10),
            difficulty: 'hard'
          }),
          credentials: 'include'
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
          }
          return response.json();
        })
        .then(data => {
          if (data.game) {
            // Initialize game with data from the server
            this.startGame(data.game.id, data.game.humanSymbol, 'bot');
            // Update the board state in case the bot went first
            this.board = data.game.board;
            this.currentPlayer = data.game.currentPlayer;
            this.showNotification('Starting game against bot', 'success');
          } else {
            this.showNotification('Failed to start game', 'error');
          }
        })
        .catch(error => {
          console.error('Error starting bot game:', error);
          this.showNotification('Error connecting to game server: ' + error.message, 'error');
        });
      }
    },
    
    joinGame() {
      if (!this.joinGameCode) return;
      
      // Clean up input (may be full URL or just code)
      let code = this.joinGameCode.trim();
      
      // Check if it's a URL and extract the code
      if (code.includes('?game=')) {
        code = code.split('?game=')[1].split('&')[0];
      }
      
      // Call matchmaking service to join the game
      // Example API call:
      // fetch(`/api/matchmaking/join/${code}`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ userId: this.userId }),
      //   credentials: 'include'
      // })
      
      // Determine if joining a bot game or human game based on code prefix
      const isJoiningBotGame = code.startsWith('BOT');
      const gameMode = isJoiningBotGame ? 'bot' : 'human';
      
      // Simulate joining
      setTimeout(() => {
        // In a real implementation, verify the game exists
        this.startGame(code, 'O', gameMode); // Joiner plays as O
        this.showNotification(`Joined game successfully`, 'success');
      }, 300);
      
      this.showJoinDialog = false;
      this.joinGameCode = '';
    },
    
    startGame(gameCode, playerSymbol, gameMode) {
      // Reset the game state
      this.resetGame();
      
      // Set up the multiplayer game
      this.inGame = true;
      this.gameCode = gameCode;
      this.playerSymbol = playerSymbol;
      this.gameMode = gameMode;
      
      // In a real implementation, you would set up WebSocket connection here
      // to receive moves from the opponent or bot
      
      // If playing against a bot and bot goes first (player is O), simulate bot move
      if (gameMode === 'bot' && playerSymbol === 'O') {
        this.simulateBotMove();
      }
    },
    
    leaveGame() {
      // Don't do anything if not in a game
      if (!this.inGame || !this.gameCode) {
        return;
      }
      
      // In a real implementation, notify the appropriate service
      if (this.gameMode === 'human') {
        // Notify matchmaking service
        // fetch(`/api/matchmaking/leave/${this.gameCode}`, { 
        //   method: 'POST'
        // })
      } else if (this.gameMode === 'bot') {
        // Notify bot service
        fetch(`http://localhost:5000/api/bot/leave/${this.gameCode}`, { 
          method: 'POST'
        })
        .catch(error => {
          console.error('Error leaving game:', error);
        });
      }
      
      // Clear game state before starting a new one
      this.inGame = false;
      this.gameCode = null;
      this.playerSymbol = null;
      this.gameMode = null;
      this.resetGame();
    },
    
    makeMove(row, col) {
      // Check if the move is valid
      if (this.board[row][col] !== '' || this.gameOver) {
        return;
      }
      
      // If in a multiplayer game, check if it's the player's turn
      if (this.gameCode && this.currentPlayer !== this.playerSymbol) {
        return;
      }
      
      // Make the move
      this.board[row][col] = this.currentPlayer;
      this.movesCount++;
      
      // Send move to appropriate service
      if (this.gameMode === 'human') {
        // Send move to human opponent via matchmaking service
        // fetch(`/api/matchmaking/move/${this.gameCode}`, {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({ row, col, player: this.currentPlayer })
        // })
      } else if (this.gameMode === 'bot') {
        // Send move to bot service
        fetch(`http://localhost:5000/api/bot/move/${this.gameCode}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ row, col, player: this.currentPlayer })
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
          }
          return response.json();
        })
        .then(data => {
          if (data.game) {
            // Update the game state with the server's response
            this.board = data.game.board;
            this.currentPlayer = data.game.currentPlayer;
            
            if (data.game.gameOver) {
              this.gameOver = true;
              this.winner = data.game.winner;
            }
          } else {
            this.showNotification('Error processing move: ' + (data.error || 'Unknown error'), 'error');
          }
        })
        .catch(error => {
          console.error('Error making move:', error);
          this.showNotification('Error connecting to game server: ' + error.message, 'error');
        });
      }
      
      // Check for win
      if (this.checkWin()) {
        this.winner = this.currentPlayer;
        this.gameOver = true;
        return;
      }
      
      // Check for draw
      if (this.movesCount === 9) {
        this.gameOver = true;
        return;
      }
      
      // Switch player
      this.currentPlayer = this.currentPlayer === 'X' ? 'O' : 'X';
      
      // If playing against bot and it's the bot's turn, simulate bot move
      if (this.gameMode === 'bot' && this.currentPlayer !== this.playerSymbol && !this.gameOver) {
        this.simulateBotMove();
      }
    },
    
    simulateBotMove() {
      // This is a placeholder function for demonstrating the frontend
      // In a real implementation, the bot's move would come from the backend
      
      // Simulate thinking time
      setTimeout(() => {
        // Find an empty cell randomly
        let emptyCells = [];
        for (let i = 0; i < 3; i++) {
          for (let j = 0; j < 3; j++) {
            if (this.board[i][j] === '') {
              emptyCells.push({row: i, col: j});
            }
          }
        }
        
        if (emptyCells.length > 0) {
          // Choose a random empty cell
          const randomIndex = Math.floor(Math.random() * emptyCells.length);
          const { row, col } = emptyCells[randomIndex];
          
          // Make the bot's move
          this.board[row][col] = this.currentPlayer;
          this.movesCount++;
          
          // Check for win
          if (this.checkWin()) {
            this.winner = this.currentPlayer;
            this.gameOver = true;
            return;
          }
          
          // Check for draw
          if (this.movesCount === 9) {
            this.gameOver = true;
            return;
          }
          
          // Switch player back to human
          this.currentPlayer = this.currentPlayer === 'X' ? 'O' : 'X';
        }
      }, 1000);
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
    
    // URL handling methods
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
    
    // Utility methods
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
    
    showNotification(text, color = 'info') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
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