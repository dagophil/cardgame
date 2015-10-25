import events
import logging


class CardGameModel(object):

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._player_order = None
        self._cards = None
        self._trump = None
        self.username = None
        self._current_round = 0
        self._said_tricks = []
        self._played_cards = []

    def notify(self, event):
        """
        Handle the event.
        :param event: the event
        """

        if isinstance(event, events.StartGameEvent):
            self._player_order = event.player_order

        elif isinstance(event, events.NewCardsEvent):
            self._cards = event.cards
            self._said_tricks = []

        elif isinstance(event, events.NewTrumpEvent):
            self._trump = event.trump

        elif isinstance(event, events.AskTricksEvent):
            self._current_round = event.n
            self._played_cards = []

        elif isinstance(event, events.PlayerSaidTricksEvent):
            self._said_tricks.append(event.n)

        elif isinstance(event, events.UserSaysTricksEvent):
            last_player = len(self._said_tricks)+1 == len(self._player_order)
            invalid_num_tricks = sum(self._said_tricks) + event.n == self._current_round
            if last_player and invalid_num_tricks:
                self._ev_manager.post(events.InvalidNumTricksEvent(event.n))
            else:
                self._ev_manager.post(events.SayTricksEvent(event.n))

        elif isinstance(event, events.UserSaysCardEvent):
            played_colors = [card[0] for card in self._played_cards if card[0] not in ["W", "L"]]

            if len(played_colors) > 0:
                # Some has played a suit.
                follow_suit = played_colors[0][0]
                if event.card[0] not in ["W", "L", follow_suit]:
                    # The player did not follow suit. Check if this is ok.
                    player_colors = [card[0] for card in self._cards]
                    if follow_suit in player_colors:
                        self._ev_manager.post(events.NotFollowedSuitEvent())
                        return

            self._ev_manager.post(events.SayCardEvent(event.card))

        elif isinstance(event, events.WinTrickEvent):
            self._played_cards = []

        elif isinstance(event, events.SayCardEvent):
            self._played_cards.append(event.card)
            if event.card in self._cards:
                self._cards.remove(event.card)
            else:
                logging.warning("Tried to remove the card %s from the played cards, but it is not in the list.")

        elif isinstance(event, events.PlayerPlayedCardEvent):
            self._played_cards.append(event.card)
