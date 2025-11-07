import pygame
import argparse
import socket
import selectors

parser = argparse.ArgumentParser(description="Classic strategy game Go implemented in python. Left-click to place stones. Spacebar to pass a turn. Score will be printed after two consecutive passes.")
parser.add_argument("-s", "--size", type=int, default=19, help="length/width of the board (default is 19x19)")
parser.add_argument("-b", "--bonus", type=float, default=0, help="the amount of bonus points added to white's score (default is 0)")
parser.add_argument("--host", action="store_true", help="use this flag to host a game over LAN")
parser.add_argument("--join", type=str, default="", help="join a game at the inputted IP address")
args = parser.parse_args()
if args.host and args.join:
    raise Exception("cannot simultaneously host and join a game")
# initialize pygame
pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption("Go")
fpsLimit = 60
running = True
# initialize screen/board dimensions
screen_size = pygame.display.get_desktop_sizes()[0][1] * 3 / 4
screen = pygame.display.set_mode((screen_size, screen_size))
board_size = args.size
tile_size = screen_size / (board_size + 1)
stone_radius = tile_size / 2
tengen_size = max(tile_size / 8, 2)
ghost_thickness = max(int(tile_size / 15), 2)
board_pos = [tile_size * i for i in range(1, board_size + 1)]
center_coord = board_pos[board_size // 2]
# initialize game state
if args.host or args.join:
    online = True
else:
    online = False
board = [[-1 for i in range(board_size)] for j in range(board_size)]
colors = ("black", "white")
turn = False
click_release = True
pass_release = True
stone_list = [set(), set()]
board_history = {}
pass_count = 0
ghost_pos = [0, 0]
opponent_turn = True
# draws the game board and pieces
def show_board():
    screen.fill((240, 170, 100))
    # draw board lines
    for i in range(board_size):
        pygame.draw.line(screen, "black", (board_pos[i], board_pos[0]), (board_pos[i], board_pos[board_size - 1]), 2)
        pygame.draw.line(screen, "black", (board_pos[0], board_pos[i]), (board_pos[board_size - 1], board_pos[i]), 2)
    # draw tengen if board dimensions are odd
    if board_size % 2:
        pygame.draw.circle(screen, "black", (center_coord, center_coord), tengen_size)
    # draw side and corner points if board is 19x19
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
# get position of ghost in board coordinates
def get_ghost(raw_x, raw_y):
    mouse_x = clamp(((raw_x + stone_radius) // tile_size), 1, board_size) - 1
    mouse_y = clamp(((raw_y + stone_radius) // tile_size), 1, board_size) - 1
    return [int(mouse_x), int(mouse_y)]
# draw ghost at point (x, y)
def show_ghost(x, y):
    pygame.draw.circle(screen, colors[turn], (board_pos[x], board_pos[y]), stone_radius, ghost_thickness)
# get the neighbors of a given point
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
# get the set of points of a given point's group, along with the group's types of neighbors
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
# update the board's state based on the given turn and move point, and return the next turn
def do_move(point, turn,):
    opponent = not turn
    if not(board[point[0]][point[1]] == -1):
        return turn
    board[point[0]][point[1]] = turn
    checked = set()
    killed_by_move = set()
    # get all stones that would be killed on this move
    for neighbor in neighborhood(point):
        if board[neighbor[0]][neighbor[1]] == opponent and neighbor not in checked:
            group, alive = get_group(neighbor)
            checked.update(group)
            if not alive[2]:
                killed_by_move.update(group)
    # prevent suicide
    if not killed_by_move:
        self_group, self_alive = get_group(point)
        if not self_alive[2]:
            board[point[0]][point[1]] = -1
            return turn
    # update list of stones that would result after move
    new_stone_list = [stone_list[0].copy(), stone_list[1].copy()]
    new_stone_list[turn].add(point)
    new_stone_list[opponent] -= killed_by_move
    new_stone_count = len(new_stone_list[0]) + len(new_stone_list[1])
    history = board_history.get(new_stone_count)
    # check if board state has occured previously in the game; if so, reject it
    if not history:
        board_history.update({new_stone_count: [new_stone_list]})
    else:
        for board_state in history:
            if new_stone_list[0] == board_state[0] and new_stone_list[1] == board_state[1]:
                board[point[0]][point[1]] = -1
                return turn
        history.append(new_stone_list)
    # move successful; update stone list and board state
    stone_list.clear()
    stone_list.append(new_stone_list[0])
    stone_list.append(new_stone_list[1])
    for death in killed_by_move:
        board[death[0]][death[1]] = -1
    return not turn
# determine the score of the game and print result
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
# call drawing functions
def display_frame():
    show_board()
    show_ghost(ghost_pos[0], ghost_pos[1])
    pygame.display.flip()
# send game initialization variables to opponent if hosting
def send_init_list(sock, size, bonus, turn):
    size_str = str(size)
    size_len = str(len(size_str))
    bonus_str = str(bonus)
    bonus_len = str(len(bonus_str))
    if turn:
        color = "1"
    else:
        color = "0"
    string = size_len + size_str + bonus_len + bonus_str + color 
    sock.sendall(string.encode())
# get game initialization variables
def get_init(sock, sel, size, bonus, turn):
    if args.join:
        while True:
            if ready_for_read(sock, sel):
                size = int(get_prepend_bytes(sock).decode())
                bonus = float(get_prepend_bytes(sock).decode())
                turn = int(get_bytes(sock, 1).decode())
                if turn == 0:
                    turn = True
                else:
                    turn = False
                return (size, bonus, turn)
# get the specified amount of bytes from the connection
def get_bytes(sock, n):
    data = b""
    data_len = 0
    while data_len < n:
        tmp = sock.recv(n - data_len)
        if not tmp:
            return False
        data += tmp
        data_len = len(data)
    return data
# get the full message from the connection when prepended with length
def get_prepend_bytes(sock):
    msg_len_raw = get_bytes(sock, 1)
    if not msg_len_raw:
        return False
    msg_len = int(msg_len_raw.decode())
    msg = get_bytes(sock, msg_len)
    if not msg:
        return False
    return msg
# get move tuple that opponent has sent
def receive_move(sock):
    data = get_prepend_bytes(sock)
    if not data:
        return False
    nums = data.decode().split()
    return (int(nums[0]), int(nums[1]))
# send move tuple to opponent
def send_move(sock, move):
    move_data = (str(move[0]) + " " + str(move[1])).encode()
    move_prepend = len(move_data)
    sock.sendall(str(move_prepend).encode() + move_data)
# check whether the given socket is ready for reading
# the given selector must have the socket registered for read events
def ready_for_read(sock, sel):
    ready = False
    events = sel.select(0)
    for key, mask in events:
        if key.fd == sock.fileno() and mask & selectors.EVENT_READ:
            ready = True
    return ready
# return connection to opponent and socket selector if hosting
def get_connection():
    # create listening socket
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind(("127.0.0.1", 33322))
    lsock.listen(1)
    # create selector to poll for events
    sel = selectors.DefaultSelector()
    sel.register(lsock, selectors.EVENT_READ, data=None)
    # listen for connection attempts, or quit
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # user has closed pygame window
                sel.unregister(lsock)
                lsock.close()
                return (False, False)
        if ready_for_read(lsock, sel):
            connection, address = lsock.accept()
            sel.unregister(lsock)
            sel.register(connection, selectors.EVENT_READ, data=None)
            lsock.close()
            return (connection, sel)
# return connection to host and socket selector if joining
def connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 33322))

    sel = selectors.DefaultSelector()
    sel.register(sock, selectors.EVENT_READ, data=None)
    return (sock, sel)

if args.host:
    connection, selector = get_connection()
    if not connection:
        running = False
if args.join:
    connection, selector = connect()
if online:
    if connection:
        if args.host:
            send_init_list(connection, 67, 2.33, True)
            print(receive_move(connection))
        if args.join:
            send_move(connection, (3,99))
            print(get_init(connection, selector, 3, 3, 3))
        print("successful connection")
        connection.close()
        running = False
# main game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    # poll for mouse input to get ghost location
    ghost_pos = get_ghost(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])

    display_frame()

    clicks = pygame.mouse.get_pressed()
    # player has attempted to place a stone, move must be handled
    if clicks[0] and click_release:
        click_release = False
        new_turn = do_move(tuple(ghost_pos), turn)
        if not(turn == new_turn):
            pass_count = 0
        turn = new_turn
    if not clicks[0]:
        click_release = True

    keys = pygame.key.get_pressed()
    # player has passed their turn
    if keys[pygame.K_SPACE] and pass_release:
        pass_release = False
        pass_count += 1
        if pass_count == 2:
            running = score_game()
        turn = not turn
    if not keys[pygame.K_SPACE]:
        pass_release = True
    # player has pressed debug button
    if keys[pygame.K_d]:
        debug()

    clock.tick(fpsLimit)
    
pygame.quit()
