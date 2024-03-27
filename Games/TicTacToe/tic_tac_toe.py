""" Import random for computer generated turn

    Returns:
        int: row/col of computer move
"""
import random
import sys
from tkinter import messagebox, Tk, Button

class TicTacToe():
    """Class representing a game of TicTacToe"""
    def __init__(self):
        self.reset_board()
        if messagebox.askyesno("Select Number of Players",
                               "Would you like to play against the computer?"):
            self.two_player = False
        else:
            self.two_player = True
        self.root = Tk()
        self.root.title("Tic-Tac-Toe")
        self.root.resizable(0,0)
        self.current_player = 'X'
        self.stop_game = False

    def reset_board(self):
        """Resets board to inital empty state as well as state board

        more info here

        Bord keeps track of the physical buttons shown to the user and where they click
        States keeps track of every move and is used for the logic in the code"""
        self.board = [
            [0,0,0],
            [0,0,0],
            [0,0,0]
        ]
        self.states = [
            [0,0,0],
            [0,0,0],
            [0,0,0]
        ]
    def play(self):
        """ Renders the state of the board and plays"""
        for row, row_val in enumerate(self.board):
            for col in range(len(row_val)):
                self._populate_board(row, col)
        self.root.mainloop()

    def _populate_board(self, row: int, col: int):
        """Populates board with buttons and displays to player"""
        self.board[row][col] = Button(height=4, width=8, font=('Helvetica', '20'),
                                        command= lambda r = row, c = col : self._user_click(r,c))
        self.board[row][col].grid(row=row, column = col)


    def _user_click(self, row: int, col: int):
        """ Displays where the user clicks on the board and the mark that represents the  player

        Args:
            row (int): x coordinate of click
            col (int): y coordinate of click
        """
        if  self.states[row][col] == 0 and not self.stop_game:
            self._go_player(row, col)
            if not self.two_player and not self.stop_game:
                self._go_computer()
        if self.two_player:
            if self.states[row][col] == 0 and not self.stop_game:
                self._go_player(row, col)

    def _go_player(self, row:int, col:int):
        """Configures move for current player"""
        self._configure_move(row,col)
        self._check_if_win()
        if self.current_player == 'O':
            self.current_player = 'X'
        else:
            self.current_player = 'O'


    def _go_computer(self):
        """Generate random place for computer to move. Cell must be a valid location"""
        while True:
            computer_row = random.randint(0,2)
            computer_col = random.randint(0,2)
            if self.states[computer_row][computer_col] == 0:
                break
        self._configure_move(computer_row, computer_col)
        self._check_if_win()
        self.current_player = 'X'

    def _configure_move(self, row: int, col: int):
        """ Adds move to the board and states variables

        Args:
            row (int): x coordinate of move
            col (int): y coordinate of move
        """
        self.board[row][col].configure(text = self.current_player)
        self.states[row][col] = self.current_player

    def _check_if_win(self):
        """ Check to see if someone has won the game"""
        for i in range(3):

            if self.states[i][0] == self.states[i][1] == self.states[i][2] != 0:
                self.stop_game = True
                self._display_winner_message()
                break

            if self.states[0][i] == self.states[1][i] == self.states[2][i] != 0:
                self.stop_game = True
                self._display_winner_message()
                break

        if self.states[0][0] == self.states[1][1] == self.states[2][2] != 0:
            self.stop_game = True
            self._display_winner_message()

        elif self.states[0][2] == self.states[1][1] == self.states[2][0] != 0:
            self.stop_game = True
            self._display_winner_message()

        else:
            if self._checkfull():
                self.stop_game = True
                self._display_winner_message(tie = True)

    def _display_winner_message(self, tie: bool = False):
        """ Display the message of who wins and ask if player would like to play again"""
        if tie:
            messagebox.showinfo("Tie!", "It's a Tie!")
        else:
            messagebox.showinfo("Winner!", self.current_player + " Won!")
        if messagebox.askyesno("Play Again?", "Would you like to play again?"):
            self.reset_board()
            self.current_player = 'X'
            self.stop_game = False
            self.play()
        else:
            sys.exit()


    def _checkfull(self):
        """Check if there are no more moves to make."""
        for i in self.states:
            for j in i:
                if j == 0:
                    return False
        return True
