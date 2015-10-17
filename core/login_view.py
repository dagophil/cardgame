import pygame
import events
import logging
from pygame_view import PygameView
from resource_manager import ResourceManager
from widgets import Widget, TextInput
import copy


BACKGROUND_IMAGE = "resources/bg_green.png"
FONT = "resources/fonts/opensans/OpenSans-Regular.ttf"
FONT_ITALIC = "resources/fonts/opensans/OpenSans-Italic.ttf"
FONT_BOLD = "resources/fonts/opensans/OpenSans-Bold.ttf"
FONT_SIZE = 16
INPUT_FORE_COLOR = (255, 255, 255)
INPUT_FILL_COLOR = (0, 0, 0, 128)
INPUT_WIDTH = 200
INPUT_PADDING = (5, 5, 5, 5)
INPUT_OFFSET = 40


class LoginView(PygameView):
    """
    The pygame login view.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._resource_manager = ResourceManager.instance()

        self._focused = None  # the focused widget

        # Get the background image.
        self._background = self._resource_manager.get_image(BACKGROUND_IMAGE, self.screen.get_size())

        # Get the fonts.
        self._font = self._resource_manager.get_font(FONT, FONT_SIZE)
        self._default_font = self._resource_manager.get_font(FONT_ITALIC, FONT_SIZE)

        # Create the container widget.
        x = (self.screen.get_width() - INPUT_WIDTH - INPUT_PADDING[1] - INPUT_PADDING[3]) / 2
        y = self.screen.get_height() / 2
        w = INPUT_WIDTH + INPUT_PADDING[1] + INPUT_PADDING[3]
        h = self.screen.get_height() - y
        self._container_widget = Widget((x, y), (w, h), 0)

        # Create the input widgets.
        username_input = TextInput((0, 0), INPUT_WIDTH, 0, self._font, padding=INPUT_PADDING, color=INPUT_FORE_COLOR,
                                   fill=INPUT_FILL_COLOR, default_text="username",
                                   default_font=self._default_font)
        host_input = copy.copy(username_input)
        host_input.default_text = "host"
        host_input.position = (0, INPUT_OFFSET)
        port_input = copy.copy(username_input)
        port_input.default_text = "port"
        port_input.position = (0, 2*INPUT_OFFSET)
        self._container_widget.add_widget(username_input)
        self._container_widget.add_widget(host_input)
        self._container_widget.add_widget(port_input)

    def focus(self, s):
        """
        Set the focus to the given widget.
        :param s: the widget
        """
        assert s is None or isinstance(s, TextInput)
        for w in self._container_widget.widgets:
            w.focused = False
        self._focused = s
        if s is not None:
            s.focused = True

    @property
    def focused(self):
        """
        Return the focused object.
        :return: the focused object
        """
        if self._focused is None:
            return None
        else:
            return self._focused.default_text

    def get_hovered(self, x, y):
        """
        Return the hovered widget.
        :param x: x coordinate
        :param y: y coordinate
        :return: the hovered widget
        """
        hov = self._container_widget.get_hovered(x, y)
        if hov is self._container_widget:
            hov = None
        return hov

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        if isinstance(event, events.InitEvent):
            pass
        elif isinstance(event, events.TickEvent):
            # Draw the background.
            self.screen.blit(self._background, (0, 0))

            # Update the blinking cursor.
            for w in self._container_widget.widgets:
                w.blink(event.elapsed_time)

            # Render the widgets.
            self._container_widget.render(self.screen)

            # Flip the buffer.
            pygame.display.flip()

        elif isinstance(event, events.AttachCharEvent):
            self._focused.text += event.char
        elif isinstance(event, events.RemoveCharEvent):
            self._focused.text = self._focused.text[:-event.n]
