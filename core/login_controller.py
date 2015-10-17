import events
from login_model import LoginModel
from login_view import LoginView
from pygame_controller import PygameController
import pygame
import common as cmn
import logging
from widgets import TextInput, Button


def isalnum(s):
    return s.isalnum()


def isdigit(s):
    return s.isdigit()


def isallowed(s):
    return s in cmn.ALLOWED_CHARS


class LoginController(PygameController):
    """
    The GUI controller.
    """

    def __init__(self, ev_manager, model, view):
        super(LoginController, self).__init__(ev_manager, view)
        assert isinstance(model, LoginModel)
        self._model = model

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        super(LoginController, self).notify(event)

        if isinstance(event, events.TickEvent):
            for pygame_event in self.events():
                if pygame_event.type == pygame.KEYDOWN:
                    # Append the pressed key to the focused input field (or delete the last char on backspace).
                    # TODO: If a key stays pressed for a short time, repeatedly print the key.
                    d = {"username": isalnum,
                         "host": isallowed,
                         "port": isdigit}
                    w = self.view.get_focused_widget()
                    if isinstance(w, TextInput):
                        t = w.default_text
                        valid = d[t]
                        if valid(pygame_event.unicode):
                            self._ev_manager.post(events.AttachCharEvent(w, t, pygame_event.unicode))
                        elif pygame_event.key == pygame.K_BACKSPACE:
                            self._ev_manager.post(events.RemoveCharEvent(w, t, 1))

        elif isinstance(event, events.LoginRequestedEvent):
            logging.debug("Login requested: Username: '%s', host: '%s', port: '%s'" %
                          (self._model.username, self._model.host, self._model.port))
