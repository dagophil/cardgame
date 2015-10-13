import events
from login_model import LoginModel
from login_view import LoginView
from pygame_controller import PygameController
import pygame
import common as cmn
import logging


CURSOR_POINTER = pygame.cursors.arrow
CURSOR_HOVER = pygame.cursors.tri_left


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
        super(LoginController, self).__init__(ev_manager)
        assert isinstance(model, LoginModel)
        assert isinstance(view, LoginView)
        self._model = model
        self._view = view

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        super(LoginController, self).notify(event)

        if isinstance(event, events.TickEvent):
            for pygame_event in self.events():
                if pygame_event.type == pygame.MOUSEMOTION:
                    # Change the cursor when an input field is hovered.
                    sx, sy = pygame_event.pos
                    hov = self._view.object_at(sx, sy)
                    if hov is None:
                        pygame.mouse.set_cursor(*CURSOR_POINTER)
                    else:
                        pygame.mouse.set_cursor(*CURSOR_HOVER)
                elif pygame_event.type == pygame.MOUSEBUTTONDOWN:
                    # Focus the current input field.
                    sx, sy = pygame_event.pos
                    hov = self._view.object_at(sx, sy)
                    self._view.focused = hov
                elif pygame_event.type == pygame.KEYDOWN:
                    # Append the pressed key to the focused input field (or delete the last char on backspace).
                    # TODO: If a key stays pressed for a short time, repeatedly print the key.
                    d = {"username": (self._view.username_input, isalnum),
                         "host": (self._view.host_input, isallowed),
                         "port": (self._view.port_input, isdigit)}
                    if self._view.focused in d:
                        input_field, valid = d[self._view.focused]
                        if valid(pygame_event.unicode):
                            input_field.text += pygame_event.unicode
                        elif pygame_event.key == pygame.K_BACKSPACE:
                            input_field.text = input_field.text[:-1]
