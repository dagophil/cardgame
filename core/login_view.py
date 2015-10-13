import pygame
import events
import logging
from pygame_view import PygameView
from resource_manager import ResourceManager
from widgets import TextInput
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


class LoginView(PygameView):
    """
    The pygame view.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._resource_manager = ResourceManager.instance()

        self._background = self._resource_manager.get_image(BACKGROUND_IMAGE, self.screen.get_size())
        self._font = self._resource_manager.get_font(FONT, FONT_SIZE)
        self._default_font = self._resource_manager.get_font(FONT_ITALIC, FONT_SIZE)

        self._username_input = TextInput(self._font, INPUT_WIDTH, padding=INPUT_PADDING, color=INPUT_FORE_COLOR,
                                         fill=INPUT_FILL_COLOR, default_text="username",
                                         default_font=self._default_font)
        self._host_input = copy.copy(self._username_input)
        self._host_input.default_text = "host"
        self._port_input = copy.copy(self._username_input)
        self._port_input.default_text = "port"

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        if isinstance(event, events.InitEvent):
            pass
        elif isinstance(event, events.TickEvent):
            self.screen.blit(self._background, (0, 0))

            self._username_input.render(self.screen, (395, 300))
            self._host_input.render(self.screen, (395, 340))
            self._port_input.render(self.screen, (395, 380))

            pygame.display.flip()
