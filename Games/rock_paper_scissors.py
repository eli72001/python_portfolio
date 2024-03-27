import random
def checkWinner(p1, p2):
    if p1 == p2:
        return 2 #TIE
    if p1 == 'rock':
        if p2 == 'paper':
            return 1 #p2 win
        else:
            return 0 #p1 win
    elif p1 == 'paper':
        if p2 == 'scissors':
            return 1
        else:
            return 0
    else:
        if p2 == 'rock':
            return 1
        else:
            return 0

def play():
    while True:
        player = input('Rock, Paper, or Scissors: ').lower()
        cpu = random.randint(0,2)
        cpu_choice = ''
        if cpu == 0:
            cpu_choice = 'rock'
        elif cpu == 1:
            cpu_choice = 'paper'
        else:
            cpu_choice = 'scissors'
        if(player == 'rock' or player == 'paper' or player == 'scissors'):
            result = checkWinner(player, cpu_choice)
            if result == 2:
                print(f"It's a Tie! You chose {player}, the cpu chose {cpu_choice}\n")
            if result == 1:
                print(f"The CPU Won! You chose {player}, the cpu chose {cpu_choice}\n")
            if result == 0:
                print(f"You Won! You chose {player}, the cpu chose {cpu_choice}\n")
        else:
            print('Invalid choice. Please try again')
        playagain = input('Would you like to play again? (y/n) ')
        print('\n')
        if playagain == 'n':
            break

play()