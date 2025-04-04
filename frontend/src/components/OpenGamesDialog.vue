<template>
    <v-dialog v-model="showOpenGamesDialogLocal" max-width="500">
      <v-card>
        <v-card-title class="text-h5">
          Open Games
          <v-spacer></v-spacer>
          <v-btn icon @click="refreshOpenGames">
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
        </v-card-title>
  
        <v-card-text>
          <v-alert v-if="loading" type="info" text>
            Loading open games...
          </v-alert>
          
          <v-alert v-else-if="error" type="error" text>
            {{ error }}
          </v-alert>
          
          <v-alert v-else-if="openGames.length === 0" type="info" text>
            No open games available. Create your own game!
          </v-alert>
          
          <v-list v-else>
            <v-list-item v-for="game in openGames" :key="game.id" @click="joinOpenGame(game.id)">
              <v-list-item-icon>
                <v-icon>mdi-gamepad-variant</v-icon>
              </v-list-item-icon>
              
              <v-list-item-content>
                <v-list-item-title>Game #{{ game.id.substring(0, 8) }}</v-list-item-title>
                <v-list-item-subtitle>
                  Created {{ formatTime(game.created_at) }}
                </v-list-item-subtitle>
              </v-list-item-content>
              
              <v-list-item-action>
                <v-btn color="primary" small>
                  Join
                </v-btn>
              </v-list-item-action>
            </v-list-item>
          </v-list>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="showOpenGamesDialogLocal = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>
  
  <script>
  export default {
    name: 'OpenGamesDialog',
    props: {
      showOpenGamesDialog: {
        type: Boolean,
        default: false
      },
      openGames: {
        type: Array,
        default: () => []
      },
      loading: {
        type: Boolean,
        default: false
      },
      error: {
        type: String,
        default: ''
      }
    },
    
    computed: {
      showOpenGamesDialogLocal: {
        get() {
          return this.showOpenGamesDialog;
        },
        set(value) {
          this.$emit('update:showOpenGamesDialog', value);
        }
      }
    },
    
    methods: {
      refreshOpenGames() {
        this.$emit('refresh-open-games');
      },
      
      joinOpenGame(gameId) {
        this.$emit('join-open-game', gameId);
      },
      
      formatTime(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diffMinutes = Math.round((now - date) / (1000 * 60));
        
        if (diffMinutes < 1) {
          return 'just now';
        } else if (diffMinutes === 1) {
          return '1 minute ago';
        } else if (diffMinutes < 60) {
          return `${diffMinutes} minutes ago`;
        } else {
          const hours = Math.floor(diffMinutes / 60);
          return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
        }
      }
    }
  }
  </script>