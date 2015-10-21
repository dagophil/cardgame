import pygame
import events
import logging
from pygame_view import PygameView
from resource_manager import ResourceManager
from widgets import Widget, TextInput, Button, ImageWidget
import copy
from actions import DelayedAction, FadeOutAction


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

        bg_widget = self.create_widgets()
        super(LoginView, self).__init__(ev_manager, bg_widget)

    def create_widgets(self):
        """
        Create the widgets and return the one that contains them all.
        :return:
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
        btn = self._create_button((0, 3*INPUT_OFFSET), (w, 100), "Login")

        def btn_clicked(x, y):
            self._ev_manager.post(events.LoginRequestedEvent())
        btn.handle_clicked = btn_clicked
        input_container.add_widget(btn)

        # Create the connection failed warning.
        self._connection_failed_warning = self._create_warning((400, 100), "Connection failed")
        bg_widget.add_widget(self._connection_failed_warning)
        self._username_taken_warning = self._create_warning((400, 100), "Username already taken")
        bg_widget.add_widget(self._username_taken_warning)

        return bg_widget

    def _create_button(self, position, size, text, z_index=0):
        """
        Create a button with centered text.
        :param position: the position
        :param size: the size
        :param text: the text
        :param z_index: the z index
        :return: the button
        """
        w, h = size
        btn_font_obj = self._font.render(text, True, (255, 255, 255, 255))
        offset_x = (w - btn_font_obj.get_width()) / 2
        offset_y = (h - btn_font_obj.get_height()) / 2
        btn_bg = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        btn_bg.fill((0, 0, 0, 128))
        btn_bg.blit(btn_font_obj, (offset_x, offset_y))
        btn_hover = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        btn_hover.fill((0, 0, 0, 160))
        btn_hover.blit(btn_font_obj, (offset_x, offset_y))
        btn_pressed = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        btn_pressed.fill((0, 0, 0, 200))
        btn_pressed.blit(btn_font_obj, (offset_x, offset_y))
        btn = Button(position, size, z_index, btn_bg, btn_hover, btn_pressed)
        return btn

    def _create_warning(self, size, text, z_index=10, fill=(0, 0, 0, 160)):
        """
        Create a warning widget that is centered on the screen.
        :param size: the size
        :param text: the text
        :param fill: the fill color
        :return: the widget
        """
        # Create the widget.
        w, h = size
        x = (self.screen.get_width() - w) / 2
        y = (self.screen.get_height() - h) / 2
        btn_font_obj = self._font.render(text, True, (255, 255, 255, 255))
        offset_x = (w - btn_font_obj.get_width()) / 2
        offset_y = (h - btn_font_obj.get_height()) / 2
        warning_bg = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        warning_bg.fill(fill)
        warning_bg.blit(btn_font_obj, (offset_x, offset_y))
        warning = ImageWidget((x, y), (w, h), z_index, warning_bg, visible=False)

        # Attach the click function.
        def warning_clicked(x, y):
            warning.hide()
            warning.clear_actions()
        warning.handle_clicked = warning_clicked

        return warning

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
