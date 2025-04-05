def check_winner(board):
    # Check rows
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != "":
            return board[i]

    # Check columns
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != "":
            return board[i]

    # Check diagonals
    if board[0] == board[4] == board[8] != "":
        return board[0]
    if board[2] == board[4] == board[6] != "":
        return board[2]

    return None


def minimax(board, is_maximizing):
    winner = check_winner(board)
    if winner == "x":
        return 1
    if winner == "o":
        return -1
    if "" not in board:
        return 0

    if is_maximizing:
        best_score = -float("inf")
        for i in range(9):
            if board[i] == "":
                board[i] = "x"
                score = minimax(board, False)
                board[i] = ""
                best_score = max(score, best_score)
        return best_score
    else:
        best_score = float("inf")
        for i in range(9):
            if board[i] == "":
                board[i] = "o"
                score = minimax(board, True)
                board[i] = ""
                best_score = min(score, best_score)
        return best_score


def best_move(board):
    best_score = -float("inf")
    move = None
    for i in range(9):
        if board[i] == "":
            board[i] = "x"
            score = minimax(board, False)
            board[i] = ""
            if score > best_score:
                best_score = score
                move = i
    return move
