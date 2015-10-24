import pygame
import logging


class SingletonExistsException(Exception):
    """
    This exception is thrown, when a singleton is about to be created but i already existed.
    """

    def __init__(self, *args, **kwargs):
        super(SingletonExistsException, self).__init__(*args, **kwargs)


class ResourceManager(object):
    """
    Manages all loadable files such as images, fonts, sounds, ...
    This is a singleton class, so you must not create more than one instance of this class.
    The current instance can be obtained using the instance() method, which creates the singleton on the first call.
    """

    __instance = None

    def __init__(self):
        if ResourceManager.__instance is not None:
            raise SingletonExistsException("Tried to create a ResourceManager, but there already is one.")
        ResourceManager.__instance = self

        self._images = {}
        self._fonts = {}

    @staticmethod
    def instance():
        """
        Return the instance.
        :return: the instance
        """
        if ResourceManager.__instance is None:
            ResourceManager.__instance = ResourceManager()
        return ResourceManager.__instance

    def get_image(self, filename, size=None):
        """
        Return the requested image in the requested size.
        :param filename: image filename
        :param size: size
        :return: the image
        """
        if size is None:
            size = (0, 0)
        if (filename, size) in self._images:
            return self._images[(filename, size)]
        else:
            if (filename, (0, 0)) in self._images:
                im = self._images[(filename, (0, 0))]
            else:
                try:
                    logging.debug("Loading image %s" % filename)
                    im = pygame.image.load(filename).convert_alpha()
                except pygame.error:
                    raise IOError("Could not load image %s." % filename)
                self._images[(filename, (0, 0))] = im
            if size != (0, 0):
                logging.debug("Resizing image %s to (%d, %d)." % (filename, size[0], size[1]))
                im = pygame.transform.smoothscale(im, size)
                self._images[(filename, size)] = im
            return im

    def get_font(self, font_name, size):
        """
        Return the requested font in the requested size.
        :param font_name: font name or path of .ttf file
        :param size: the size
        :return: the font
        """
        if size is None:
            size = 16
        if (font_name, size) in self._fonts:
            return self._fonts[(font_name, size)]
        else:
            if font_name in pygame.font.get_fonts():
                logging.debug("Loading system font %s in size %d." % (font_name, size))
                font = pygame.font.SysFont(font_name, size)
            else:
                logging.debug("Loading font file %s in size %d." % (font_name, size))
                font = pygame.font.Font(font_name, size)
            self._fonts[(font_name, size)] = font
            return font
