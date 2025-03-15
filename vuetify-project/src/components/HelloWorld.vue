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
      }
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
    // Check if user is already logged in (via cookie)
    this.checkLoginStatus();
    
    // Check if the URL contains a game code (for direct joining)
    this.checkUrlForGameCode();
  },
  methods: {
    // Authentication methods
    checkLoginStatus() {
      // Check cookies for existing session
      // This would be replaced with actual cookie checking logic
      const userCookie = this.getCookie('ttt_user');
      
      if (userCookie) {
        try {
          const userData = JSON.parse(userCookie);
          this.isLoggedIn = true;
          this.userType = userData.type;
          this.username = userData.username;
          this.userId = userData.id;
        } catch (e) {
          console.error('Error parsing user cookie:', e);
          this.clearUserSession();
        }
      }
    },
    
    loginWithGithub() {
      // In a real implementation, this would redirect to GitHub OAuth flow
      // For now, we'll simulate a successful GitHub login
      
      // Redirect to GitHub login URL
      // window.location.href = '/api/auth/github';
      
      // For demo purposes, we'll simulate a successful login
      this.simulateGithubLogin();
    },
    
    simulateGithubLogin() {
      // This is just for demonstration - would be replaced with actual OAuth
      const githubUser = {
        id: 'gh_' + Math.random().toString(36).substring(2, 10),
        username: 'github_user',
        type: 'github'
      };
      
      this.setUserSession(githubUser);
      this.showNotification('Logged in with GitHub successfully', 'success');
    },
    
    continueAsGuest() {
      // Call backend to create a guest user
      this.createGuestUser();
    },
    
    createGuestUser() {
      // In a real implementation, this would call your backend
      // For now, we'll simulate a backend response
      
      // API call would be something like:
      // fetch('/api/auth/guest', {
      //   method: 'POST',
      //   credentials: 'include'
      // })
      
      // Simulate backend response
      setTimeout(() => {
        const guestUser = {
          id: 'guest_' + Math.random().toString(36).substring(2, 10),
          username: 'Guest_' + Math.floor(Math.random() * 1000),
          type: 'guest'
        };
        
        this.setUserSession(guestUser);
        this.showNotification('Continuing as guest', 'info');
      }, 300);
    },
    
    setUserSession(userData) {
      // Set user data in the app state
      this.isLoggedIn = true;
      this.userType = userData.type;
      this.username = userData.username;
      this.userId = userData.id;
      
      // Set cookie to persist the session
      this.setCookie('ttt_user', JSON.stringify(userData), 7); // 7 days expiry
    },
    
    logout() {
      // Clear user session
      this.clearUserSession();
      this.showNotification('Logged out successfully', 'info');
    },
    
    clearUserSession() {
      // Clear app state
      this.isLoggedIn = false;
      this.userType = null;
      this.username = '';
      this.userId = null;
      
      // Delete cookies
      this.deleteCookie('ttt_user');
      
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
        fetch('http://localhost:5000/api/bot/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            userId: this.userId || 'guest_' + Math.random().toString(36).substring(2, 10),
            difficulty: 'hard' // You could add a difficulty selector in your UI
          })
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
    },
    
    // Cookie handling methods
    setCookie(name, value, days) {
      let expires = '';
      if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
      }
      document.cookie = name + '=' + (value || '') + expires + '; path=/';
    },
    
    getCookie(name) {
      const nameEQ = name + '=';
      const ca = document.cookie.split(';');
      for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
      }
      return null;
    },
    
    deleteCookie(name) {
      document.cookie = name + '=; Max-Age=-99999999; path=/';
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