import events
from login_model import LoginModel
from login_view import LoginView
from pygame_controller import PygameController
import pygame


CURSOR_POINTER = pygame.cursors.arrow
CURSOR_HOVER = pygame.cursors.tri_left


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
                    sx, sy = pygame_event.pos
                    hov = self._view.object_at(sx, sy)
                    self._view.focus(hov)
