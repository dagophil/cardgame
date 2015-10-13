import pygame


class PygameView(object):
    """
    This view should be subclassed by all pygame views. It enables safe access to the screen.
    """

    _screen = None

    @property
    def screen(self):
        """
        Return the screen.
        :return: the screen
        """
        return PygameView._screen

    @staticmethod
    def init(width, height):
        """
        Initialize the screen.
        :param width: screen width
        :param height: screen height
        """
        PygameView._screen = pygame.display.set_mode((width, height))
