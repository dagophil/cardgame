import sys
import argparse
import logging
import random
import json
from twisted.internet.protocol import Factory
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import core.common as cmn


class ClientConnection(LineReceiver):
    """
    Protocol:
    - Initial handshake:
      Server sends client id (random integer n in [0, 99999]), client responds with handshake function.
      Server sends WAIT_FOR_NAME, client responds with the username (must be alpha numeric).
      Once the username is valid, the client is accepted.
    - After being accepted, all messages have the format "msgid#msg".
    """

    def __init__(self, factory, host, port):
        assert isinstance(factory, ClientConnector)
        assert isinstance(host, str)
        assert isinstance(port, int)
        self._factory = factory
        self._host = host
        self._port = port
        self._id = factory.rand_ids.pop()
        self._state = cmn.PENDING
        self.username = "Unknown%d" % self._id

    @property
    def hostname(self):
        """
        Return the hostname in the format ip:port.
        :return: the hostname
        """
        return "%s:%d" % (self._host, self._port)

    @property
    def clients(self):
        """
        Return the clients.
        :return: the clients
        """
        return self._factory.clients

    @property
    def game(self):
        """
        Return the game.
        :return: the game
        """
        return self._factory.game

    def send(self, line):
        """
        Convert line to a string and send it.
        :param line: something to be sent
        """
        line = str(line)
        logging.debug("Send '%s' to %s" % (line, self.hostname))
        self.sendLine(line)

    def send_all(self, line):
        """
        Convert line to a string and send it to all clients.
        :param line: something to be sent
        """
        for client_id in self.clients:
            client = self.clients[client_id]
            client.send(line)

    def send_all_others(self, line):
        """
        Convert line to a string and send it to all clients except the current.
        :param line: something to be sent
        """
        for client_id in self.clients:
            if client_id != self._id:
                client = self.clients[client_id]
                client.send(line)

    def connectionMade(self):
        """
        Do the initial handshake (send the client id).
        """
        logging.info("New connection: %s" % self.hostname)
        self.send(self._id)

    def connectionLost(self, reason=connectionDone):
        """
        Remove the client from the client list.
        :param reason:
        """
        logging.info("Lost connection: %s" % self.hostname)
        if self._id in self.clients:
            del self.clients[self._id]
            self.send_all_others("%d#%s" % (cmn.USER_LEFT, self.username))

    def lineReceived(self, line):
        """
        Parse the client messages and call the according functions.
        :param line: the received line
        """
        # Remove unwanted characters from the input.
        assert isinstance(line, str)
        line = line.translate(cmn.CHAR_TRANS_TABLE)
        logging.debug("Received '%s' from %s" % (line, self.hostname))

        if self._state != cmn.ACCEPTED:
            # Check if the server is full.
            if len(self.clients) == self.game.num_players:
                logging.info("Refused connection from %s because the server is full." % self.hostname)
                self.send("Sorry, the server is full.")
                self.stopProducing()
                return

        if self._state == cmn.PENDING:
            # Check if the handshake number is correct.
            non_wizard = False
            try:
                line = int(line)
            except ValueError:
                non_wizard = True
            if not non_wizard and line == cmn.handshake_fun(self._id):
                self._state = cmn.WAIT_FOR_NAME
                self.send(self._state)
            else:
                logging.warning("Non-wizard connection from %s" % self.hostname)
                self.send("Your are not a wizard cardgame client.")
                self.stopProducing()

        elif self._state == cmn.WAIT_FOR_NAME:
            # Check if the name is valid.
            if not line.isalnum():
                logging.info("Refused username '%s' from %s" % (line, self.hostname))
                self.send(cmn.FORBIDDEN_USERNAME)
                return

            # Check if the name is already taken.
            for client_id in self.clients:
                client = self.clients[client_id]
                if client.username.lower() == line.lower():
                    logging.info("Refused already taken username '%s' from %s" % (line, self.hostname))
                    self.send(cmn.TAKEN_USERNAME)
                    return

            # Accept the user.
            self._accept_user(line)

        elif self._state == cmn.ACCEPTED:
            # Handle the message.
            self._handle_message(line)

        else:
            logging.warning("Unknown state: %d" % self._state)

    def _accept_user(self, username):
        """
        Accept the current client and start the game if there are enough players.
        :param username: the username
        """
        # Accept the player.
        self.username = username
        self._state = cmn.ACCEPTED
        self.clients[self._id] = self
        logging.info("%s chooses username '%s'" % (self.hostname, self.username))
        self.send_all("%d#%s" % (cmn.NEW_USER, self.username))

        if len(self.clients) == self.game.num_players:
            self._start_game()

    def _start_game(self):
        """
        Start the game.
        """
        logging.info("Starting the game.")
        self.game.start(self.clients)

    def _handle_message(self, line):
        """
        Split the given line into message id and message and give them to _handle_valid_message.
        :param line: the line
        """
        if "#" not in line:
            logging.warning("%s sent invalid message '%s'" % (self.username, line))
            self.send("%d#%s" % (cmn.UNKNOWN_MESSAGE, line))
        else:
            i = line.index("#")
            msg_id, msg = line[:i], line[i+1:]
            try:
                msg_id = int(msg_id)
            except ValueError:
                logging.warning("%s used non-integer message id in message '%s'" % (self.username, line))
                self.send("%d#%s" % (cmn.UNKNOWN_MESSAGE, line))
                return
            self._handle_valid_message(msg_id, msg)

    def _handle_valid_message(self, msg_id, msg):
        """
        Handle the message.
        :param msg_id: the message id
        :param msg: the message
        """
        if msg_id == cmn.CHAT:
            # Attach the username and send the message to the other players. Since the username is alpha numeric, it
            # cannot contain "#", so we can use that to separate the username from the message.
            self.send_all("%d#%s#%s" % (cmn.CHAT, self.username, msg))
            return

        if msg_id in [cmn.SAY_TRUMP, cmn.SAY_TRICKS, cmn.SAY_CARD]:
            # Make sure that the game started and it is the client's turn.
            if not self.game.started:
                logging.warning("%s tried to play, but the game did not start." % self.username)
                self.send("%d#>noone<" % cmn.NOT_YOUR_TURN)
                return
            elif self.game.current_client != self:
                logging.warning("%s tried to play, but it is not his turn." % self.username)
                self.send("%d#%s" % (cmn.NOT_YOUR_TURN, self.game.current_player_username))
                return

        if msg_id == cmn.SAY_TRUMP and self.game.state != cmn.WAIT_FOR_SAY_TRUMP \
                or msg_id == cmn.SAY_TRICKS and self.game.state != cmn.WAIT_FOR_SAY_TRICKS \
                or msg_id == cmn.SAY_CARD and self.game.state != cmn.WAIT_FOR_SAY_CARD:
            logging.warning("%s tried to make a move that is not possible right now." % self.username)
            self.send("%d#%d" % (cmn.INVALID_MOVE, msg_id))
            return

        if msg_id == cmn.SAY_TRUMP:
            # Parse the trump.
            if self.game.trump != "W" or msg not in ["C", "S", "H", "D"]:
                logging.warning("%s tried to say the invalid trump '%s'." % (self.username, msg))
                self.send("%d#%s" % (cmn.INVALID_TRUMP, msg))
                return
            self.game.say_trump(msg)

        elif msg_id == cmn.SAY_TRICKS:
            # Parse the number of tricks.
            try:
                num_tricks = int(msg)
            except ValueError:
                logging.warning("%s used non-integer for number of tricks in message '%s'" % (self.username, msg))
                self.send("%d#%s" % (cmn.UNKNOWN_MESSAGE, msg))
                return
            self.game.say_tricks(num_tricks)

        elif msg_id == cmn.SAY_CARD:
            # Parse the played card.
            if msg not in self.game.current_player_cards:
                logging.warning("%s tried to play the card '%s' without having this card." % (self.username, msg))
                self.send("%d#%s" % (cmn.INVALID_CARD, msg))
                return
            self.game.say_card(msg)

        else:
            logging.warning("Unhandled msg id '%d' with msg '%s' from %s" % (msg_id, msg, self.hostname))


