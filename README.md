# PocketGo
PocketGo is an implementation of the classic strategy game Go. It features custom board sizes, custom bonus point settings, local/online multiplayer, and automated scoring.
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
# Online
To host an online game, use the `--host` option:
```
python main.py --host
```
The window will appear empty while the program looks for an connection. Close the window to stop looking for a connection. To join a game, use `--join` followed by a valid IPv4 address:
```
python main.py --join 127.0.0.1
```
This will attempt to connect to a player hosting a game at the inputted IP address. The size and bonus options will be inherited from the hoster.
# Controls
- Left click: place a stone
- Spacebar: pass the current player's turn

After both players have passed their turns consecutively, the game will end and the score will be printed on the command line/terminal
