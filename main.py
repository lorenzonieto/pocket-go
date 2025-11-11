import pygame
import argparse
import socket
import selectors
import game
import multi

parser = argparse.ArgumentParser(description="Classic strategy game Go implemented in python. Left-click to place stones. Spacebar to pass a turn. Score will be printed after two consecutive passes.")
parser.add_argument("-s", "--size", type=int, default=19, help="length/width of the board (default is 19x19)")
parser.add_argument("-b", "--bonus", type=float, default=0, help="the amount of bonus points added to white's score (default is 0)")
parser.add_argument("--host", action="store_true", help="use this flag to host a game over LAN")
parser.add_argument("--join", type=str, default="", help="join a game at the inputted IP address")
args = parser.parse_args()
if args.host and args.join:
    raise Exception("cannot simultaneously host and join a game")
online = args.host or args.join
# initialize pygame
pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption("Go")
screen_size = pygame.display.get_desktop_sizes()[0][1] * 3 / 4
screen = pygame.display.set_mode((screen_size, screen_size))
fpsLimit = 60
click_release = False
pass_release = False
running = True

size = args.size
bonus = args.bonus
my_turn = True

if online:
    sock, sel = multi.get_connection(args.host, args.join)
    connection = multi.Multiplayer(sock, sel)
    if connection.socket:
        if args.host:
            connection.send_init_list(size, bonus, 1)
            print("connection successful")
        else:
            size, bonus, my_turn = connection.get_init()
            print("connection susccessful")
    else:
        running = False

board = game.Board(size, screen_size, bonus)

# main game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if not running:
        break
    if online:
        if multi.ready_for_read(connection.socket, connection.selector):
            move = connection.receive_move()
            if move and not my_turn:
                board.do_move(move)
                my_turn = True
                if board.pass_count > 1:
                    board.score_game()
                    break
            elif not move:
                print("opponent disconnected")
                break
    # poll for mouse input and set ghost position
    board.set_ghost(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])

    game.display_frame(screen, board, my_turn)

    if my_turn:
        clicks = pygame.mouse.get_pressed()
        # player has attempted to place a stone, move must be handled
        if clicks[0] and click_release:
            click_release = False
            old_turn = board.turn
            move = tuple(board.ghost_pos)
            board.do_move(move)
            new_turn = board.turn
            if not(old_turn == new_turn) and online:
                connection.send_move(move)
                my_turn = False
        if not clicks[0]:
            click_release = True

        keys = pygame.key.get_pressed()
        # player has passed their turn
        if keys[pygame.K_SPACE] and pass_release:
            pass_release = False
            move = (-1, -1)
            board.do_move(move)
            if online:
                connection.send_move(move)
                my_turn = False
            if board.pass_count > 1:
                board.score_game()
                break
        if not keys[pygame.K_SPACE]:
            pass_release = True
        # player has pressed debug button
        if keys[pygame.K_d]:
            game.debug()

    clock.tick(fpsLimit)
if online:
    connection.end()
pygame.quit()
