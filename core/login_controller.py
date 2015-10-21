import events
from login_model import LoginModel
from login_view import LoginView
from pygame_controller import PygameController
import pygame
import common as cmn
import logging
from widgets import TextInput
from game_network_controller import GameNetworkController
import os


def _dummyfunc(s):
    return False


def _isalnum(s):
    return s.isalnum()


def _isdigit(s):
    return s.isdigit()


def _isallowed(s):
    return all(c in cmn.ALLOWED_CHARS for c in s)


_allowed_funcs = {"username": _isalnum,
                  "host": _isallowed,
                  "port": _isdigit}


class LoginController(PygameController):
    """
    The GUI controller.
    """

    def __init__(self, ev_manager, model, view, login_file):
        super(LoginController, self).__init__(ev_manager, view)
        assert isinstance(model, LoginModel)
        self._model = model
        self._network_controller = GameNetworkController(self._ev_manager, buffer_messages=True)
        self._network_running = False
        self._login_filename = login_file

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        super(LoginController, self).notify(event)

        if isinstance(event, events.InitEvent):
            pass
            # Load previous login data.
            if os.path.isfile(self._login_filename):
                with open(self._login_filename) as f:
                    lines = [line.strip() for line in f]
                lines = [l for l in lines if len(l) > 0]
                lines = [l.split(": ") for l in lines]
                if any(len(l) != 2 for l in lines):
                    logging.warning("Could not parse login file '%s'." % self._login_filename)
                    return
                try:
                    login_data = dict(lines)
                except ValueError:
                    logging.warning("Could not parse login file '%s'." % self._login_filename)
                    return
                # Check for the allowed values.
                for k in login_data:
                    v = login_data[k]
                    if k in _allowed_funcs:
                        if _allowed_funcs[k](v):
                            self._ev_manager.post(events.AttachCharEvent(None, k, v))
                        else:
                            logging.warning("Value '%s' for %s not allowed." % (v, k))

        elif isinstance(event, events.TickEvent):
            for pygame_event in self.events():
                if pygame_event.type == pygame.KEYDOWN:
                    if pygame_event.key == pygame.K_RETURN:
                        self._ev_manager.post(events.LoginRequestedEvent())
                    elif pygame_event.key == pygame.K_TAB:
                        self.view.focus_next()
                    else:
                        # Append the pressed key to the focused input field (or delete the last char on backspace).
                        # TODO: If a key stays pressed for a short time, repeatedly print the key.
                        w = self.view.get_focused_widget()
                        if isinstance(w, TextInput):
                            t = w.default_text
                            valid = _allowed_funcs.get(t, _dummyfunc)
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

        elif isinstance(event, events.AcceptedUsernameEvent):
            logging.warning("TODO: Continue after the username was accepted.")
