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

    def render(self, surface, position, focused=False, blink=False):
        """
        Render the widget to the given surface at the given position.
        :param surface: the surface
        :param position: the position
        :param focused: if this is True, the default text is not shown
        :param blink: if this is True and the widget is focused, append a blinking cursor
        """
        s = pygame.Surface((self.render_width, self.render_height), flags=pygame.SRCALPHA)
        s.fill(self.fill)
        if blink and focused:
            app = "|"
        else:
            app = ""
        if len(self.text) > 0 or focused:
            font_obj = self.font.render(self.text+app, True, self.color)
        else:
            font_obj = self.default_font.render(self.default_text+app, True, self.color)
        s.blit(font_obj, self.offset)
        surface.blit(s, position)
