<template>
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="game-board">
          <div v-for="(row, rowIndex) in board" :key="'row-' + rowIndex" class="game-row">
            <div 
              v-for="(cell, colIndex) in row" 
              :key="'cell-' + rowIndex + '-' + colIndex"
              class="game-cell"
              @click="makeMove(rowIndex, colIndex)"
              :class="{ 'disabled': cell !== '' || gameOver || currentPlayer !== playerSymbol }"
            >
              <span v-if="cell === 'X'" class="x-mark">X</span>
              <span v-else-if="cell === 'O'" class="o-mark">O</span>
            </div>
          </div>
        </div>
      </v-col>
    </v-row>
  </template>
  
  <script>
  export default {
    name: 'GameBoard',
    props: {
      board: {
        type: Array,
        required: true
      },
      gameOver: {
        type: Boolean,
        default: false
      },
      currentPlayer: {
        type: String,
        default: 'X'
      },
      playerSymbol: {
        type: String,
        default: null
      }
    },
    methods: {
      makeMove(rowIndex, colIndex) {
        this.$emit('make-move', rowIndex, colIndex);
      }
    }
  }
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