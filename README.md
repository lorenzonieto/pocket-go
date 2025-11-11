# PocketGo
PocketGo is an implementation of the classic strategy game Go. It features custom board sizes, custom bonus point settings, automated scoring, and local multiplayer.
# Installation
PocketGo requires python, which can be downloaded [here](https://www.python.org/downloads/) at the offical python website. It also requires the pygame library, which is available [here](https://www.pygame.org/wiki/GettingStarted).
# Features
To run the game on a standard 19x19 board with no bonus points, open the command prompt/terminal and enter
```
python main.py
```
Use the `--size` option to change the size of the board and the `--bonus` option to change the amount of bonus points for white. For example,
```
python main.py --size 9 --bonus 8
```
will run the game on a 9x9 board with 8 points added to white's score.
# Controls
- Left click: place a stone
- Spacebar: pass the current player's turn

After both players have passed their turns consecutively, the game will end and the score will be printed on the command line/terminal
