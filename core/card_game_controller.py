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

        # Some view changes shall first be seen some time after the last win.
        delta_time = self._view.last_win_time + 5 - self._view.elapsed_time

        if isinstance(event, events.InitModelEvent):
            self._network_controller.buffer_messages = False

        elif isinstance(event, events.PlayerJoinedEvent):
            logging.warning("TODO: Handle player '%s' joined." % event.name)

        # elif isinstance(event, events.StartGameEvent):

        elif isinstance(event, events.NewCardsEvent):
            if delta_time > 0:
                call_event = events.CallFunctionEvent(self._view.show_cards, event.cards)
                self._ev_manager.post(events.DelayedEvent(delta_time, call_event))
            else:
                self._view.show_cards(event.cards)

        elif isinstance(event, events.NewTrumpEvent):
            if delta_time > 0:
                call_event = events.CallFunctionEvent(self._view.show_trump, event.trump)
                self._ev_manager.post(events.DelayedEvent(delta_time, call_event))
            else:
                self._view.show_trump(event.trump)

        elif isinstance(event, events.AskTrumpEvent):
            if delta_time > 0:
                call_event = events.CallFunctionEvent(self._view.ask_trump)
                self._ev_manager.post(events.DelayedEvent(delta_time, call_event))
            else:
                self._view.ask_trump()

        elif isinstance(event, events.AskTricksEvent):
            if delta_time > 0:
                call_event = events.CallFunctionEvent(self._view.ask_tricks, event.n)
                self._ev_manager.post(events.DelayedEvent(delta_time, call_event))
            else:
                self._view.ask_tricks(event.n)

        elif isinstance(event, events.InvalidNumTricksEvent):
            self._view.show_invalid_num_tricks(event.n)

        elif isinstance(event, events.AskCardEvent):
            if delta_time > 0:
                call_event = events.CallFunctionEvent(self._view.show_user_move)
                self._ev_manager.post(events.DelayedEvent(delta_time, call_event))
            else:
                self._view.show_user_move()

        elif isinstance(event, events.RoundPointsEvent):
            call_event = events.CallFunctionEvent(self._view.show_round_points, event.points)
            self._ev_manager.post(events.DelayedEvent(1, call_event))

        elif isinstance(event, events.FinalWinnersEvent):
            self._view.final_winners = [w[0] for w in event.winners]
            call_event = events.CallFunctionEvent(self._view.show_final_points)
            self._ev_manager.post(events.DelayedEvent(6, call_event))

        elif isinstance(event, events.FinalPointsEvent):
            self._view.final_points = event.points
