<template>
    <v-card class="chat-container" outlined>
      <v-card-title class="py-2 d-flex align-center">
        <v-icon left small>mdi-chat</v-icon>
        <span class="text-subtitle-1">Game Chat</span>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text class="chat-messages pa-2" ref="messagesContainer">
        <div v-if="messages.length === 0" class="text-center text-caption pa-4 grey--text">
          No messages yet. Start the conversation!
        </div>
        
        <div 
          v-for="(message, index) in messages" 
          :key="'msg-' + index"
          class="message mb-2 pa-2 rounded"
          :class="{ 
            'message-self': message.sender === playerSymbol,
            'message-opponent': message.sender !== playerSymbol && message.sender !== 'bot',
            'message-bot': message.sender === 'bot'
          }"
        >
          <div class="message-sender">
            <span>{{ getSenderName(message.sender) }}</span>
          </div>
          <div class="message-content">
            {{ message.message }}
          </div>
        </div>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="pa-2">
        <v-text-field
          v-model="newMessage"
          placeholder="Type a message..."
          outlined
          dense
          hide-details
          @keyup.enter="sendMessage"
        >
          <template v-slot:append>
            <v-btn
              icon
              color="primary"
              :disabled="!newMessage.trim()"
              @click="sendMessage"
            >
              <v-icon>mdi-send</v-icon>
            </v-btn>
          </template>
        </v-text-field>
      </v-card-actions>
    </v-card>
  </template>
  
  <script>
  export default {
    name: 'GameChat',
    props: {
      playerSymbol: {
        type: String,
        required: true
      },
      gameMode: {
        type: String,
        required: true
      }
    },
    
    data() {
      return {
        messages: [],
        newMessage: '',
      };
    },
    
    methods: {
      sendMessage() {
        const message = this.newMessage.trim();
        if (!message) return;
        
        this.$emit('send-message', message);
        this.newMessage = '';
      },
      
      addMessage(messageData) {
        this.messages.push(messageData);
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      },
      
      scrollToBottom() {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight;
        }
      },
      
      getSenderName(sender) {
        if (sender === this.playerSymbol) {
          return 'You';
        } else if (sender === 'bot') {
          return 'Bot';
        } else {
          return 'Opponent';
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .chat-container {
    display: flex;
    flex-direction: column;
    height: 300px;
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    max-height: 200px;
  }
  
  .message {
    max-width: 85%;
    word-wrap: break-word;
  }
  
  .message-self {
    background-color: #00028b;
    margin-left: auto;
    border-radius: 15px 15px 0 15px !important;
  }
  
  .message-opponent {
    background-color: #7c0000;
    margin-right: auto;
    border-radius: 15px 15px 15px 0 !important;
  }
  
  .message-bot {
    background-color: #e8f5e9;
    margin-right: auto;
    border-radius: 15px 15px 15px 0 !important;
  }
  
  .message-sender {
    font-size: 0.8rem;
    font-weight: bold;
    margin-bottom: 2px;
  }
  
  .message-content {
    font-size: 0.95rem;
  }
  </style>