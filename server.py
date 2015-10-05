import sys
import argparse
import logging
import random
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
        self._factory = factory
        self._host = host
        self._port = port
        self._id = factory.rand_ids.pop()
        self._state = cmn.PENDING
        self._username = "Unknown%d" % self._id

    @property
    def hostname(self):
        return "%s:%d" % (self._host, self._port)

    @property
    def clients(self):
        return self._factory.clients

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
        Convert line to a string and send it to all clients (except the current).
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
            self.send_all("%d#%s" % (cmn.USER_LEFT, self._username))

    def lineReceived(self, line):
        """
        Parse the client messages and call the according functions.
        :param line: the received line
        """
        # Remove unwanted characters from the input.
        assert isinstance(line, str)
        line = line.translate(cmn.CHAR_TRANS_TABLE)
        logging.debug("Received '%s' from %s" % (line, self.hostname))

        if self._state == cmn.PENDING:
            # Send/receive the handshake numbers.
            if int(line) == cmn.handshake_fun(self._id):
                self._state = cmn.WAIT_FOR_NAME
                self.send(self._state)
            else:
                logging.warning("Non-wizard connection from %s" % self.hostname)
                self.send("Your are not a wizard cardgame client.")
                self.stopProducing()

        elif self._state == cmn.WAIT_FOR_NAME:
            # Accept or refuse the username.
            if line.isalnum():
                self._username = line
                self._state = cmn.ACCEPTED
                self.clients[self._id] = self
                logging.info("%s chooses username '%s'" % (self.hostname, self._username))
                self.send_all("%d#%s" % (cmn.NEW_USER, self._username))
            else:
                logging.info("Refused username '%s' from %s" % (line, self.hostname))
                self.send(cmn.FORBIDDEN_USERNAME)

        elif self._state == cmn.ACCEPTED:
            # Handle the message.
            self._handle_message(line)

        else:
            logging.warning("Unknown state: %d" % self._state)

    def _handle_message(self, line):
        """
        Split the given line into message id and message and give them to _handle_valid_message.
        :param line: the line
        """
        if "#" not in line:
            logging.warning("%s sent invalid message '%s'" % (self.hostname, line))
            self.send("%d#%s" % (cmn.UNKNOWN_MESSAGE, line))
        else:
            i = line.index("#")
            msg_id, msg = line[:i], line[i+1:]
            try:
                msg_id = int(msg_id)
            except ValueError:
                logging.warning("%s used non-integer message id in message '%s'" % (self.hostname, line))
                self.send("%d#%s" % (cmn.UNKNOWN_MESSAGE, line))
                return
            self._handle_valid_message(msg_id, msg)

    def _handle_valid_message(self, msg_id, msg):
        """
        Handle the message.
        :param msg_id: the message id
        :param msg: the message
        """
        logging.warning("Unhandled msg id '%d' with msg '%s' from %s" % (msg_id, msg, self.hostname))
        # TODO: React to the messages.


class ClientConnector(Factory):
    """
    Create a ClientConnection for each incoming client.
    """

    def __init__(self):
        self.rand_ids = range(100000)
        random.shuffle(self.rand_ids)
        self.clients = {}

    def buildProtocol(self, addr):
        return ClientConnection(self, addr.host, addr.port)


parser = argparse.ArgumentParser(description="Wizard cardgame - Server")
parser.add_argument("--port", type=int, required=True,
                    help="listen port for incoming connections")
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

    reactor.listenTCP(args.port, ClientConnector())
    reactor.run()


if __name__ == "__main__":
    main(parser.parse_args())
    sys.exit(0)
