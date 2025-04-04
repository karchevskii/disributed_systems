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

    <!-- Game Details Dialog -->
    <v-dialog v-model="showGameDetailsDialog" max-width="600">
      <v-card v-if="selectedGame">
        <v-card-title class="text-h5">
          Game Details
        </v-card-title>

        <v-card-text>
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
            <v-col cols="12" sm="6">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>Date</v-list-item-title>
                  <v-list-item-subtitle>{{ formatDate(selectedGame.created_at) }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>
            <v-col cols="12" sm="6">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>Game ID</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedGame.game_id }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>
          </v-row>

          <v-divider class="my-4"></v-divider>

          <h3 class="text-subtitle-1 mb-2">Final Board</h3>
          <div class="game-board-preview">
            <div class="game-board-row" v-for="(_, rowIndex) in 3" :key="'row-' + rowIndex">
              <div
                class="game-board-cell"
                v-for="(_, colIndex) in 3"
                :key="'cell-' + rowIndex + '-' + colIndex"
              >
                <span v-if="getBoardCell(rowIndex, colIndex) === 'x'" class="x-mark">X</span>
                <span v-else-if="getBoardCell(rowIndex, colIndex) === 'o'" class="o-mark">O</span>
              </div>
            </div>
          </div>

          <v-divider class="my-4"></v-divider>

          <h3 class="text-subtitle-1 mb-2">Game Moves</h3>
          <v-timeline dense>
            <v-timeline-item
              v-for="(move, index) in selectedGame.moves"
              :key="index"
              :color="move.symbol === 'x' ? 'red' : 'blue'"
              small
            >
              <div>
                <strong>{{ getPlayerName(move.player) }}</strong> placed 
                <span :class="move.symbol === 'x' ? 'x-mark' : 'o-mark'">
                  {{ move.symbol.toUpperCase() }}
                </span> 
                at position ({{ Math.floor(move.position / 3) }}, {{ move.position % 3 }})
              </div>
            </v-timeline-item>
          </v-timeline>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="showGameDetailsDialog = false">Close</v-btn>
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
    }
  },
  
  methods: {
    async refreshGameHistory() {
      this.loading = true;
      this.error = '';
      
      try {
        const response = await fetch(`${this.gameHistoryApiUrl}/games`, {
          method: 'GET',
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch game history: ${response.statusText}`);
        }
        
        // Get the response text first instead of directly calling .json()
        const responseText = await response.text();
        
        let data;
        try {
          // Attempt to parse the JSON
          data = JSON.parse(responseText);
        } catch (parseError) {
          console.error('Error parsing JSON:', parseError);
          console.log('Response text:', responseText);
          throw new Error('Error parsing game history data from server');
        }
        
        if (!data || !data.games || !Array.isArray(data.games)) {
          throw new Error('Invalid game history data format');
        }
        
        // Process the games to ensure the data structure is correct
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
      } catch (error) {
        console.error('Error fetching game history:', error);
        this.error = error.message || 'Failed to fetch game history';
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
    },

    getBoardCell(row, col) {
      if (!this.selectedGame || !this.selectedGame.board) return '';
      const index = row * 3 + col;
      return this.selectedGame.board[index] || '';
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
    }
  },
  
  watch: {
    showGameHistoryDialog(newVal) {
      if (newVal === true) {
        this.refreshGameHistory();
      }
    }
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

.game-board-row {
  display: flex;
}

.game-board-cell {
  width: 60px;
  height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.5rem;
  font-weight: bold;
  border: 2px solid #ccc;
}

.x-mark {
  color: #f44336; /* Red */
}

.o-mark {
  color: #2196f3; /* Blue */
}
</style>