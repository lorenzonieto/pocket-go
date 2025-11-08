import pygame
class Board:
    def __init__(self, board_size, bonus, online, turn):
        self.screen_size = pygame.display.get_desktop_sizes()[0][1] * 3 / 4
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size))
        self.board_size = board_size
        self.tile_size = self.screen_size / (self.board_size + 1)
        self.stone_radius = self.tile_size / 2
        self.tengen_size = max(self.tile_size / 8, 2)
        self.ghost_thickness = max(int(self.tile_size / 15), 2)
        self.board_pos = [self.tile_size * i for i in range(1, board_size + 1)]
        self.bonus = bonus
        self.center_coord = self.board_pos[self.board_size // 2]
        self.online = online
        self.board = [[-1 for i in range(self.board_size)] for j in range(self.board_size)]
        self.colors = ("black", "white")
        self.turn = turn
        self.stone_list = [set(), set()]
        self.board_history = {}
        self.pass_count = 0
        self.ghost_pos = [0, 0]

    def show_board(self):
        self.screen.fill((240, 170, 100))
        # draw board lines
        for i in range(self.board_size):
            pygame.draw.line(self.screen, "black", (self.board_pos[i], self.board_pos[0]),
                            (self.board_pos[i], self.board_pos[self.board_size - 1]), 2)
            pygame.draw.line(self.screen, "black", (self.board_pos[0], self.board_pos[i]),
                            (self.board_pos[self.board_size - 1], self.board_pos[i]), 2)
        # draw tengen if board dimensions are odd
        if self.board_size % 2:
            pygame.draw.circle(self.screen, "black", (self.center_coord, self.center_coord), self.tengen_size)
        # draw side and corner points if board is 19x19
        if self.board_size == 19:
            for i in range(3):
                for j in range(3):
                    x_coord = self.board_pos[(i * 6) + 3]
                    y_coord = self.board_pos[(j * 6) + 3]
                    pygame.draw.circle(self.screen, "black", (x_coord, y_coord), self.tengen_size)
        # draw pieces
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] < 0:
                    continue
                else:
                    pygame.draw.circle(self.screen, self.colors[self.board[i][j]], 
                                    (self.board_pos[i], self.board_pos[j]), self.stone_radius)
    def clamp(self, n, floor, ceiling):
        return min(max(n, floor), ceiling)
    # set position of ghost in board coordinates
    def set_ghost(self, raw_x, raw_y):
        mouse_x = self.clamp(((raw_x + self.stone_radius) // self.tile_size), 1, self.board_size) - 1
        mouse_y = self.clamp(((raw_y + self.stone_radius) // self.tile_size), 1, self.board_size) - 1
        self.ghost_pos[0] = int(mouse_x)
        self.ghost_pos[1] = int(mouse_y)
    # draw ghost at point (x, y)
    def show_ghost(self, x, y):
        pygame.draw.circle(self.screen, self.colors[self.turn], (self.board_pos[x], self.board_pos[y]),
                           self.stone_radius, self.ghost_thickness)
    # get the neighbors of a given point
    def neighborhood(self, point):
        neighbors = []
        if point[0] > 0:
            neighbors.append((point[0] - 1, point[1]))
        if point[0] < (self.board_size - 1):
            neighbors.append((point[0] + 1, point[1]))
        if point[1] > 0:
            neighbors.append((point[0], point[1] - 1))
        if point[1] < (self.board_size - 1):
            neighbors.append((point[0], point[1] + 1))
        return neighbors
    # get the set of points of a given point's group, along with the group's types of neighbors
    def get_group(self, point):
        group = set()
        unexplored = {point}
        color = self.board[point[0]][point[1]]
        neighbor_types = [False, False, False]
        while unexplored:
            new = unexplored.pop()
            group.add(new)
            for neighbor in self.neighborhood(new):
                if (self.board[neighbor[0]][neighbor[1]] == color) and not(neighbor in unexplored):
                    if not(neighbor in group):
                        unexplored.add(neighbor)
                        neighbor_types[color] = True
                else:
                    neighbor_types[self.board[neighbor[0]][neighbor[1]]] = True
        return group, neighbor_types
    def debug(self):
        #print(self.get_group(tuple(self.ghost_pos)))
        return
    # update the board's state based on the given turn and move point, and return the next turn
    def do_move(self):
        point = tuple(self.ghost_pos)
        opponent = not self.turn
        if not(self.board[point[0]][point[1]] == -1):
            return
        self.board[point[0]][point[1]] = self.turn
        checked = set()
        killed_by_move = set()
        # get all stones that would be killed on this move
        for neighbor in self.neighborhood(point):
            if self.board[neighbor[0]][neighbor[1]] == opponent and neighbor not in checked:
                group, alive = self.get_group(neighbor)
                checked.update(group)
                if not alive[2]:
                    killed_by_move.update(group)
        # prevent suicide
        if not killed_by_move:
            self_group, self_alive = self.get_group(point)
            if not self_alive[2]:
                self.board[point[0]][point[1]] = -1
                return
        # update list of stones that would result after move
        new_stone_list = [self.stone_list[0].copy(), self.stone_list[1].copy()]
        new_stone_list[self.turn].add(point)
        new_stone_list[opponent] -= killed_by_move
        new_stone_count = len(new_stone_list[0]) + len(new_stone_list[1])
        # check if board state has occured previouslt in the game; if so, reject it
        history = self.board_history.get(new_stone_count)
        if not history:
            self.board_history.update({new_stone_count: [new_stone_list]})
        else:
            for board_state in history:
                if new_stone_list[0] == board_state[0] and new_stone_list[1] == board_state[1]:
                    self.board[point[0]][point[1]] = -1
                    return
            history.append(new_stone_list)
        # move successful; update stone list and board state
        self.stone_list.clear()
        self.stone_list.append(new_stone_list[0])
        self.stone_list.append(new_stone_list[1])
        for death in killed_by_move:
            self.board[death[0]][death[1]] = -1
        self.turn = not self.turn
    # determine the score of the game and print result
    def score_game(self):
        if self.bonus.is_integer():
            score = [0, int(self.bonus)]
        else:
            score = [0, self.bonus]
        scored = set()
        for i in range(self.board_size):
            for j in range(self.board_size):
                if not((i, j) in scored):
                    color = self.board[i][j]
                    group, state = self.get_group((i, j))
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
    def display_frame(self):
        self.show_board()
        self.show_ghost(self.ghost_pos[0], self.ghost_pos[1])
        pygame.display.flip()