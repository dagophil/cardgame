import pygame
import events
import logging
from pygame_view import PygameView
from resource_manager import ResourceManager
from widgets import Widget, TextInput, Button, ImageWidget
import copy
from actions import DelayedAction, FadeOutAction
import special_widgets


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
        self._rm = ResourceManager.instance()
        self._font = self._rm.get_font(FONT, FONT_SIZE)
        self._default_font = self._rm.get_font(FONT_ITALIC, FONT_SIZE)
        self._text_inputs = None
        self._connection_failed_warning = None
        self._username_taken_warning = None

        bg_widget = self._create_widgets()
        super(LoginView, self).__init__(ev_manager, bg_widget)

    def _create_widgets(self):
        """
        Create the widgets and return the one that contains them all.
        :return: the background widget
        """
        # Create the background widget.
        bg = self._rm.get_image(BACKGROUND_IMAGE, self.screen.get_size())
        bg_widget = ImageWidget((0, 0), self.screen.get_size(), -1, bg)

        # Create the container for the input widgets.
        x = (self.screen.get_width() - INPUT_WIDTH - INPUT_PADDING[1] - INPUT_PADDING[3]) / 2
        y = self.screen.get_height() / 2
        w = INPUT_WIDTH + INPUT_PADDING[1] + INPUT_PADDING[3]
        h = self.screen.get_height() - y
        input_container = Widget((x, y), (w, h), 0)
        bg_widget.add_widget(input_container)

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
        input_container.add_widget(username_input)
        input_container.add_widget(host_input)
        input_container.add_widget(port_input)
        self._text_inputs = {"username": username_input, "host": host_input, "port": port_input}

        # Create the button widget.
        btn = special_widgets.simple_button((0, 3*INPUT_OFFSET), (w, 100), "Login", self._font)

        def btn_clicked(x, y):
            self._ev_manager.post(events.LoginRequestedEvent())
        btn.handle_clicked = btn_clicked
        input_container.add_widget(btn)

        # Create the connection failed warning.
        self._connection_failed_warning = special_widgets.warning_widget((400, 100), self.screen.get_size(),
                                                                         "Connection failed", self._font)
        bg_widget.add_widget(self._connection_failed_warning)
        self._username_taken_warning = special_widgets.warning_widget((400, 100), self.screen.get_size(),
                                                                      "Username already taken", self._font)
        bg_widget.add_widget(self._username_taken_warning)

        return bg_widget

    def focus_next(self):
        """
        Move the focus to the next input widget.
        """
        if self._text_inputs["username"].focused:
            self._text_inputs["username"].focused = False
            self._text_inputs["host"].focused = True
        elif self._text_inputs["host"].focused:
            self._text_inputs["host"].focused = False
            self._text_inputs["port"].focused = True
        elif self._text_inputs["port"].focused:
            self._text_inputs["port"].focused = False
            self._text_inputs["username"].focused = True
        else:
            self._text_inputs["username"].focused = True

    def notify(self, event):
        """
        Attach and remove chars from the text inputs.
        :param event: the event
        """
        super(LoginView, self).notify(event)

        if isinstance(event, events.AttachCharEvent):
            if event.entity is None:
                ent = self._text_inputs.get(event.entity_name, None)
            else:
                ent = event.entity
            if isinstance(ent, TextInput):
                ent.text += event.char

        elif isinstance(event, events.RemoveCharEvent):
            if event.entity is None:
                ent = self._text_inputs.get(event.entity_name, None)
            else:
                ent = event.entity
            if isinstance(ent, TextInput):
                ent.text = ent.text[:-event.n]

        elif isinstance(event, events.ConnectionFailedEvent):
            self._connection_failed_warning.clear_actions()
            self._connection_failed_warning.show()
            self._connection_failed_warning.add_action(DelayedAction(3, FadeOutAction(0.5)))

        elif isinstance(event, events.TakenUsernameEvent):
            self._username_taken_warning.clear_actions()
            self._username_taken_warning.show()
            self._username_taken_warning.add_action(DelayedAction(3, FadeOutAction(0.5)))

        elif isinstance(event, events.CloseCurrentModelEvent):
            self._ev_manager.unregister_listener(self)
