// App.vue
<template>
  <v-app>
    <v-main>
      <v-container class="fill-height">
        <v-row justify="center">
          <v-col cols="12" sm="8" md="6" lg="4">
            <v-card elevation="10" class="pa-4">
              <v-card-title class="text-center text-h4 mb-4">Tic Tac Toe</v-card-title>
              
              <div class="mb-4 d-flex justify-center">
                <!-- Login Button -->
                <v-btn color="primary" @click="showLoginDialog = true">
                  <v-icon left>mdi-account</v-icon>
                  Login
                </v-btn>

                <!-- Invite Button -->
                <v-btn class="ml-2" color="secondary" @click="showInviteDialog = true">
                  <v-icon left>mdi-account-plus</v-icon>
                  Invite Friend
                </v-btn>
              </div>
              
              <!-- Game Status -->
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
                        :class="{ 'disabled': cell !== '' || gameOver }"
                      >

                        <span v-if="cell === 'X'" class="x-mark">X</span>
                        <span v-else-if="cell === 'O'" class="o-mark">O</span>
                      </div>
                    </div>
                  </div>
                </v-col>
              </v-row>
              
              <!-- New Game Button (shows when game ends) -->
              <div class="text-center" v-if="gameOver">
                <v-btn color="success" @click="resetGame">
                  <v-icon left>mdi-refresh</v-icon>
                  New Game
                </v-btn>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
      
      <!-- Login Dialog -->
      <v-dialog v-model="showLoginDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Login</v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field
                label="Username"
                v-model="username"
                prepend-icon="mdi-account"
                required
              ></v-text-field>

              <v-text-field
                label="Password"
                v-model="password"
                prepend-icon="mdi-lock"
                type="password"
                required
              ></v-text-field>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="grey" text @click="showLoginDialog = false">Cancel</v-btn>
            <v-btn color="primary" @click="login">Login</v-btn>
          </v-card-actions>

        </v-card>
      </v-dialog>
      
      <!-- Invite Friend Dialog -->
      <v-dialog v-model="showInviteDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Invite a Friend</v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field
                label="Friend's Email"
                v-model="friendEmail"
                prepend-icon="mdi-email"
                required
              ></v-text-field>

              <v-textarea
                label="Message (Optional)"
                v-model="inviteMessage"
                prepend-icon="mdi-message-text"
                rows="3"
              ></v-textarea>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="grey" text @click="showInviteDialog = false">Cancel</v-btn>
            <v-btn color="secondary" @click="inviteFriend">Send Invite</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'TicTacToe',
  data() {
    return {
      board: [
        ['', '', ''],
        ['', '', ''],
        ['', '', '']
      ],
      currentPlayer: 'X',
      winner: null,
      gameOver: false,
      movesCount: 0,
      
      // Login related
      showLoginDialog: false,
      username: '',
      password: '',
      loggedIn: false,
      
      // Invite related
      showInviteDialog: false,
      friendEmail: '',
      inviteMessage: 'Hey, join me for a game of Tic Tac Toe!'
    };
  },
  computed: {
    gameStatus() {
      if (this.winner) {
        return `Player ${this.winner} wins!`;
      } else if (this.gameOver) {
        return "It's a draw!";
      } else {
        return `Player ${this.currentPlayer}'s turn`;
      }
    }
  },
  methods: {
    makeMove(row, col) {
      // Check if the cell is already occupied or if the game is over
      if (this.board[row][col] !== '' || this.gameOver) {
        return;
      }
      
      // Make the move
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
      
      // Switch player
      this.currentPlayer = this.currentPlayer === 'X' ? 'O' : 'X';
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
    
    login() {
      // Here you would implement actual login logic
      console.log('Login with:', this.username, this.password);
      this.loggedIn = true;
      this.showLoginDialog = false;
      
      // Clear form fields
      this.username = '';
      this.password = '';
    },
    
    inviteFriend() {
      // Here you would implement actual invite logic
      console.log('Invite sent to:', this.friendEmail);
      console.log('Message:', this.inviteMessage);
      this.showInviteDialog = false;
      
      // Clear form fields
      this.friendEmail = '';
      this.inviteMessage = 'Hey, join me for a game of Tic Tac Toe!';
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