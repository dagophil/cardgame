from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

def TEST():
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