import pygame


BLINK_TIME = 0.5


class Widget(object):
    """
    Parent of all widget objects.
    """

    def __init__(self, position, size, z_index):
        self.position = position
        self.size = size
        self.z_index = z_index
        self.widgets = []

    def add_widget(self, w):
        """
        Add the widget to the container.
        :param w: the widget
        """
        assert isinstance(w, Widget)
        if w not in self.widgets:
            self.widgets.append(w)

    def remove_widget(self, w):
        """
        Remove the widget from the container.
        :param w: the widget
        """
        if w in self.widgets:
            self.widgets.remove(w)

    def is_hovered(self, x, y):
        """
        Return whether (x, y) is inside the widget.
        :param x: x coordinate
        :param y: y coordinate
        :return: whether (x, y) is inside the widget
        """
        x_in = self.position[0] <= x <= self.position[0] + self.size[0]
        y_in = self.position[1] <= y <= self.position[1] + self.size[1]
        return x_in and y_in

    def get_hovered(self, x, y):
        """
        Return the widget that is hovered by (x, y).
        If self is not hovered, None is returned.
        If self is hovered and does not contain other widgets, self is returned.
        If self is hovered and contains other widgets, the hovered sub widget with the largest z_index is returned.
        If none of the sub widgets is hovered, self is returned.
        :param x: x coordinate
        :param y: y coordinate
        :return: the hovered widget
        """
        if not self.is_hovered(x, y):
            return None
        else:
            x -= self.position[0]
            y -= self.position[1]
            hovered_widgets = [w for w in self.widgets if w.is_hovered(x, y)]
            if len(hovered_widgets) == 0:
                return self
            else:
                hovered_widgets.sort(key=lambda ww: ww.z_index)
                return hovered_widgets[-1].get_hovered(x, y)

    def render(self, surface):
        """
        Render the sub widgets on the surface.
        Subclasses of Widget should call this at the end of their own render() method.
        :param surface: the surface
        """
        sub_surface = surface.subsurface(self.position, self.size)
        for w in self.widgets:
            w.render(sub_surface)


class TextInput(Widget):
    """
    A widget for text input.
    """

    def __init__(self, position, width, z_index, font, padding=(0, 0, 0, 0), color=(255, 255, 255), fill=(0, 0, 0, 0),
                 text="", default_text="", default_font=None):
        self.font = font
        self.padding = padding
        self.color = color
        self.fill = fill
        self.text = text
        self.default_text = default_text
        if default_font is None:
            self.default_font = font
        else:
            self.default_font = default_font
        self._blink_time = 0
        self._focused = False

        width += padding[1] + padding[3]
        height = font.get_linesize() + padding[0] + padding[2]
        super(TextInput, self).__init__(position, (width, height), z_index)

    @property
    def focused(self):
        return self._focused

    @focused.setter
    def focused(self, f):
        self._focused = f
        self._blink_time = 0

    def blink(self, elapsed_time):
        """
        Update the blink time.
        :param elapsed_time: time since last frame
        """
        self._blink_time += elapsed_time
        self._blink_time %= 2*BLINK_TIME

    def render(self, surface):
        """
        Render the widget to the given surface at the given position.
        :param surface: the surface
        """
        s = pygame.Surface(self.size, flags=pygame.SRCALPHA)
        s.fill(self.fill)
        if self._blink_time < BLINK_TIME and self.focused:
            app = "|"
        else:
            app = ""
        if len(self.text) > 0 or self.focused:
            font_obj = self.font.render(self.text+app, True, self.color)
        else:
            font_obj = self.default_font.render(self.default_text+app, True, self.color)

        s.blit(font_obj, (self.padding[3], self.padding[0]))
        surface.blit(s, self.position)


class Button(Widget):
    """
    A button widget.
    """

    def __init__(self, position, size, z_index, default_img, hover_img, pressed_img):
        super(Button, self).__init__(position, size, z_index)
