import pygame
class Board:
    def __init__(self, board_size):
        self.screen_size = pygame.display.get_desktop_sizes()[0][1] * 3 / 4
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size))
        self.board_size = board_size
        self.tile_size = self.screen_size / (self.board_size + 1)
        self.stone_radius = self.tile_size / 2
        self.tengen_size = max(self.tile_size / 8, 2)
        self.ghost_thickness = max(int(self.tile_size / 15), 2)
