import pygame


class PygameView(object):

    def __init__(self):
        self.width = None
        self.height = None
        self._screen = None

    def init(self, width, height):
        self.width = width
        self.height = height
        pygame.display.set_mode((self.width, self.height))
        self._screen = pygame.display.get_surface()

    def exit(self):
        pygame.quit()
