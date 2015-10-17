import events
from login_model import LoginModel
from login_view import LoginView
from pygame_controller import PygameController
import pygame
import common as cmn
import logging
from widgets import TextInput, Button
from game_network_controller import GameNetworkController


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
        self._network_controller = GameNetworkController(self._ev_manager)
        self._network_running = False

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

            # Check the username.
            if len(self._model.username) == 0:
                logging.warning("Username must not have length 0.")
                self._ev_manager.post(events.InvalidUsernameEvent())
                return
            self._network_controller.username = self._model.username

            # Check the port.
            try:
                port = int(self._model.port)
            except ValueError:
                logging.warning("Could not convert port %s to int." % self._model.port)
                return

            if self._network_running:
                # Send the new username.
                self._network_controller.update_username(self._model.username)
            else:
                # Build the connection.
                self._network_controller.connect(self._model.host, port)
                self._network_running = True

        elif isinstance(event, events.ConnectionFailedEvent) or isinstance(event, events.ConnectionLostEvent):
            self._network_running = False

        elif isinstance(event, events.TakenUsernameEvent):
            logging.warning("TODO: Show a message that the username was taken.")

        elif isinstance(event, events.AcceptedUsernameEvent):
            logging.warning("TODO: Continue after the username was accepted.")
