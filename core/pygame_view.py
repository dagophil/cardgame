import pygame
import events
from widgets import Widget, TextInput, Button


CURSOR_POINTER = pygame.cursors.arrow
CURSOR_HOVER = pygame.cursors.tri_left


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

    def __init__(self, ev_manager, background_widget):
        assert isinstance(ev_manager, events.EventManager)
        assert isinstance(background_widget, Widget)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._background_widget = background_widget

    def hover(self, x, y):
        """
        Set the hovered state on the widgets and change the mouse if something is hovered.
        :param x: x coordinate
        :param y: y coordinate
        """
        self._background_widget.hover(x, y)
        hov = self._background_widget.get_widget_at(x, y)
        if hov is not None and hov != self._background_widget and \
                (isinstance(hov, TextInput) or isinstance(hov, Button)):
            pygame.mouse.set_cursor(*CURSOR_HOVER)
        else:
            pygame.mouse.set_cursor(*CURSOR_POINTER)

    def mouse_down(self, x, y):
        """
        Pass the mouse down event to the background widget.
        :param x: x coordinate
        :param y: y coordinate
        """
        self._background_widget.mouse_down(x, y)

    def mouse_up(self, x, y):
        """
        Pass the mouse up event to the background widget.
        :param x: x coordinate
        :param y: y coordinate
        """
        self._background_widget.mouse_up(x, y)

    def get_focused_widget(self):
        """

        :return:
        """
        return self._background_widget.get_focused_widget()

    def render(self, surface):
        """
        Render the view.
        :param surface: the surface
        """
        self._background_widget.render(surface)

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        if isinstance(event, events.TickEvent):
            self._background_widget.update(event.elapsed_time)
            self.render(self.screen)
            pygame.display.flip()
