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
            if int(line) == cmn.handshake_fun(self._id):
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
        self.send_all_others("%d#%s" % (cmn.NEW_USER, self.username))

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
            self.send_all_others("%d#%s#%s" % (cmn.CHAT, self.username, msg))
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

    def __init__(self, num_players):
        self.num_players = num_players
        self._num_rounds = 60 / self.num_players  # integer division will floor this
        self._clients = None
        self._player_ids = None
        self._deck = None
        self._round = 0
        self._tricks = None
        self._player_cards = None
        self.current_player = 0
        self.trump = None

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
        self._tricks = [0] * self.num_players
        logging.info("Playing round %d." % self._round)

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
        self.trump = "W"

        # Send the trump to all players.
        logging.info("The trump suit is %s." % cmn.COLOR_NAMES[self.trump])
        self.current_client.send_all("%d#%s" % (cmn.FOUND_TRUMP, self.trump))

        if self.trump == "W":
            # Ask the first player for the trump.
            self.current_client.send("%d#0" % cmn.ASK_TRUMP)
        else:
            # Ask the first player how many tricks he makes.
            self.current_client.send("%d#%d" % (cmn.ASK_TRICKS, self._round))

    def say_trump(self, trump):
        """
        Save the trump and ask the first player to say the number of tricks.
        :param trump: the trump
        """
        self.trump = trump
        logging.info("%s chose the trump suit %s." % (self.current_player_username, trump))
        self.current_client.send_all("%d#%s" % (cmn.FOUND_TRUMP, self.trump))
        self.current_client.send("%d#%d" % (cmn.ASK_TRICKS, self._round))

    def say_tricks(self, num_tricks):
        """
        Save the number of tricks that the current player said and ask the next player.
        If all players said, ask the next player to play his card.
        :param num_tricks: the number of tricks
        """
        # Check if the number of tricks is valid.
        num_tricks_in_range = 0 <= num_tricks <= self._round
        num_tricks_equals_round = sum(self._tricks) + num_tricks == self._round
        if (not num_tricks_in_range) or (self.is_last_player and num_tricks_equals_round):
            logging.warning("%s said invalid number of tricks: %d" % (self.current_player_username, num_tricks))
            self.current_client.send("%d#%d" % (cmn.INVALID_NUM_TRICKS, num_tricks))
            return

        # Tell all players what was played.
        logging.info("%s said %d tricks." % (self.current_player_username, num_tricks))
        self.current_client.send_all_others("%d#%s#%d" % (cmn.PLAYER_SAID_TRICKS, self.current_player_username, num_tricks))

        # Save the said number.
        self._tricks[self.current_player] = num_tricks
        self.current_player = (self.current_player+1) % self.num_players

        # Ask the next player to say the tricks or to play the card.
        if not self.is_first_player:
            self.current_client.send("%d#%d" % (cmn.ASK_TRICKS, self._round))
        else:
            self.current_client.send("%d#%s" % (cmn.ASK_CARD, str(self.current_player_cards)))

    def say_card(self, card):
        """
        Save the card that the current player played and ask the next player.
        If all players played, find out who won.
        :param card: the card
        """
        logging.warning("%s said %s, and now we have to handle this." % (self.current_player_username, card))


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
    reactor.listenTCP(args.port, ClientConnector(WizardGame(args.num_players)))
    logging.info("Server is running.")
    reactor.run()
    logging.info("Shutdown successful.")


if __name__ == "__main__":
    main(parser.parse_args())
    sys.exit(0)
