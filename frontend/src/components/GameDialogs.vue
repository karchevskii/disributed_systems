<template>
    <div>
      <!-- Game Mode Selection Dialog (Human/Bot) -->
      <v-dialog v-model="showGameModeDialogLocal" max-width="400">
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
            <v-btn color="grey" text @click="showGameModeDialogLocal = false">Cancel</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- Symbol Selection Dialog (X or O) -->
      <v-dialog v-model="showSymbolDialogLocal" max-width="400">
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
            <v-btn color="grey" text @click="showSymbolDialogLocal = false">Cancel</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- Join Game Dialog -->
      <v-dialog v-model="showJoinDialogLocal" max-width="400">
        <v-card>
          <v-card-title class="text-h5">Join a Game</v-card-title>
  
          <!-- Textfield for Game-Code -->
          <v-card-text>
            <v-form @submit.prevent="joinGame">
              <v-text-field
                label="Game ID"
                v-model="joinGameCodeLocal"
                prepend-icon="mdi-pound"
                placeholder="Enter game ID or paste invite link"
                required
              ></v-text-field>
            </v-form>
          </v-card-text>
  
          <v-card-actions>
            <v-spacer></v-spacer>
  
            <!-- Cancel Button -->
            <v-btn color="grey" text @click="showJoinDialogLocal = false">Cancel</v-btn>
  
            <!-- Join Button -->
            <v-btn color="primary" @click="joinGame" :disabled="!joinGameCodeLocal">Join</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
  </template>
  
<script>
  export default {
    name: 'GameDialogs',
    props: {
      showGameModeDialog: {
        type: Boolean,
        default: false
      },
      showSymbolDialog: {
        type: Boolean,
        default: false
      },
      showJoinDialog: {
        type: Boolean,
        default: false
      },
      joinGameCode: {
        type: String,
        default: ''
      }
    },
    
    computed: {
      showGameModeDialogLocal: {
        get() {
          return this.showGameModeDialog;
        },
        set(value) {
          this.$emit('update:showGameModeDialog', value);
        }
      },
      showSymbolDialogLocal: {
        get() {
          return this.showSymbolDialog;
        },
        set(value) {
          this.$emit('update:showSymbolDialog', value);
        }
      },
      showJoinDialogLocal: {
        get() {
          return this.showJoinDialog;
        },
        set(value) {
          this.$emit('update:showJoinDialog', value);
        }
      },
      joinGameCodeLocal: {
        get() {
          return this.joinGameCode;
        },
        set(value) {
          this.$emit('update:joinGameCode', value);
        }
      }
    },
    
    methods: {
      createNewGame(mode) {
        this.$emit('create-new-game', mode);
      },
      
      confirmCreateGame(symbol) {
        this.$emit('confirm-create-game', symbol);
      },
      
      joinGame() {
        this.$emit('join-game');
      }
    }
  }
</script>