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
                  
                  <!-- Browse Open Games -->
                  <v-btn 
                    color="info" 
                    class="mb-3" 
                    block 
                    @click="showOpenGamesDialog = true"
                  >
                    <v-icon left>mdi-format-list-bulleted</v-icon>
                    Browse Open Games
                  </v-btn>
                  
                  <!-- View Game History -->
                  <v-btn 
                    color="success" 
                    class="mb-3" 
                    block 
                    @click="showGameHistoryDialog = true"
                  >
                    <v-icon left>mdi-history</v-icon>
                    View Game History
                  </v-btn>
                </div>
              </div>
              
              <!-- Game View (when in a game) -->
              <div v-else>
                <!-- Game Info - Simplified based on game mode -->
                <div class="d-flex justify-space-between align-center mb-3">
                  <div>
                    <!-- Opponent icon (Human/Bot) -->
                    <v-chip :color="gameMode === 'bot' ? 'info' : 'warning'" small>
                      <v-icon left small>{{ gameMode === 'bot' ? 'mdi-robot' : 'mdi-account' }}</v-icon>
                      {{ gameMode === 'bot' ? 'Bot' : 'Multiplayer' }}
                    </v-chip>
                  </div>
                  
                  <!-- For multiplayer games, show copy ID button -->
                  <v-btn 
                    v-if="gameMode === 'human'"
                    small
                    outlined
                    color="primary"
                    @click="copyGameId"
                  >
                    <v-icon left small>mdi-content-copy</v-icon>
                    Copy Game ID
                  </v-btn>
                </div>
                
                <!-- Game/Turn Status with improved styling -->
                <v-card-subtitle class="text-center text-h6 mb-2">
                  <span>{{ gameStatus }}</span>
                </v-card-subtitle>
                
                <!-- Game Board -->
                <game-board 
                  :board="board" 
                  :gameOver="gameOver" 
                  :currentPlayer="currentPlayer"
                  :playerSymbol="playerSymbol"
                  @make-move="makeMove"
                />
                
                <!-- Chat Component -->
                <game-chat
                  ref="gameChat"
                  :playerSymbol="playerSymbol"
                  :gameMode="gameMode"
                  class="mt-4"
                  @send-message="sendChatMessage"
                />
                
                <!-- Game Control Buttons -->
                <div class="text-center mt-4">
                  <!-- Only show "Back to Menu" button when game is over -->
                  <v-btn v-if="gameOver" color="success" @click="leaveGame">
                    <v-icon left>mdi-exit-to-app</v-icon>
                    Back to Menu
                  </v-btn>
                  
                  <!-- In-progress game controls -->
                  <template v-if="!gameOver">
                    <!-- Leave Game button -->
                    <v-btn color="error" @click="leaveGame">
                      <v-icon left>mdi-exit-to-app</v-icon>
                      {{ gameMode === 'human' ? 'Forfeit Game' : 'Leave Game' }}
                    </v-btn>
                  </template>
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

      <!-- Import Open Games Dialog -->
      <open-games-dialog
        :showOpenGamesDialog="showOpenGamesDialog"
        :openGames="openGames"
        :loading="loadingOpenGames"
        :error="openGamesError"
        @update:showOpenGamesDialog="showOpenGamesDialog = $event"
        @refresh-open-games="fetchOpenGames"
        @join-open-game="joinOpenGame"
      />

      <!-- Import Game History Dialog -->
      <game-history
        :showGameHistoryDialog="showGameHistoryDialog"
        :gameHistoryApiUrl="gameService ? gameService.gameHistoryApiUrl : ''"
        :userId="userId"
        @update:showGameHistoryDialog="showGameHistoryDialog = $event"
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
import OpenGamesDialog from './OpenGamesDialog.vue';
import GameChat from './GameChat.vue';
import GameHistory from './GameHistory.vue';
import GameService from './GameService.js';

