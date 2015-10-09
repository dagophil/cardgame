import sys
import argparse
import logging
import threading
from multiprocessing import Queue
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import pygame
import core.common as cmn
from core.pygame_view import PygameView


class GameApp(object):
    """
    The game app.
    """

    def __init__(self, view, args):
        self._view = view
        self._running = False
        self._args = args
        self._clock = pygame.time.Clock()
        self._msg_queue = Queue()
        self._state = cmn.PENDING
        self.client = None
        self._wait_for_user = False
        self._force_exit = False

    @property
    def fps(self):
        """
        Return the fps.
        :return: the fps
        """
        return self._args.fps

    def force_exit(self):
        """
        Force the app exit.
        """
        self._force_exit = True

    def send(self, msg):
        """
        Convert line to a string and send it.
        :param msg: something to be sent
        """
        if self.client is None:
            logging.warning("Tried to send, but there is no client.")
        else:
            msg = str(msg)
            logging.debug("Send '%s'" % msg)
            self.client.sendLine(msg)

    def run(self):
        """
        Start the game.
        """
        if self._force_exit:
            return

        # Init the view.
        self._view.init(self._args.width, self._args.height)

        # Start the game loop.
        self._running = True
        elapsed_time = 0
        while self._running and not self._force_exit:
            self.tick(elapsed_time)
            elapsed_time = self._clock.tick(self.fps) / 1000.0

        # Exit the view.
        self._view.exit()

    def stop(self):
        """
        Stop the game.
        """
        self._running = False

    def tick(self, elapsed_time):
        """
        One iteration in the game loop.
        :param elapsed_time: the elapsed time since the last frame
        """
        self._handle_messages()

    def _handle_messages(self):
        """
        Handle the network messages.
        """
        # Get the new messages from the queue.
        messages = []
        while not self._msg_queue.empty():
            msg = self._msg_queue.get()
            messages.append(msg)

        # Handle the messages.
        for msg in messages:
            if msg is None:
                self.stop()
                break
            elif self._state == cmn.PENDING:
                try:
                    msg = int(msg)
                except ValueError:
                    logging.warning("Could not parse handshake number: %s" % msg)
                    self.stop()
                self.send(cmn.handshake_fun(msg))
                self._state = cmn.WAIT_FOR_NAME
            elif self._state == cmn.WAIT_FOR_NAME:
                try:
                    msg = int(msg)
                except ValueError:
                    logging.warning("Waiting for name, expected int, but got '%s'." % msg)
                    self.stop()
                self._wait_for_user = True
                if msg == 1:
                    self._ask_for_username()
                elif msg == cmn.TAKEN_USERNAME:
                    self._username_is_taken()
            else:
                logging.warning("Unhandled message: '%s'" % msg)

    def _ask_for_username(self):
        """
        Ask the user for the username.
        """
        logging.warning("ask_for_username(): Not implemented.")

    def _username_is_taken(self):
        """

        :return:
        """
        logging.warning("username_is_taken(): Not implemented.")

    def append_message(self, msg):
        """
        Append the given message to the message queue.
        :param msg: the message
        """
        self._msg_queue.put(msg)


class ServerConnection(LineReceiver):
    """
    Protocol: See ClientConnection in server.py.
    """

    def __init__(self, factory):
        self._factory = factory

    @property
    def app(self):
        return self._factory.app

    def connectionMade(self):
        """
        Show some info that the connection was made.
        """
        logging.info("Made connection.")
        self.app.client = self

    def connectionLost(self, reason=connectionDone):
        """
        Show some info that the connection was lost.
        :param reason:
        """
        logging.info("Lost connection.")
        self.app.append_message(None)

    def lineReceived(self, line):
        """
        Parse the messages from the server and call the according functions.
        :param line: the received line
        """
        assert isinstance(line, str)
        line = line.translate(cmn.CHAR_TRANS_TABLE)
        logging.debug("Received '%s'" % line)
        self.app.append_message(line)


class ServerConnector(ClientFactory):
    """
    Creates a ClientConnection for each incoming client.
    """

    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        return ServerConnection(self)

    def clientConnectionFailed(self, connector, reason):
        logging.warning("Failed to connect.")
        self.app.force_exit()


parser = argparse.ArgumentParser(description="Wizard cardgame - Client")
parser.add_argument("--host", type=str, required=True,
                    help="the server hostname")
parser.add_argument("--port", type=int, required=True,
                    help="the port on the server")
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="show verbose output")
parser.add_argument("--debug", action="store_true",
                    help="show debug output")
parser.add_argument("--fps", type=int, default=60,
                    help="number of frames per second")
parser.add_argument("--width", type=int, default=800,
                    help="window width")
parser.add_argument("--height", type=int, default=600,
                    help="window height")


def main(args):
    """
    Set the logging level and start the pygame loop.
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

    # Create the game app.
    app = GameApp(PygameView(), args)

    # Start the reactor in a thread.
    connector = reactor.connectTCP(args.host, args.port, ServerConnector(app))
    logging.info("Client is running.")
    t = threading.Thread(target=reactor.run, args=(False,))
    t.start()

    # Start the game loop.
    app.run()

    # Shut down the reactor.
    connector.disconnect()
    reactor.callFromThread(reactor.stop)
    t.join()
    logging.info("Shutdown successful.")


if __name__ == "__main__":
    main(parser.parse_args())
    sys.exit(0)

