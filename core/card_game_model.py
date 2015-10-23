import events


class CardGameModel(object):

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._player_order = None
        self._cards = None
        self._trump = None
        self.username = None

    def notify(self, event):
        """
        Handle the event.
        :param event: the event
        """

        if isinstance(event, events.StartGameEvent):
            self._player_order = event.player_order

        elif isinstance(event, events.NewCardsEvent):
            self._cards = event.cards

        elif isinstance(event, events.NewTrumpEvent):
            self._trump = event.trump
