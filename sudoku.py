import random

def generate_board():
    """Generates a new Sudoku board."""
    base = 3
    side = base * base

    def pattern(r, c): return (base * (r % base) + r // base + c) % side
    def shuffle(s): return random.sample(s, len(s))

    rBase = range(base)
    rows = [g * base + r for g in shuffle(rBase) for r in shuffle(rBase)]
    cols = [g * base + c for g in shuffle(rBase) for c in shuffle(rBase)]
    nums = shuffle(range(1, base * base + 1))

    board = [[nums[pattern(r, c)] for c in cols] for r in rows]

    squares = side * side
    empties = squares * 3 // 4
    for p in random.sample(range(squares), empties):
        board[p // side][p % side] = 0

    return board

def is_valid(board, r, c, num):
    """Checks if a number can be placed in a specific cell."""
    for i in range(9):
        if board[r][i] == num or board[i][c] == num:
            return False

    start_row, start_col = 3 * (r // 3), 3 * (c // 3)
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def is_solved(board):
    """Checks if the board is completely and correctly filled."""
    for row in board:
        if 0 in row:
            return False
    return True

def print_board(board):
    """Prints the Sudoku board."""
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - ")
        for j, num in enumerate(row):
            if j % 3 == 0 and j != 0:
                print("| ", end="")
            print(f"{num if num != 0 else '.'} ", end="")
        print()
