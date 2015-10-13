import pygame


class TextInput(object):
    """
    A widget for text input.
    """

    def __init__(self, font, width, padding=(0, 0, 0, 0), color=(255, 255, 255), fill=(0, 0, 0, 0), text="",
                 default_text="", default_font=None):
        self.font = font
        self.width = width
        self.padding = padding
        self.color = color
        self.fill = fill
        self.text = text
        self.default_text = default_text
        if default_font is None:
            self.default_font = font
        else:
            self.default_font = default_font

    @property
    def render_width(self):
        return self.width + self.padding[1] + self.padding[3]

    @property
    def render_height(self):
        return self.font.get_linesize() + self.padding[0] + self.padding[2]

    @property
    def offset(self):
        return self.padding[3], self.padding[0]

    def render(self, surface, position):
        """
        Render the widget to the given surface at the given position.
        :param surface: the surface
        :param position: the position
        """
        s = pygame.Surface((self.render_width, self.render_height), flags=pygame.SRCALPHA)
        s.fill(self.fill)
        if len(self.text) > 0:
            font_obj = self.font.render(self.text, True, self.color)
        else:
            font_obj = self.default_font.render(self.default_text, True, self.color)
        s.blit(font_obj, self.offset)
        surface.blit(s, position)
