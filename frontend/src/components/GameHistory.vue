<template>
  <v-dialog v-model="showGameHistoryDialogLocal" max-width="700">
    <v-card>
      <v-card-title class="text-h5">
        Game History
        <v-spacer></v-spacer>
        <v-btn icon @click="refreshGameHistory">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-alert v-if="loading" type="info" text>
          Loading game history...
        </v-alert>
        
        <v-alert v-else-if="error" type="error" text>
          {{ error }}
        </v-alert>
        
        <v-alert v-else-if="games.length === 0" type="info" text>
          No game history available. Play some games first!
        </v-alert>

        <v-data-table
          v-else
          :headers="headers"
          :items="games"
          :items-per-page="5"
          class="elevation-1"
        >
          <template v-slot:item.game_type="{ item }">
            <v-chip
              :color="item.game_type === 'bot' ? 'info' : 'warning'"
              x-small
            >
              <v-icon left x-small>{{ item.game_type === 'bot' ? 'mdi-robot' : 'mdi-account-multiple' }}</v-icon>
              {{ item.game_type === 'bot' ? 'Bot' : 'Multiplayer' }}
            </v-chip>
          </template>

          <template v-slot:item.winner="{ item }">
            <span v-if="item.winner === 'draw'">Draw</span>
            <v-chip
              v-else-if="item.winner === userId"
              color="success"
              x-small
            >
              Victory
            </v-chip>
            <v-chip
              v-else
              color="error"
              x-small
            >
              Defeat
            </v-chip>
          </template>

          <template v-slot:item.created_at="{ item }">
            {{ formatDate(item.created_at) }}
          </template>

          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              x-small
              color="primary"
              @click="viewGameDetails(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="grey" text @click="showGameHistoryDialogLocal = false">Close</v-btn>
      </v-card-actions>
    </v-card>

    <!-- Game Details Dialog with Replay Feature -->
    <v-dialog v-model="showGameDetailsDialog" max-width="600">
      <v-card v-if="selectedGame">
        <v-card-title class="text-h5">
          Game Replay
        </v-card-title>

        <v-card-text>
          <!-- Game Information -->
          <v-row>
            <v-col cols="12" sm="6">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>Game Type</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ selectedGame.game_type === 'bot' ? 'vs Bot' : 'Multiplayer' }}
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>
            <v-col cols="12" sm="6">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>Result</v-list-item-title>
                  <v-list-item-subtitle>
                    <span v-if="selectedGame.winner === 'draw'">Draw</span>
                    <span v-else-if="selectedGame.winner === userId">Victory</span>
                    <span v-else>Defeat</span>
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>
          </v-row>

          <!-- Show Your Symbol -->
          <div class="d-flex justify-center align-center my-3">
            <v-chip 
              :color="playerSymbolInGame === 'x' ? 'red' : 'blue'" 
              dark
              class="font-weight-bold"
            >
              You played as {{ playerSymbolInGame.toUpperCase() }}
            </v-chip>
          </div>

          <!-- Current Move Display -->
          <div class="text-center mb-3">
            <h3 class="text-subtitle-1">
              {{ currentMoveIndex === -1 ? 'Starting Board' : 
                 currentMoveIndex === replayMoves.length ? 'Final Position' : 
                 `Move ${currentMoveIndex + 1} of ${replayMoves.length}` }}
            </h3>
          </div>

          <!-- Game Board for Replay -->
          <div class="game-board-replay">
            <div class="game-board-row" v-for="(_, rowIndex) in 3" :key="'row-' + rowIndex">
              <div
                class="game-board-cell"
                v-for="(_, colIndex) in 3"
                :key="'cell-' + rowIndex + '-' + colIndex"
              >
                <span v-if="getReplayBoardCell(rowIndex, colIndex) === 'x'" class="x-mark">X</span>
                <span v-else-if="getReplayBoardCell(rowIndex, colIndex) === 'o'" class="o-mark">O</span>
              </div>
            </div>
          </div>

          <!-- Replay Controls -->
          <div class="d-flex justify-center align-center mt-4">
            <v-btn icon color="primary" @click="moveToStart" :disabled="currentMoveIndex === -1">
              <v-icon>mdi-skip-backward</v-icon>
            </v-btn>
            
            <v-btn icon color="primary" @click="movePrevious" :disabled="currentMoveIndex === -1">
              <v-icon>mdi-step-backward</v-icon>
            </v-btn>
            
            <v-btn 
              icon 
              :color="isPlaying ? 'error' : 'success'" 
              @click="togglePlayback"
              :disabled="currentMoveIndex === replayMoves.length"
            >
              <v-icon>{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
            </v-btn>
            
            <v-btn icon color="primary" @click="moveNext" :disabled="currentMoveIndex === replayMoves.length">
              <v-icon>mdi-step-forward</v-icon>
            </v-btn>
            
            <v-btn icon color="primary" @click="moveToEnd" :disabled="currentMoveIndex === replayMoves.length">
              <v-icon>mdi-skip-forward</v-icon>
            </v-btn>
          </div>

          <!-- Move Speed Control -->
          <div class="d-flex align-center mt-2 px-4">
            <span class="pr-2">Speed:</span>
            <v-slider
              v-model="playbackSpeed"
              min="1"
              max="10"
              thumb-label
              dense
              hide-details
            ></v-slider>
          </div>

          <!-- Current Move Info -->
          <v-card v-if="currentMoveIndex >= 0 && currentMoveIndex < replayMoves.length" outlined class="mt-4">
            <v-card-text>
              <strong>{{ getPlayerName(replayMoves[currentMoveIndex].player) }}</strong> placed 
              <span :class="replayMoves[currentMoveIndex].symbol === 'x' ? 'x-mark' : 'o-mark'">
                {{ replayMoves[currentMoveIndex].symbol.toUpperCase() }}
              </span> 
              at position ({{ Math.floor(replayMoves[currentMoveIndex].position / 3) }}, 
              {{ replayMoves[currentMoveIndex].position % 3 }})
            </v-card-text>
          </v-card>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="closeGameDetails">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script>
export default {
  name: 'GameHistory',
  props: {
    showGameHistoryDialog: {
      type: Boolean,
      default: false
    },
    gameHistoryApiUrl: {
      type: String,
      required: true
    },
    userId: {
      type: String,
      required: true
    }
  },
  
  data() {
    return {
      games: [],
      loading: false,
      error: '',
      showGameDetailsDialog: false,
      selectedGame: null,
      currentMoveIndex: -1,
      replayBoard: Array(9).fill(''),
      replayMoves: [],
      playbackInterval: null,
      isPlaying: false,
      playbackSpeed: 5,
      playerSymbolInGame: 'x',
      headers: [
        { text: 'Type', value: 'game_type' },
        { text: 'Result', value: 'winner' },
        { text: 'Date', value: 'created_at' },
        { text: 'Actions', value: 'actions', sortable: false }
      ]
    };
  },
  
  computed: {
    showGameHistoryDialogLocal: {
      get() {
        return this.showGameHistoryDialog;
      },
      set(value) {
        this.$emit('update:showGameHistoryDialog', value);
      }
    },
    playbackDelay() {
      // Convert speed (1-10) to milliseconds (2000ms to 200ms)
      return 2200 - (this.playbackSpeed * 200);
    }
  },
  
  methods: {
    async refreshGameHistory() {
      this.loading = true;
      this.error = '';
      
      try {
        // Direct fetch using the API URL from props
        const response = await fetch(`${this.gameHistoryApiUrl}/games`, {
          method: 'GET',
          credentials: 'include'
        });
        
        // If API returns an error response, check if it's 404 (no games yet)
        if (!response.ok) {
          if (response.status === 404) {
            // No games yet, not an error
            this.games = [];
          } else {
            console.error(`Game history API error: ${response.status}`);
            this.error = `Failed to fetch game history: ${response.statusText}`;
          }
          return;
        }
        
        // Get the raw text
        const responseText = await response.text();
        
        // If response is empty
        if (!responseText.trim()) {
          this.games = [];
          return;
        }
        
        // Try to parse the JSON
        try {
          const data = JSON.parse(responseText);
          
          if (!data || !data.games || !Array.isArray(data.games)) {
            console.error("Invalid data format:", data);
            this.games = [];
            return;
          }
          
          console.log("Game history data:", data.games);
          
          // Process the games
          this.games = data.games.map(game => {
            // Ensure the board is always an array of 9 items
            if (!Array.isArray(game.board) || game.board.length !== 9) {
              game.board = Array(9).fill('');
            }
            
            // Normalize the moves array
            if (!Array.isArray(game.moves)) {
              game.moves = [];
            }
            
            return game;
          });
        } catch (parseError) {
          console.error('Error parsing JSON:', parseError);
          console.log('Raw response:', responseText);
          this.error = 'Error parsing game history data';
          this.games = [];
        }
      } catch (error) {
        console.error('Error fetching game history:', error);
        this.error = error.message || 'Failed to fetch game history';
        this.games = [];
      } finally {
        this.loading = false;
      }
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    },
    
    viewGameDetails(game) {
      this.selectedGame = game;
      this.showGameDetailsDialog = true;
      
      // Determine which symbol the player used in this game
      if (game.player_x_id === this.userId) {
        this.playerSymbolInGame = 'x';
      } else {
        this.playerSymbolInGame = 'o';
      }
      
      // Initialize replay
      this.initializeReplay();
    },
    
    initializeReplay() {
      // Reset current state
      this.stopPlayback();
      this.currentMoveIndex = -1;
      this.replayBoard = Array(9).fill('');
      
      // Make a copy of the moves to manipulate
      if (this.selectedGame && Array.isArray(this.selectedGame.moves)) {
        // Sort moves by timestamp if available
        this.replayMoves = [...this.selectedGame.moves].sort((a, b) => {
          if (a.timestamp && b.timestamp) {
            return new Date(a.timestamp) - new Date(b.timestamp);
          }
          return 0;
        });
      } else {
        this.replayMoves = [];
      }
    },
    
    // Get the value at a specific cell in the replay board
    getReplayBoardCell(row, col) {
      const index = row * 3 + col;
      return this.replayBoard[index] || '';
    },
    
    // Play/Pause functionality
    togglePlayback() {
      if (this.isPlaying) {
        this.stopPlayback();
      } else {
        this.startPlayback();
      }
    },
    
    startPlayback() {
      if (this.currentMoveIndex < this.replayMoves.length) {
        this.isPlaying = true;
        this.playbackInterval = setInterval(() => {
          this.moveNext();
          
          // Stop at the end
          if (this.currentMoveIndex >= this.replayMoves.length) {
            this.stopPlayback();
          }
        }, this.playbackDelay);
      }
    },
    
    stopPlayback() {
      if (this.playbackInterval) {
        clearInterval(this.playbackInterval);
        this.playbackInterval = null;
      }
      this.isPlaying = false;
    },
    
    // Navigation controls
    moveToStart() {
      this.stopPlayback();
      this.currentMoveIndex = -1;
      this.replayBoard = Array(9).fill('');
    },
    
    movePrevious() {
      if (this.currentMoveIndex > -1) {
        this.currentMoveIndex--;
        this.updateReplayBoard();
      }
    },
    
    moveNext() {
      if (this.currentMoveIndex < this.replayMoves.length - 1) {
        this.currentMoveIndex++;
        
        // Apply the move
        const move = this.replayMoves[this.currentMoveIndex];
        this.replayBoard[move.position] = move.symbol;
      } else if (this.currentMoveIndex === this.replayMoves.length - 1) {
        // Increment to final state without making changes
        this.currentMoveIndex++;
      }
    },
    
    moveToEnd() {
      this.stopPlayback();
      this.replayBoard = [...this.selectedGame.board];
      this.currentMoveIndex = this.replayMoves.length;
    },
    
    // Rebuild the board up to the current move
    updateReplayBoard() {
      // Start with an empty board
      this.replayBoard = Array(9).fill('');
      
      // Apply all moves up to the current index
      for (let i = 0; i <= this.currentMoveIndex; i++) {
        const move = this.replayMoves[i];
        this.replayBoard[move.position] = move.symbol;
      }
    },
    
    getPlayerName(playerId) {
      if (!this.selectedGame) return 'Unknown';
      
      if (playerId === 'bot') {
        return 'Bot';
      } else if (playerId === this.userId) {
        return 'You';
      } else {
        return 'Opponent';
      }
    },
    
    closeGameDetails() {
      this.stopPlayback();
      this.showGameDetailsDialog = false;
      this.selectedGame = null;
    }
  },
  
  watch: {
    showGameHistoryDialog(newVal) {
      if (newVal === true) {
        this.refreshGameHistory();
      }
    },
    
    playbackSpeed() {
      // Restart playback with new speed if currently playing
      if (this.isPlaying) {
        this.stopPlayback();
        this.startPlayback();
      }
    },
    
    showGameDetailsDialog(newVal) {
      if (!newVal) {
        this.stopPlayback();
      }
    }
  },
  
  // Clean up any intervals when component is destroyed
  beforeDestroy() {
    this.stopPlayback();
  }
}
</script>

<style scoped>
.game-board-preview {
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  max-width: 180px;
}

.game-board-replay {
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  max-width: 240px;
}

.game-board-row {
  display: flex;
}

.game-board-cell {
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 2rem;
  font-weight: bold;
  border: 2px solid #ccc;
}

.x-mark {
  color: #f44336; /* Red */
  font-weight: bold;
}

.o-mark {
  color: #2196f3; /* Blue */
  font-weight: bold;
}
</style>