class WizardGame(object):
    """
    Holds and manages the game states.
    """

    def __init__(self, num_players, num_rounds=None):
        self.num_players = num_players
        self._num_rounds = 60 / self.num_players  # integer division will floor this
        if num_rounds is not None:
            if num_rounds > self._num_rounds:
                logging.warning("Tried to set number of rounds to %d, but the maximum is %d." % (num_rounds, self._num_rounds))
            else:
                self._num_rounds = num_rounds
        self._clients = None
        self._player_ids = None
        self._deck = None
        self._round = 0
        self._said_tricks = None
        self._made_tricks = None
        self._player_cards = None
        self._trick_cards = None
        self.current_player = 0
        self.trump = None
        self._points = []
        self.state = None

    @staticmethod
    def _create_cards():
        """
        Create and return a list with a full card deck.
        A single card is a string "CV", where C ist the color (C, D, H, or S) and V is the value (2, 3, 4, 5, 6, 7, 8,
        9, T, J, Q, K, or A), or a String "CV", where C is W or L (wizard or loser) and V is its id (0, 1, 2, or 3).
        :return: the deck
        """
        return [c+n for c in "CDHS" for n in "23456789TJQKA"] + [c+n for c in "WL" for n in "0123"]

    def start(self, clients):
        """
        Find a random player order and start the first round.
        :param clients: the clients
        """
        # Find a random player order.
        self._clients = clients
        self._player_ids = self._clients.keys()
        random.shuffle(self._player_ids)
        logging.info("The seat order is %s." % ", ".join(self._clients[p].username for p in self._player_ids))

        # Send the player order to all clients.
        msg = json.dumps([self._clients[i].username for i in self._player_ids])
        for client_id in clients:
            client = clients[client_id]
            client.send("%d#%s" % (cmn.START_GAME, msg))

        # Start the first round.
        self._next_round()

    @property
    def current_player_id(self):
        """
        Return the player id of the current player.
        :return: the player id
        """
        return self._player_ids[self.current_player]

    @property
    def current_client(self):
        """
        Return the client of the current player.
        :return: the client
        """
        return self._clients[self.current_player_id]

    @property
    def current_player_username(self):
        """
        Return the username of the current player.
        :return: the username
        """
        return self.current_client.username

    @property
    def current_player_cards(self):
        """
        Return the cards of the current player.
        :return: the cards
        """
        return self._player_cards[self.current_player]

    @property
    def started(self):
        """
        Return whether the game has started or not.
        :return: True if the game has started else False
        """
        return self._round > 0

    @property
    def is_first_player(self):
        """
        Return True if the current player is the first player.
        :return: whether the current player is the first player
        """
        return self.current_player == self._round % self.num_players

    @property
    def is_last_player(self):
        """
        Return True if the current player is the last player.
        :return: whether the current player is the last player
        """
        return (self.current_player+1) % self.num_players == self._round % self.num_players

    def _next_round(self):
        """
        Increase the round number, get a new deck and shuffle it and send the cards to each player.
        """
        self._round += 1
        self.current_player = self._round % self.num_players
        self._said_tricks = [0] * self.num_players
        self._made_tricks = [0] * self.num_players
        self._trick_cards = []
        logging.info("Playing round %d of %d." % (self._round, self._num_rounds))
        logging.info("%s starts." % self.current_player_username)

        # Shuffle the cards.
        self._deck = self._create_cards()
        random.shuffle(self._deck)

        # Send the cards to the players.
        self._player_cards = [None] * self.num_players
        for i, player_id in enumerate(self._player_ids):
            client = self._clients[player_id]
            self._player_cards[i], self._deck = self._deck[:self._round], self._deck[self._round:]
            msg = json.dumps(self._player_cards[i])
            client.send("%d#%s" % (cmn.CARDS, msg))

        # Find the trump.
        r = random.randint(1, 60)
        if r <= 13:
            self.trump = "D"
        elif r <= 26:
            self.trump = "H"
        elif r <= 39:
            self.trump = "S"
        elif r <= 52:
            self.trump = "C"
        elif r <= 56:
            self.trump = "L"
        else:
            self.trump = "W"

        # Send the trump to all players.
        logging.info("The trump suit is %s." % cmn.COLOR_NAMES[self.trump])
        self.current_client.send_all("%d#%s" % (cmn.FOUND_TRUMP, self.trump))

        if self.trump == "W":
            # Ask the first player for the trump.
            self.state = cmn.WAIT_FOR_SAY_TRUMP
            self.current_client.send("%d#0" % cmn.ASK_TRUMP)
        else:
            # Ask the first player how many tricks he makes.
            self.state = cmn.WAIT_FOR_SAY_TRICKS
            self.current_client.send("%d#%d" % (cmn.ASK_TRICKS, self._round))

    def say_trump(self, trump):
        """
        Save the trump and ask the first player to say the number of tricks.
        :param trump: the trump
        """
        self.trump = trump
        logging.info("%s chose the trump suit %s." % (self.current_player_username, trump))
        self.current_client.send_all("%d#%s" % (cmn.FOUND_TRUMP, self.trump))
        self.state = cmn.WAIT_FOR_SAY_TRICKS
        self.current_client.send("%d#%d" % (cmn.ASK_TRICKS, self._round))

    def say_tricks(self, num_tricks):
        """
        Save the number of tricks that the current player said and ask the next player.
        If all players said, ask the next player to play his card.
        :param num_tricks: the number of tricks
        """
        # Check if the number of tricks is valid.
        num_tricks_in_range = 0 <= num_tricks <= self._round
        num_tricks_equals_round = sum(self._said_tricks) + num_tricks == self._round
        if (not num_tricks_in_range) or (self.is_last_player and num_tricks_equals_round):
            logging.warning("%s said invalid number of tricks: %d" % (self.current_player_username, num_tricks))
            self.current_client.send("%d#%d" % (cmn.INVALID_NUM_TRICKS, num_tricks))
            return

        # Tell all players what was played.
        logging.info("%s said %d tricks." % (self.current_player_username, num_tricks))
        self.current_client.send_all("%d#%s#%d" % (cmn.PLAYER_SAID_TRICKS, self.current_player_username, num_tricks))

        # Save the said number.
        self._said_tricks[self.current_player] = num_tricks
        self.current_player = (self.current_player+1) % self.num_players

        # Ask the next player to say the tricks or to play the card.
        if not self.is_first_player:
            self.state = cmn.WAIT_FOR_SAY_TRICKS
            self.current_client.send("%d#%d" % (cmn.ASK_TRICKS, self._round))
        else:
            self.state = cmn.WAIT_FOR_SAY_CARD
            self.current_client.send("%d#%s" % (cmn.ASK_CARD, json.dumps(self.current_player_cards)))

    def say_card(self, played_card):
        """
        Save the card that the current player played and ask the next player.
        If all players played, find out who won.
        :param played_card: the played card
        """
        # Check if the player followed suit.
        played_colors = [card[0] for card in self._trick_cards if card[0] not in ["W", "L"]]
        if len(played_colors) > 0:
            # Someone has played a suit already. This is not always the case:
            # There is no suit if the first cards where wizards / losers and when the first card has not been played at
            # all.
            follow_suit = played_colors[0][0]
            if played_card[0] not in ["W", "L", follow_suit]:
                # The player did not follow suit. This is only okay, if none of the hand cards are of the suit.
                player_colors = [card[0] for card in self.current_player_cards]
                if follow_suit in player_colors:
                    logging.warning("%s did not follow suit." % self.current_player_username)
                    self.current_client.send("%d#%s#%s" % (cmn.NOT_FOLLOWED_SUIT, follow_suit, played_card))
                    return

        # Tell all players what was played.
        logging.info("%s played %s." % (self.current_player_username, played_card))
        self.current_client.send_all("%d#%s#%s" % (cmn.PLAYER_PLAYED_CARD, self.current_player_username, played_card))

        # Save the played card.
        self._trick_cards.append(played_card)
        self.current_player_cards.remove(played_card)
        self.current_player = (self.current_player+1) % self.num_players

        # Ask the next player to play the card or find the winner.
        if len(self._trick_cards) < self.num_players:
            self.current_client.send("%d#%s" % (cmn.ASK_CARD, json.dumps(self.current_player_cards)))
        else:
            self._find_trick_winner()

    def _find_trick_winner(self):
        """
        Find the winner of the current trick.
        """
        played_colors = [card[0] for card in self._trick_cards]
        if "W" in played_colors:
            # Someone played a wizard => first wizard wins.
            winner_index = played_colors.index("W")
            winner = (self.current_player + winner_index) % self.num_players
        elif all(c == "L" for c in played_colors):
            # Everyone played a jester => last player wins.
            winner = (self.current_player - 1) % self.num_players
        elif self.trump != "L" and any(card[0] == self.trump for card in self._trick_cards):
            # No wizards, but trump was played => the highest trump wins.
            trump_values = [(card[1], i) for i, card in enumerate(self._trick_cards) if card[0] == self.trump]
            trump_values = [(cmn.NUMERIC_VALUES[x[0]], x[1]) for x in trump_values]
            winner_index = max(trump_values)[1]
            winner = (self.current_player+winner_index) % self.num_players
        else:
            # No wizards and no trump => the highest card that followed suit wins.
            follow_suit = (c for c in played_colors if c not in ["W", "L"]).next()
            suit_values = [(card[1], i) for i, card in enumerate(self._trick_cards) if card[0] == follow_suit]
            suit_values = [(cmn.NUMERIC_VALUES[x[0]], x[1]) for x in suit_values]
            winner_index = max(suit_values)[1]
            winner = (self.current_player+winner_index) % self.num_players

        # The next trick starts with the winner.
        self.current_player = winner
        self._trick_cards = []

        # Save the winner.
        self._made_tricks[winner] += 1
        logging.info("%s wins the trick." % self.current_player_username)
        self.current_client.send_all("%d#%s" % (cmn.WINS_TRICK, self.current_player_username))

        # Ask the next player to play the card or compute the result of this round.
        if sum(self._made_tricks) < self._round:
            self.current_client.send("%d#%s" % (cmn.ASK_CARD, json.dumps(self.current_player_cards)))
        else:
            self._compute_round_result()

    def _compute_round_result(self):
        """
        Compute the result of the current round.
        """
        points = []
        for i in xrange(self.num_players):
            diff = abs(self._said_tricks[i] - self._made_tricks[i])
            if diff == 0:
                points.append(20 + 10*self._made_tricks[i])
            else:
                points.append(-10*diff)

        logging.info("Round ended. The round points in seat order: %s." % ", ".join(str(x) for x in points))
        self.current_client.send_all("%d#%s" % (cmn.MADE_POINTS, json.dumps(points)))
        self._points.append(points)

        # Start the next round or compute the final results.
        if self._round < self._num_rounds:
            self._next_round()
        else:
            self._compute_final_result()

    def _compute_final_result(self):
        """
        Compute the final result of the game.
        """
        points = [sum(x) for x in zip(*self._points)]
        logging.info("The final points in seat order: %s." % ", ".join(str(x) for x in points))
        self.current_client.send_all("%d#%s" % (cmn.FINAL_POINTS, json.dumps(points)))

        # Find the winners.
        max_points = max(points)
        search_start = 0
        winners = []
        for i in xrange(points.count(max_points)):
            winner_index = points.index(max_points, search_start)
            search_start = winner_index + 1
            winner_client = self._clients[self._player_ids[winner_index]]
            winners.append((winner_client.username, max_points))

        # Announce the winners.
        self.current_client.send_all("%d#%s" % (cmn.FINAL_WINNERS, json.dumps(winners)))
        if len(winners) == 1:
            logging.info("The winners: %s." % ", ".join(w[0] for w in winners))

        # Exit the game.
        reactor.stop()


