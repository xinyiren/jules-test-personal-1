from sudoku import generate_board, is_valid, is_solved, print_board

def main():
    """Main function to run the Sudoku game."""
    board = generate_board()

    while not is_solved(board):
        print_board(board)
        try:
            row = int(input("Enter row (1-9): ")) - 1
            col = int(input("Enter col (1-9): ")) - 1
            num = int(input("Enter num (1-9): "))

            if 0 <= row < 9 and 0 <= col < 9 and 1 <= num <= 9:
                if is_valid(board, row, col, num):
                    board[row][col] = num
                else:
                    print("Invalid move. Try again.")
            else:
                print("Invalid input. Row, col, and num must be between 1 and 9.")
        except ValueError:
            print("Invalid input. Please enter numbers only.")

    print("Congratulations! You solved the Sudoku!")
    print_board(board)

if __name__ == "__main__":
    main()
