import events
from collections import deque
import pygame
from pygame_view import PygameView


class PygameController(object):
    """
    This controller should be subclasses by the controllers that handle the pygame events. All pygame events are passed
    into an internal list that can be obtained (and cleared) using the events() method. If the pygame.QUIT event is
    posted, CloseCurrentModelEvent(None) is sent to the event manager.
    """

    def __init__(self, ev_manager, model, view):
        assert isinstance(ev_manager, events.EventManager)
        assert isinstance(view, PygameView)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._pygame_events = deque()
        self._model = model
        self._view = view

    @property
    def model(self):
        return self._model

    @property
    def view(self):
        return self._view

    def events(self):
        """
        Return the pygame events and clear the list.
        :return: the pygame events
        """
        l = list(self._pygame_events)
        self._pygame_events.clear()
        return l

    def notify(self, event):
        """
        If the given event is a tick event, all pygame events except pygame.QUIT are stored in the event list. If the
        pygame.QUIT event occurs, the CloseCurrentModel event is posted on the event manager.
        :param event: the event
        """
        if isinstance(event, events.TickEvent):
            for pygame_event in pygame.event.get():
                if pygame_event.type == pygame.QUIT:
                    self._ev_manager.post(events.CloseCurrentModelEvent(None))
                else:
                    # Forward the mouse events to the view.
                    if pygame_event.type == pygame.MOUSEMOTION:
                        sx, sy = pygame_event.pos
                        self.view.hover(sx, sy)
                    elif pygame_event.type == pygame.MOUSEBUTTONDOWN:
                        sx, sy = pygame_event.pos
                        self.view.mouse_down(sx, sy)
                    elif pygame_event.type == pygame.MOUSEBUTTONUP:
                        sx, sy = pygame_event.pos
                        self.view.mouse_up(sx, sy)
                    self._pygame_events.append(pygame_event)