class ClientConnector(Factory):
    """
    Creates a ClientConnection for each incoming client.
    """

    def __init__(self, game):
        assert isinstance(game, WizardGame)
        self.rand_ids = range(100000)
        random.shuffle(self.rand_ids)
        self.clients = {}
        self.game = game

    def buildProtocol(self, addr):
        return ClientConnection(self, addr.host, addr.port)


parser = argparse.ArgumentParser(description="Wizard cardgame - Server")
parser.add_argument("--port", type=int, required=True,
                    help="listen port for incoming connections")
parser.add_argument("-n", "--num_players", type=int, required=True,
                    help="number of players")
parser.add_argument("-k", "--num_rounds", type=int, default=None,
                    help="number of rounds, default: floor(60/num_players)")
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="show verbose output")
parser.add_argument("--debug", action="store_true")


def main(args):
    """
    Set the logging level and start the reactor loop.
    :param args: command line arguments
    """
    # Set the logging level and create the logger.
    if args.verbose == 0:
        logging_level = logging.WARNING
    else:
        logging_level = logging.INFO
    if args.debug:
        logging_level = logging.DEBUG
    logging_handler = logging.StreamHandler(sys.stdout)
    logging_handler.setFormatter(cmn.ColoredFormatter())
    logging.root.addHandler(logging_handler)
    logging.root.setLevel(logging_level)

    # Check the number of players.
    assert args.num_players > 0

    # Start the reactor.
    reactor.listenTCP(args.port, ClientConnector(WizardGame(args.num_players, args.num_rounds)))
    logging.info("Server is running.")
    reactor.run()
    logging.info("Shutdown successful.")


if __name__ == "__main__":
    main(parser.parse_args())
    sys.exit(0)
