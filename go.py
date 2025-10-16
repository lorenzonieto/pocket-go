import pygame
import argparse

parser = argparse.ArgumentParser(description="Classic strategy game Go implemented in python. Left-click to place stones. Spacebar to pass a turn. Score will be printed after two consecutive passes.")
parser.add_argument("-s", "--size", type=int, default=19, help="length/width of the board (default is 19x19)")
parser.add_argument("-b", "--bonus", type=float, default=0, help="the amount of bonus points added to white's score (default is 0)")
args = parser.parse_args()

pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption("Go")
fpsLimit = 60
running = True

screen_size = pygame.display.get_desktop_sizes()[0][1] * 3 / 4
screen = pygame.display.set_mode((screen_size, screen_size))
board_size = args.size
tile_size = screen_size / (board_size + 1)
stone_radius = tile_size / 2
tengen_size = max(tile_size / 8, 2)
ghost_thickness = max(int(tile_size / 15), 2)
board = [[-1 for i in range(board_size)] for j in range(board_size)]
board_pos = [tile_size * i for i in range(1, board_size + 1)]
center_coord = board_pos[board_size // 2]
colors = ("black", "white")
turn = False
click_release = True
pass_release = True
stone_list = [set(), set()]
board_history = {}
pass_count = 0

ghost_pos = [0, 0]

def show_board():
    screen.fill((240, 170, 100))
    # draw board lines
    for i in range(board_size):
        pygame.draw.line(screen, "black", (board_pos[i], board_pos[0]), (board_pos[i], board_pos[board_size - 1]), 2)
        pygame.draw.line(screen, "black", (board_pos[0], board_pos[i]), (board_pos[board_size - 1], board_pos[i]), 2)
    if board_size % 2:
        pygame.draw.circle(screen, "black", (center_coord, center_coord), tengen_size)
    if board_size == 19:
        for i in range(3):
            for j in range(3):
                x_coord = board_pos[(i * 6) + 3]
                y_coord = board_pos[(j * 6) + 3]
                pygame.draw.circle(screen, "black", (x_coord, y_coord), tengen_size)
    # draw pieces
    for i in range(board_size):
        for j in range(board_size):
            if board[i][j] < 0:
                continue
            else:
                pygame.draw.circle(screen, colors[board[i][j]], (board_pos[i], board_pos[j]), stone_radius)

def clamp(n, floor, ceiling):
    return min(max(n, floor), ceiling)

def get_ghost(raw_x, raw_y):
    mouse_x = clamp(((raw_x + stone_radius) // tile_size), 1, board_size) - 1
    mouse_y = clamp(((raw_y + stone_radius) // tile_size), 1, board_size) - 1
    return [int(mouse_x), int(mouse_y)]

def show_ghost(x, y):
    pygame.draw.circle(screen, colors[turn], (board_pos[x], board_pos[y]), stone_radius, ghost_thickness)

def neighborhood(point):
    neighbors = []
    if point[0] > 0:
        neighbors.append((point[0] - 1, point[1]))
    if point[0] < (board_size - 1):
        neighbors.append((point[0] + 1, point[1]))
    if point[1] > 0:
        neighbors.append((point[0], point[1] - 1))
    if point[1] < (board_size - 1):
        neighbors.append((point[0], point[1] + 1))
    return neighbors

def get_group(point):
    group = set()
    unexplored = {point}
    color = board[point[0]][point[1]]
    neighbor_types = [False, False, False]
    while unexplored:
        new = unexplored.pop()
        group.add(new)
        for neighbor in neighborhood(new):
            if (board[neighbor[0]][neighbor[1]] == color) and not(neighbor in unexplored):
                if not(neighbor in group):
                    unexplored.add(neighbor)
                    neighbor_types[color] = True
            else:
                neighbor_types[board[neighbor[0]][neighbor[1]]] = True
    return group, neighbor_types


def debug():
    #print(get_group(tuple(ghost_pos)))
    return

def do_move(point, turn, ):
    opponent = not turn
    if not(board[point[0]][point[1]] == -1):
        return turn
    board[point[0]][point[1]] = turn
    checked = set()
    killed_by_move = set()
    for neighbor in neighborhood(point):
        if board[neighbor[0]][neighbor[1]] == opponent and neighbor not in checked:
            group, alive = get_group(neighbor)
            checked.update(group)
            if not alive[2]:
                killed_by_move.update(group)
    if not killed_by_move:
        self_group, self_alive = get_group(point)
        if not self_alive[2]:
            board[point[0]][point[1]] = -1
            return turn
    new_stone_list = [stone_list[0].copy(), stone_list[1].copy()]
    new_stone_list[turn].add(point)
    new_stone_list[opponent] -= killed_by_move
    new_stone_count = len(new_stone_list[0]) + len(new_stone_list[1])
    history = board_history.get(new_stone_count)
    if not history:
        board_history.update({new_stone_count: [new_stone_list]})
    else:
        for board_state in history:
            if new_stone_list[0] == board_state[0] and new_stone_list[1] == board_state[1]:
                board[point[0]][point[1]] = -1
                return turn
        history.append(new_stone_list)
    stone_list.clear()
    stone_list.append(new_stone_list[0])
    stone_list.append(new_stone_list[1])
    for death in killed_by_move:
        board[death[0]][death[1]] = -1
    return not turn

def score_game():
    if args.bonus.is_integer():
        score = [0, int(args.bonus)]
    else:
        score = [0, args.bonus]
    scored = set()
    for i in range(board_size):
        for j in range(board_size):
            if not((i, j) in scored):
                color = board[i][j]
                group, state = get_group((i, j))
                if color < 0:
                    if not(state[0] == state[1]):
                        if state[0]:
                            score[0] += len(group)
                        else:
                            score[1] += len(group)
                    scored.update(group)
                else:
                    score[color] += len(group)
                    scored.update(group)
    print("Black " + str(score[0]) + "-" + str(score[1]) + " White")
    return False

def display_frame():
    show_board()
    show_ghost(ghost_pos[0], ghost_pos[1])

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    ghost_pos = get_ghost(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])

    display_frame()

    clicks = pygame.mouse.get_pressed()

    if clicks[0] and click_release:
        click_release = False
        turn = do_move(tuple(ghost_pos), turn)
        pass_count = 0
    if not clicks[0]:
        click_release = True

    keys = pygame.key.get_pressed()

    if keys[pygame.K_SPACE] and pass_release:
        pass_release = False
        pass_count += 1
        if pass_count == 2:
            running = score_game()
        turn = not turn
    if not keys[pygame.K_SPACE]:
        pass_release = True

    if keys[pygame.K_d]:
        debug()

    pygame.display.flip()
    clock.tick(fpsLimit)
    
pygame.quit()