from pygame_controller import PygameController
from card_game_model import CardGameModel
from card_game_view import CardGameView
from game_network_controller import GameNetworkController
import events
import logging


class CardGameController(PygameController):
    """
    The GUI controller.
    """

    def __init__(self, ev_manager, model, view, network_controller, username):
        super(CardGameController, self).__init__(ev_manager, view)
        assert isinstance(model, CardGameModel)
        assert isinstance(view, CardGameView)
        assert isinstance(network_controller, GameNetworkController)
        self._model = model
        self._network_controller = network_controller
        self._model.username = username
        self._view = view
        self._view.username = username

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        super(CardGameController, self).notify(event)

        if isinstance(event, events.InitModelEvent):
            self._network_controller.buffer_messages = False

        elif isinstance(event, events.PlayerJoinedEvent):
            logging.warning("TODO: Handle player '%s' joined." % event.name)

        # elif isinstance(event, events.StartGameEvent):

        elif isinstance(event, events.NewCardsEvent):
            self._view.show_cards(event.cards)

        elif isinstance(event, events.NewTrumpEvent):
            self._view.show_trump(event.trump)

        elif isinstance(event, events.AskTrumpEvent):
            self._view.ask_trump()
