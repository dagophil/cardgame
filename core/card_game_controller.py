from pygame_controller import PygameController
from card_game_model import CardGameModel
from game_network_controller import GameNetworkController
import events
import logging


class CardGameController(PygameController):
    """
    The GUI controller.
    """

    def __init__(self, ev_manager, model, view, network_controller):
        super(CardGameController, self).__init__(ev_manager, view)
        assert isinstance(model, CardGameModel)
        assert isinstance(network_controller, GameNetworkController)
        self._model = model
        self._network_controller = network_controller

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

