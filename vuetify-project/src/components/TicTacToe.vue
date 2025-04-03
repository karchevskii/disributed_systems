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
                <game-board 
                  :board="board" 
                  :gameOver="gameOver" 
                  :currentPlayer="currentPlayer"
                  :playerSymbol="playerSymbol"
                  @make-move="makeMove"
                />
                
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
      
      <!-- Import Dialogs Component -->
      <game-dialogs
        :showGameModeDialog="showGameModeDialog"
        :showSymbolDialog="showSymbolDialog"
        :showJoinDialog="showJoinDialog"
        :joinGameCode="joinGameCode"
        @update:showGameModeDialog="showGameModeDialog = $event"
        @update:showSymbolDialog="showSymbolDialog = $event"
        @update:showJoinDialog="showJoinDialog = $event"
        @update:joinGameCode="joinGameCode = $event"
        @create-new-game="createNewGame"
        @confirm-create-game="confirmCreateGame"
        @join-game="joinGame"
      />
      
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
import GameBoard from './GameBoard.vue';
import GameDialogs from './GameDialogs.vue';
import GameService from './GameService.js';

export default {
  name: 'TicTacToe',
  components: {
    GameBoard,
    GameDialogs
  },
  
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
      
      // Create an instance of GameService
      gameService: null,
    };
  },
  
  computed: {
    gameStatus() {
      if (this.gameOver) {
        if (this.winner) {
          return this.winner === this.playerSymbol ? 'You won!' : 'You lost!';
        } else {
          return 'It\'s a draw!';
        }
      } else {
        return this.currentPlayer === this.playerSymbol ? 'Your turn' : 'Opponent\'s turn';
      }
    },
    
    inviteLink() {
      if (this.gameCode && this.gameMode === 'human') {
        return `${window.location.origin}${window.location.pathname}?game=${this.gameCode}`;
      }
      return null;
    }
  },
  
  created() {
    // Initialize GameService
    this.gameService = new GameService(
      'http://localhost:8000',
      'http://localhost:8001',
      this.handleSocketMessage.bind(this),
      this.showNotification.bind(this)
    );
  },
  
  methods: {
    // Authentication methods
    async checkLoginStatus() {
      try {
        const isAuthenticated = await this.gameService.checkAuthStatus();
        
        if (isAuthenticated) {
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
        const userData = await this.gameService.getUserInfo();
        
        this.isLoggedIn = true;
        this.userId = userData.id;
        this.userEmail = userData.email || '';
        
        // Determine user type and username
        if (userData.email && userData.email.includes('@guest.')) {
          this.userType = 'guest';
          // For guests, use the part of the email before @
          this.username = userData.email.split('@')[0] || 'Guest';
        } else {
          // GitHub user
          this.userType = 'github';
          
          // Try to get the GitHub username
          if (userData.oauth_accounts && userData.oauth_accounts.length > 0) {
            this.username = userData.oauth_accounts[0].account_id || 'GitHub User';
          } else {
            // Fallback
            this.username = userData.email ? userData.email.split('@')[0] : 'User';
          }
        }
      } catch (error) {
        console.error('Error getting user info:', error);
        this.clearUserSession();
      }
    },
    
    async loginWithGithub() {
      try {
        const authUrl = await this.gameService.getGithubAuthUrl();
        window.location.href = authUrl;
      } catch (error) {
        console.error('Error in GitHub login:', error);
        this.showNotification('Error connecting to server', 'error');
      }
    },

    async continueAsGuest() {
      try {
        const success = await this.gameService.createGuestUser();
        
        if (success) {
          this.showNotification('Continuing as guest', 'info');
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
        
        await this.gameService.logout();
        
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
    
    // Game methods
    async createNewGame(mode) {
      this.gameMode = mode;
      this.showGameModeDialog = false;
      
      // Show symbol selection dialog
      this.showSymbolDialog = true;
    },
    
    async confirmCreateGame(symbol) {
      this.showSymbolDialog = false;
      
      try {
        // First, ensure we've properly ended any previous game
        if (this.inGame && this.gameCode) {
          this.leaveGame();
        }
        
        const gameData = await this.gameService.createGame(this.gameMode, symbol);
        
        // Initialize the game
        this.startGame(gameData.id, symbol, this.gameMode);
        
        // If multiplayer game, show the invite message
        if (this.gameMode === 'human') {
          this.showNotification(`Game created! Share the Game ID: ${gameData.id} with a friend.`, 'success');
        } else {
          this.showNotification('Game against bot started!', 'success');
        }
      } catch (error) {
        console.error('Error creating game:', error);
        this.showNotification('Error creating game: ' + error.message, 'error');
      }
    },
    
    async joinGame() {
      if (!this.joinGameCode) return;
      
      try {
        // Clean up input (may be full URL or just code)
        let gameId = this.joinGameCode.trim();
        
        // Check if it's a URL and extract the code
        if (gameId.includes('?game=')) {
          gameId = gameId.split('?game=')[1].split('&')[0];
        }
        
        const gameData = await this.gameService.joinGame(gameId);
        
        // Determine player symbol based on the game data
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
        
        this.showNotification(`Joined game successfully`, 'success');
      } catch (error) {
        console.error('Error joining game:', error);
        this.showNotification('Error joining game: ' + error.message, 'error');
      }
      
      this.showJoinDialog = false;
      this.joinGameCode = '';
    },
    
    // Handle WebSocket messages
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
      }
    },
    
    // Make Move method
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
      this.gameService.sendMove(position);
    },
    
    // Start Game method
    startGame(gameId, playerSymbol, gameMode) {
      // Reset the game state
      this.resetGame();
      
      // Set up the game
      this.inGame = true;
      this.gameCode = gameId;
      this.playerSymbol = playerSymbol;
      this.gameMode = gameMode;
      
      // Connect to WebSocket
      this.gameService.connectToGameSocket(gameId);
    },
    
    // Leave Game method
    leaveGame() {
      // Don't do anything if not in a game
      if (!this.inGame || !this.gameCode) {
        return;
      }
      
      // Close WebSocket connection
      this.gameService.closeSocket();
      
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
    }
  }
};
</script>