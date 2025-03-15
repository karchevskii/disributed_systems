from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import uuid
import time
from typing import Dict, List, Tuple, Optional, Union

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type"], "methods": ["GET", "POST", "OPTIONS"]}})  # Enable CORS for all routes

# In-memory storage for active games
# In production, you would use a database
games = {}

class TicTacToeGame:
    def __init__(self, game_id: str, user_id: str, difficulty: str = "hard"):
        self.id = game_id
        self.user_id = user_id
        self.difficulty = difficulty  # Options: "easy", "medium", "hard", "impossible"
        self.board = [['', '', ''] for _ in range(3)]
        self.current_player = 'X'  # X always starts
        self.winner = None
        self.game_over = False
        self.created_at = time.time()
        self.last_activity = time.time()
        self.human_symbol = 'X'  # Human is X by default
        self.bot_symbol = 'O'    # Bot is O by default

    def make_move(self, row: int, col: int, player: str) -> bool:
        """Make a move on the board"""
        if (
            row < 0 or row > 2 or 
            col < 0 or col > 2 or 
            self.board[row][col] != '' or 
            self.game_over or 
            player != self.current_player
        ):
            return False

        self.board[row][col] = player
        self.last_activity = time.time()
        
        # Check for win or draw
        if self._check_win(player):
            self.winner = player
            self.game_over = True
        elif self._is_board_full():
            self.game_over = True
        else:
            # Switch player
            self.current_player = 'O' if player == 'X' else 'X'
        
        return True

    def _check_win(self, player: str) -> bool:
        """Check if the current player has won"""
        # Check rows
        for row in self.board:
            if row.count(player) == 3:
                return True
        
        # Check columns
        for col in range(3):
            if [self.board[row][col] for row in range(3)].count(player) == 3:
                return True
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] == player:
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] == player:
            return True
        
        return False

    def _is_board_full(self) -> bool:
        """Check if the board is full (draw)"""
        for row in self.board:
            if '' in row:
                return False
        return True

    def get_bot_move(self) -> Optional[Tuple[int, int]]:
        """Get the next move for the bot based on difficulty"""
        if self.difficulty == "easy":
            return self._get_easy_bot_move()
        elif self.difficulty == "medium":
            return self._get_medium_bot_move()
        elif self.difficulty == "hard":
            return self._get_hard_bot_move()
        else:  # impossible
            return self._get_minimax_move()

    def _get_easy_bot_move(self) -> Optional[Tuple[int, int]]:
        """Bot makes random moves"""
        empty_cells = []
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == '':
                    empty_cells.append((i, j))
        
        if empty_cells:
            return random.choice(empty_cells)
        return None

    def _get_medium_bot_move(self) -> Optional[Tuple[int, int]]:
        """Bot blocks obvious wins or takes obvious wins, otherwise random"""
        # First check if bot can win
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == '':
                    self.board[i][j] = self.bot_symbol
                    if self._check_win(self.bot_symbol):
                        self.board[i][j] = ''  # Reset
                        return (i, j)
                    self.board[i][j] = ''  # Reset
        
        # Then check if human can win and block
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == '':
                    self.board[i][j] = self.human_symbol
                    if self._check_win(self.human_symbol):
                        self.board[i][j] = ''  # Reset
                        return (i, j)
                    self.board[i][j] = ''  # Reset
        
        # Otherwise make a random move
        return self._get_easy_bot_move()

    def _get_hard_bot_move(self) -> Optional[Tuple[int, int]]:
        """Smart bot that also prioritizes center and corners"""
        # First check for winning moves or blocking moves
        winning_move = self._get_medium_bot_move()
        if winning_move and (winning_move != self._get_easy_bot_move()):
            return winning_move
        
        # Take center if available
        if self.board[1][1] == '':
            return (1, 1)
        
        # Take corners if available
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        empty_corners = [corner for corner in corners if self.board[corner[0]][corner[1]] == '']
        if empty_corners:
            return random.choice(empty_corners)
        
        # Otherwise make a random move
        return self._get_easy_bot_move()

    def _get_minimax_move(self) -> Optional[Tuple[int, int]]:
        """Unbeatable bot using minimax algorithm with alpha-beta pruning"""
        best_score = float('-inf')
        best_move = None
        
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == '':
                    self.board[i][j] = self.bot_symbol
                    score = self._minimax(0, False, float('-inf'), float('inf'))
                    self.board[i][j] = ''
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
        
        return best_move

    def _minimax(self, depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
        """Minimax algorithm with alpha-beta pruning"""
        # Check for terminal states
        if self._check_win(self.bot_symbol):
            return 10 - depth
        if self._check_win(self.human_symbol):
            return depth - 10
        if self._is_board_full():
            return 0
        
        if is_maximizing:
            best_score = float('-inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == '':
                        self.board[i][j] = self.bot_symbol
                        score = self._minimax(depth + 1, False, alpha, beta)
                        self.board[i][j] = ''
                        best_score = max(score, best_score)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            break
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == '':
                        self.board[i][j] = self.human_symbol
                        score = self._minimax(depth + 1, True, alpha, beta)
                        self.board[i][j] = ''
                        best_score = min(score, best_score)
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            break
            return best_score

    def to_dict(self) -> Dict:
        """Convert game state to dictionary for JSON response"""
        return {
            "id": self.id,
            "board": self.board,
            "currentPlayer": self.current_player,
            "winner": self.winner,
            "gameOver": self.game_over,
            "humanSymbol": self.human_symbol,
            "botSymbol": self.bot_symbol
        }


@app.route('/api/bot/create', methods=['POST'])
def create_game():
    """Create a new game against the bot"""
    data = request.get_json()
    
    user_id = data.get('userId')
    if not user_id:
        return jsonify({"error": "Missing userId"}), 400
    
    difficulty = data.get('difficulty', 'hard')
    # Validate difficulty
    if difficulty not in ["easy", "medium", "hard", "impossible"]:
        difficulty = "hard"  # Default to hard if invalid
    
    # Generate a game ID
    game_id = f"BOT{uuid.uuid4().hex[:6].upper()}"
    
    # Create new game
    game = TicTacToeGame(game_id, user_id, difficulty)
    
    # Store game in memory
    games[game_id] = game
    
    # Set player symbols based on preference
    human_symbol = data.get('humanSymbol', 'X')
    if human_symbol not in ['X', 'O']:
        human_symbol = 'X'  # Default to X
    
    game.human_symbol = human_symbol
    game.bot_symbol = 'O' if human_symbol == 'X' else 'X'
    
    # If bot is X, make the first move
    if game.bot_symbol == 'X':
        bot_move = game.get_bot_move()
        if bot_move:
            game.make_move(bot_move[0], bot_move[1], 'X')
    
    return jsonify({
        "game": game.to_dict(),
        "message": "Game created successfully"
    })


@app.route('/api/bot/move/<game_id>', methods=['POST'])
def make_move(game_id):
    """Handle human move and respond with bot move"""
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    
    game = games[game_id]
    data = request.get_json()
    
    # Get move from request
    row = data.get('row')
    col = data.get('col')
    player = data.get('player')
    
    # Validate move
    if row is None or col is None or player is None:
        return jsonify({"error": "Invalid move parameters"}), 400
    
    # Make human move
    move_success = game.make_move(row, col, player)
    if not move_success:
        return jsonify({"error": "Invalid move"}), 400
    
    # Check if game is over after human move
    if game.game_over:
        return jsonify({
            "game": game.to_dict(),
            "message": "Game over"
        })
    
    # Make bot move
    bot_move = game.get_bot_move()
    if bot_move:
        game.make_move(bot_move[0], bot_move[1], game.current_player)
    
    return jsonify({
        "game": game.to_dict(),
        "message": "Move processed successfully"
    })


@app.route('/api/bot/game/<game_id>', methods=['GET'])
def get_game(game_id):
    """Get current game state"""
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    
    return jsonify({
        "game": games[game_id].to_dict()
    })


@app.route('/api/bot/leave/<game_id>', methods=['POST'])
def leave_game(game_id):
    """End game and clean up resources"""
    if game_id in games:
        del games[game_id]
    
    return jsonify({
        "message": "Game ended successfully"
    })


# Maintenance endpoint to clean up stale games
@app.route('/api/bot/maintenance/cleanup', methods=['POST'])
def cleanup_games():
    """Remove stale games (older than 1 hour with no activity)"""
    current_time = time.time()
    stale_threshold = 60 * 60  # 1 hour
    
    stale_games = [
        game_id for game_id, game in games.items()
        if current_time - game.last_activity > stale_threshold
    ]
    
    for game_id in stale_games:
        del games[game_id]
    
    return jsonify({
        "message": f"Removed {len(stale_games)} stale games"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)