export default {
  name: 'TicTacToe',
  components: {
    OpenGamesDialog,
    GameBoard,
    GameDialogs,
    GameChat,
    GameHistory
  },
  
  mounted() {
    // Check if user is already logged in (via API)
    this.checkLoginStatus();
    
    // Check if the URL contains a game code (for direct joining)
    this.checkUrlForGameCode();
    
    // Add beforeUnload handler for page exit warning
    window.addEventListener('beforeunload', this.handleBeforeUnload);
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
      gameStatusText: null,  // Custom status text for disconnections
      
      // UI controls
      showGameModeDialog: false,
      showJoinDialog: false,
      joinGameCode: '',
      showSymbolDialog: false, // New dialog for selecting X or O

      // Game history
      showGameHistoryDialog: false,

      // Open games
      showOpenGamesDialog: false,
      openGames: [],
      loadingOpenGames: false,
      openGamesError: '',
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
      // If we have custom status text, use that
      if (this.gameStatusText) {
        return this.gameStatusText;
      }
      
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
    const apiBaseUrl = 'http://tictactoe.local/users-service';
    const gameApiUrl = 'http://tictactoe.local/game-service';
    
    // Store API URLs for direct access in component methods
    this.apiBaseUrl = apiBaseUrl;
    this.gameApiUrl = gameApiUrl;
    this.gameService = new GameService(
      'http://tictactoe.local/users-service',
      'http://tictactoe.local/game-service',
      this.handleSocketMessage.bind(this),
      this.showNotification.bind(this)
    );
  },

  watch: {
    // Fetch open games when dialog is opened
    showOpenGamesDialog(newVal) {
      if (newVal === true) this.fetchOpenGames();
    }
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
          // For guests, use a shorter name format: Guest + last 4 chars of ID
          const shortId = userData.id.substring(userData.id.length - 4);
          this.username = `Guest${shortId}`;
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
    
    // Open Games methods
    async fetchOpenGames() {
      if (!this.isLoggedIn) return;
      
      this.loadingOpenGames = true;
      this.openGamesError = '';
      
      try {
        // Use Fetch API to get open games from backend
        const response = await fetch(`${this.gameService.gameApiUrl}/games/open`, {
          method: 'GET',
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch open games: ${response.statusText}`);
        }
        
        const data = await response.json();
        this.openGames = data;
      } catch (error) {
        console.error('Error fetching open games:', error);
        this.openGamesError = error.message || 'Failed to fetch open games';
      } finally {
        this.loadingOpenGames = false;
      }
    },
    
    async joinOpenGame(gameId) {
      try {
        const gameData = await this.gameService.joinGame(gameId);
        
        // Determine player symbol from game data
        const playerSymbol = gameData.players.x === this.userId ? 'X' : 'O';
        
        // Start the game
        this.startGame(gameId, playerSymbol, 'human');
        
        this.showOpenGamesDialog = false;
        this.showNotification('Successfully joined game!', 'success');
      } catch (error) {
        console.error('Error joining open game:', error);
        this.showNotification('Error joining game: ' + error.message, 'error');
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
          this.showNotification(`Game created! Use the Copy Game ID button to share with a friend.`, 'success');
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
    
    // Chat methods
    sendChatMessage(message) {
      if (!this.inGame) return;
      
      // Send the chat message through WebSocket
      this.gameService.sendChatMessage(message);
    },
    
    // Handle WebSocket messages
    handleSocketMessage(data) {
      if (data.type === 'game_state') {
        // Update the game state
        const gameData = data.game;
        
        // Debug logs
        console.log("Game data received:", gameData);
        console.log("Current player ID from server:", gameData.current_player);
        console.log("My user ID:", this.userId);
        console.log("My player symbol:", this.playerSymbol);
        
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
          console.log("Setting currentPlayer to my symbol:", this.playerSymbol);
        } else if (gameData.current_player === 'bot') {
          this.currentPlayer = this.playerSymbol === 'X' ? 'O' : 'X';
          console.log("Setting currentPlayer for bot game");
        } else {
          this.currentPlayer = this.playerSymbol === 'X' ? 'O' : 'X';
          console.log("Setting currentPlayer to opponent's symbol");
        }
        console.log("Current player after update:", this.currentPlayer);
        
        // Update move count
        this.movesCount = gameData.board.filter(cell => cell !== '').length;
        
        // Update game status display
        this.updateGameStatusDisplay(gameData);
      } else if (data.type === 'chat') {
        // Handle chat messages
        if (this.$refs.gameChat) {
          this.$refs.gameChat.addMessage({
            sender: data.sender.toUpperCase(),
            message: data.message
          });
        }
      } else if (data.type === 'connection_status') {
        // Just show a notification if connection is lost
        if (data.status === 'disconnected' && this.inGame && !this.gameOver) {
          this.showNotification('Disconnected from game server.', 'error');
        }
      } else if (data.type === 'error') {
        this.showNotification(data.message, 'error');
      }
    },
    
    // Updated game status display based on backend data
    updateGameStatusDisplay(gameData) {
      // Check if there was a timeout or disconnection
      if (gameData.status === 'completed' && gameData.moves && gameData.moves.length > 0) {
        const lastMove = gameData.moves[gameData.moves.length - 1];
        
        if (lastMove.action === 'disconnect' || lastMove.action === 'disconnect_timeout') {
          if (this.winner === this.playerSymbol) {
            this.gameStatusText = 'You won! (Opponent disconnected)';
          } else {
            this.gameStatusText = 'You lost! (Disconnected from game)';
          }
          return;
        }
      }
      
      // Default status text (use computed property)
      this.gameStatusText = null;
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
      this.gameStatusText = null;
      
      // Connect to WebSocket
      this.gameService.connectToGameSocket(gameId);
      
      // Update the page URL with the game ID for multiplayer games
      if (gameMode === 'human') {
        const url = new URL(window.location.href);
        url.searchParams.set('game', gameId);
        window.history.replaceState({}, '', url.toString());
      }
    },
    
    // Leave Game method
    leaveGame() {
      // Don't do anything if not in a game
      if (!this.inGame || !this.gameCode) {
        return;
      }
      
      // Show a confirmation dialog if the game is active
      if (!this.gameOver && this.gameMode === 'human') {
        if (!confirm('Are you sure you want to leave? You will forfeit the game.')) {
          return;
        }
      }
      
      // Close WebSocket connection
      this.gameService.closeSocket();
      
      // Clear game state before starting a new one
      this.inGame = false;
      this.gameCode = null;
      this.playerSymbol = null;
      this.gameMode = null;
      this.gameStatusText = null;
      this.resetGame();
      
      // Clear game parameter from URL
      const url = new URL(window.location.href);
      url.searchParams.delete('game');
      window.history.replaceState({}, '', url.toString());
    },
    
    handleBeforeUnload(event) {
      if (this.inGame && !this.gameOver && this.gameMode === 'human') {
        // Standard way to show a confirmation dialog when leaving the page
        const message = 'Leaving this page will forfeit the game. Are you sure?';
        event.returnValue = message;
        return message;
      }
    },
    
    // Utility methods
    showNotification(text, color = 'info') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },
    
    copyGameId() {
      if (!this.gameCode) {
        console.error('No game code available to copy');
        return;
      }
      
      // Try using clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(this.gameCode)
          .then(() => {
            this.showNotification('Game ID copied to clipboard!', 'success');
          })
          .catch(err => {
            console.error('Could not copy text with clipboard API:', err);
            this.fallbackCopy(this.gameCode);
          });
      } else {
        // Fallback for browsers that don't support clipboard API
        this.fallbackCopy(this.gameCode);
      }
    },
    
    fallbackCopy(text) {
      // Create temporary element
      const textArea = document.createElement('textarea');
      textArea.value = text;
      
      // Make it invisible
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      
      // Select and copy
      textArea.focus();
      textArea.select();
      
      let success = false;
      try {
        success = document.execCommand('copy');
      } catch (err) {
        console.error('Fallback copy failed:', err);
      }
      
      // Clean up
      document.body.removeChild(textArea);
      
      if (success) {
        this.showNotification('Game ID copied to clipboard!', 'success');
      } else {
        this.showNotification('Failed to copy game ID. Game ID: ' + this.gameCode, 'error');
      }
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
      
      // Clear chat messages if chat component exists
      if (this.$refs.gameChat) {
        this.$refs.gameChat.messages = [];
      }
    }
  },
  
  beforeDestroy() {
    // Remove beforeUnload handler
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    
    // Close any active WebSocket connections
    if (this.gameService) {
      this.gameService.closeSocket();
    }
  }
};
</script>