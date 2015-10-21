from pygame_controller import PygameController
from card_game_model import CardGameModel
from game_network_controller import GameNetworkController


class CardGameController(PygameController):
    """
    The GUI controller.
    """

    def __init__(self, ev_manager, model, view, network_controller):
        super(CardGameController, self).__init__(ev_manager, view)
        assert isinstance(model, CardGameModel)
        self._model = model
        self._network_controller = network_controller
