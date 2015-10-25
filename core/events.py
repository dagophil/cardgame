import collections
import logging


class Event(object):
    pass


class InitModelEvent(Event):
    pass


class TickEvent(Event):
    def __init__(self, elapsed_time):
        self.elapsed_time = elapsed_time


class ExitEvent(Event):
    pass


class CloseCurrentModelEvent(Event):
    def __init__(self, next_model_name, *args, **kwargs):
        self.next_model_name = next_model_name
        self.next_model_args = args
        self.next_model_kwargs = kwargs


class AttachCharEvent(Event):
    def __init__(self, entity, entity_name, char):
        self.entity = entity
        self.entity_name = entity_name
        self.char = char


class RemoveCharEvent(Event):
    def __init__(self, entity, entity_name, n):
        self.entity = entity
        self.entity_name = entity_name
        self.n = n


class LoginRequestedEvent(Event):
    pass


class ConnectionMadeEvent(Event):
    pass


class ConnectionLostEvent(Event):
    pass


class ConnectionFailedEvent(Event):
    pass


class LineReceivedEvent(Event):
    def __init__(self, line):
        self.line = line


class InvalidUsernameEvent(Event):
    pass


class TakenUsernameEvent(Event):
    pass


class AcceptedUsernameEvent(Event):
    pass


class AppCrashedEvent(Event):
    pass


class PlayerJoinedEvent(Event):
    def __init__(self, name):
        self.name = name


class PlayerLeftEvent(Event):
    def __init__(self, name):
        self.name = name


class StartGameEvent(Event):
    def __init__(self, player_order):
        self.player_order = player_order


class NewCardsEvent(Event):
    def __init__(self, cards):
        self.cards = cards


class AskTrumpEvent(Event):
    pass

class ChooseTrumpEvent(Event):
    def __init__(self, trump):
        self.trump = trump


class NewTrumpEvent(Event):
    def __init__(self, trump):
        self.trump = trump


class AskTricksEvent(Event):
    def __init__(self, n):
        self.n = n


class UserSaysTricksEvent(Event):
    def __init__(self, n):
        self.n = n


class SayTricksEvent(Event):
    def __init__(self, n):
        self.n = n


class PlayerSaidTricksEvent(Event):
    def __init__(self, player, n):
        self.player = player
        self.n = n


class InvalidNumTricksEvent(Event):
    def __init__(self, n):
        self.n = n


class AskCardEvent(Event):
    pass


class UserSaysCardEvent(Event):
    def __init__(self, card):
        self.card = card


class WinTrickEvent(Event):
    def __init__(self, player):
        self.player = player


class NotFollowedSuitEvent(Event):
    pass


class SayCardEvent(Event):
    def __init__(self, card):
        self.card = card


class PlayerPlayedCardEvent(Event):
    def __init__(self, player, card):
        self.player = player
        self.card = card


class DelayedEvent(Event):
    def __init__(self, time, event):
        self.time = time
        self.event = event


class RoundPointsEvent(Event):
    def __init__(self, points):
        self.points = points


class CallFunctionEvent(Event):
    """
    If a CallFunctionEvent is posted on the event manager, the event manager simply calls the function with the stored
    arguments. These events are useful in combination with DelayedEvent.
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs


class EventManager(object):
    """
    Receives event and post them to the listeners.
    """

    def __init__(self):
        self._listeners = {}
        self._queue = collections.deque()
        self._next_id = 0
        self._delayed_events = []
        self.next_model_name = None
        self.next_model_args = ()
        self.next_model_kwargs = {}

    def register_listener(self, listener):
        """
        Register a listener.
        :param listener: the listener
        :return: the listener id
        """
        listener_id = self._next_id
        self._next_id += 1
        self._listeners[listener] = listener_id
        logging.debug("Registered listener %s with id %d." % (listener.__class__.__name__, listener_id))
        return listener_id

    def unregister_listener(self, listener):
        """
        Unregister a listener.
        :param listener: the listener
        """
        if listener in self._listeners:
            del self._listeners[listener]
            logging.debug("Unregistered listener %s." % listener.__class__.__name__)

    def post(self, event):
        """
        Add an event to the event queue.
        :param event: the event
        """
        # If a CallFunctionEvent is posted, simply call the function.
        if isinstance(event, CallFunctionEvent):
            event.func(*event.args, **event.kwargs)
            return

        # Delayed events are handled in a separate list.
        if isinstance(event, DelayedEvent):
            self._delayed_events.append(event)
        else:
            self._queue.append(event)

        # Update the timestamp on the delayed events. Post them to the real queue, if their time has come.
        if isinstance(event, TickEvent):
            for ev in self._delayed_events:
                assert isinstance(ev, DelayedEvent)
                ev.time -= event.elapsed_time
                if ev.time <= 0:
                    ev.time = 0
                    self.post(ev.event)
            self._delayed_events = [ev for ev in self._delayed_events if ev.time > 0]

        if isinstance(event, TickEvent) or isinstance(event, InitModelEvent):
            while len(self._queue) > 0:
                ev = self._queue.popleft()
                # Iterate over a copy of the dict, so even from within the loop, listeners can delete themselves.
                for l in list(self._listeners):
                    l.notify(ev)

        elif isinstance(event, CloseCurrentModelEvent):
            self.next_model_name = event.next_model_name
            self.next_model_args = event.next_model_args
            self.next_model_kwargs = event.next_model_kwargs

        elif isinstance(event, AppCrashedEvent):
            for l in list(self._listeners):
                l.notify(event)
