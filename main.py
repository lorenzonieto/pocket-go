import pygame
import argparse
import socket
import selectors
import game

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
fpsLimit = 60
running = True

game = game.Board(args.size, args.bonus, online, False)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    # poll for mouse input and set ghost position
    game.set_ghost(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])

    game.display_frame()

    clicks = pygame.mouse.get_pressed()
    # player has attempted to place a stone, move must be handled
    if clicks[0] and click_release:
        click_release = False
        old_turn = game.turn
        game.do_move()
        new_turn = game.turn
        if not(old_turn == new_turn):
            pass_count = 0
    if not clicks[0]:
        click_release = True

    keys = pygame.key.get_pressed()
    # player has passed their turn
    if keys[pygame.K_SPACE] and pass_release:
        pass_release = False
        pass_count += 1
        if pass_count == 2:
            running = False
            game.score_game()
        game.turn = not game.turn
    if not keys[pygame.K_SPACE]:
        pass_release = True
    # player has pressed debug button
    if keys[pygame.K_d]:
        debug()

    clock.tick(fpsLimit)
pygame.quit()