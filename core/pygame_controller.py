import events
from collections import deque
import pygame


class PygameController(object):
    """
    This controller should be subclasses by the controllers that handle the pygame events. All pygame events are passed
    into an internal list that can be obtained (and cleared) using the events() method. If the pygame.QUIT event is
    posted, CloseCurrentModelEvent(None) is sent to the event manager.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._pygame_events = deque()

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
                    self._pygame_events.append(pygame_event)
