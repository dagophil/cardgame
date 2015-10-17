from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
import events
import logging
from multiprocessing import Queue
import threading


class NetworkController(object):
    """
    Controller for network events.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._network_events = Queue()
        self._connector = None
        self._server_connector = None
        self._thread = threading.Thread(target=reactor.run, args=(False,))
        self._thread.start()
        logging.debug("Started reactor.")

    def connect(self, host, port):
        """
        Start the reactor.
        """
        logging.info("Connecting host '%s' on port '%d'." % (host, port))
        self._server_connector = ServerConnector(self._post_network_event)
        self._connector = blockingCallFromThread(reactor, reactor.connectTCP, host, port, self._server_connector)

    def _post_network_event(self, event):
        """
        Put the event into the queue.
        """
        self._network_events.put(event)

    def _disconnect(self):
        """
        Close all connections.
        """
        if self._connector is not None:
            self._connector.disconnect()
        self._connector = None
        self._server_connector = None

    def _shutdown(self):
        """
        Close all connections.
        """
        self._disconnect()
        reactor.callFromThread(reactor.stop)
        self._thread.join()
        self._thread = None
        logging.debug("Reactor is shut down.")

    def send(self, line):
        """
        Send the given line over network.
        :param line: the line
        """
        if self._server_connector is None:
            logging.warning("Tried to send over network, but there are no connections.")
        else:
            line = str(line)
            self._server_connector.sendLine(line)
            logging.debug("Sent '%s' over network." % line)

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        if isinstance(event, events.CloseCurrentModelEvent):
            self._shutdown()
        elif isinstance(event, events.TickEvent):
            network_events = []
            while not self._network_events.empty():
                network_events.append(self._network_events.get())
            for ev in network_events:
                if isinstance(ev, events.ConnectionFailedEvent):
                    logging.warning("Connection failed.")
                    self._disconnect()
                elif isinstance(ev, events.ConnectionLostEvent):
                    logging.warning("Connection lost.")
                elif isinstance(ev, events.ConnectionMadeEvent):
                    logging.info("Connection established.")
                self._ev_manager.post(ev)


class ServerConnection(LineReceiver):
    """
    Protocol: See ClientConnection in server.py.
    """

    def __init__(self, factory):
        assert isinstance(factory, ServerConnector)
        self._factory = factory

    def connectionMade(self):
        """
        Show some info that the connection was made.
        """
        self._factory.connections[self] = 1
        self._factory.post_func(events.ConnectionMadeEvent())

    def connectionLost(self, reason=connectionDone):
        """
        Show some info that the connection was lost.
        :param reason:
        """
        if self in self._factory.connections:
            del self._factory.connections[self]
        self._factory.post_func(events.ConnectionLostEvent())

    def lineReceived(self, line):
        """
        Parse the messages from the server and call the according functions.
        :param line: the received line
        """
        self._factory.post_func(events.LineReceivedEvent(line))


class ServerConnector(ClientFactory):
    """
    Creates a ClientConnection for each incoming client.
    """

    def __init__(self, post_func):
        self.post_func = post_func
        self.connections = {}

    def buildProtocol(self, addr):
        return ServerConnection(self)

    def clientConnectionFailed(self, connector, reason):
        self.post_func(events.ConnectionFailedEvent())

    def sendLine(self, line):
        for k in self.connections:
            k.sendLine(line)
