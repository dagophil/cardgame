from network_controller import NetworkController
import events
import logging
import common as cmn
import json
import numbers


class InvalidMessageException(Exception):
    pass


class GameNetworkController(NetworkController):
    """
    A network controller that performs the handshake and translates the messages to events.
    """

    def __init__(self, ev_manager, buffer_messages=False):
        super(GameNetworkController, self).__init__(ev_manager)
        self.username = None
        self._state = cmn.WAIT_FOR_HANDSHAKE
        self._buffer_messages = buffer_messages  # if True, store the messages and handle them later
        self._buffer = []

    @property
    def buffer_messages(self):
        return self._buffer_messages

    @buffer_messages.setter
    def buffer_messages(self, b):
        self._buffer_messages = b
        if not b:
            for msg in self._buffer:
                self._handle_valid_message(*msg)

    def update_username(self, username):
        """
        Update the username.
        :param username: the username
        """
        self.username = username
        self.send(self.username)

    def _split(self, line):
        """
        Split the received line into msg_id and msg. The split occurs at the first "#".
        :param line: the line
        :return: msg_id, msg
        """
        if "#" not in line:
            raise InvalidMessageException()
        else:
            i = line.index("#")
            msg_id, msg = line[:i], line[i+1:]
            try:
                msg_id = int(msg_id)
            except ValueError:
                raise InvalidMessageException()
            return msg_id, msg

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        super(GameNetworkController, self).notify(event)

        if isinstance(event, events.ChooseTrumpEvent):
            self.send("%d#%s" % (cmn.SAY_TRUMP, event.trump))

        elif isinstance(event, events.SayTricksEvent):
            self.send("%d#%d" % (cmn.SAY_TRICKS, event.n))

        elif isinstance(event, events.LineReceivedEvent):
            line = event.line
            line = line.translate(cmn.CHAR_TRANS_TABLE)
            logging.debug("Received '%s' over network." % line)

            if self._state == cmn.WAIT_FOR_HANDSHAKE:
                # Apply the handshake function and send the result.
                try:
                    val = int(line)
                except ValueError:
                    logging.warning("Could not translate handshake value '%s' to int." % line)
                    self._ev_manager.post(events.ConnectionFailedEvent)
                    return
                self._state = cmn.PENDING
                answer = cmn.handshake_fun(val)
                self.send(answer)

            elif self._state == cmn.PENDING:
                # Check if the handshake was accepted and send the username.
                fail = False
                val = cmn.WAIT_FOR_NAME-1
                try:
                    val = int(line)
                except ValueError:
                    fail = True
                if fail or val != cmn.WAIT_FOR_NAME:
                    logging.warning("Expected %d for handshake answer, received '%s'." % (cmn.WAIT_FOR_NAME, line))
                    self._ev_manager.post(events.ConnectionFailedEvent)
                    return
                self._state = cmn.WAIT_FOR_NAME
                self.send(self.username)

            elif self._state == cmn.WAIT_FOR_NAME:
                if "#" not in line:
                    # Check if the "taken username" message was sent.
                    fail = False
                    val = cmn.TAKEN_USERNAME-1
                    try:
                        val = int(line)
                    except ValueError:
                        fail = True
                    if fail or val != cmn.TAKEN_USERNAME:
                        logging.warning("Expected error code %d, got '%s' instead." % (cmn.TAKEN_USERNAME, line))
                    else:
                        self._ev_manager.post(events.TakenUsernameEvent())
                else:
                    # Check if the username was accepted.
                    try:
                        msg_id, msg = self._split(line)
                    except InvalidMessageException:
                        logging.warning("Could not split message '%s'." % line)
                        return
                    try:
                        msg_id = int(msg_id)
                    except ValueError:
                        logging.warning("Could not convert msg id '%s' to int." % msg_id)
                        return
                    if msg_id != cmn.NEW_USER or msg != self.username:
                        logging.warning("Expected the username acceptec message, got '%s' instead." % line)
                        return
                    self._state = cmn.ACCEPTED
                    self._ev_manager.post(events.AcceptedUsernameEvent())

            elif self._state == cmn.ACCEPTED:
                self._handle_message(line)

            else:
                logging.warning("Unknown state: %d" % self._state)

    def _handle_message(self, line):
        """
        Split the given line into message id and message and give them to _handle_valid_message.
        :param line: the line
        """
        if "#" not in line:
            logging.warning("Got invalid message '%s' from server." % line)
        else:
            i = line.index("#")
            msg_id, msg = line[:i], line[i+1:]
            try:
                msg_id = int(msg_id)
            except ValueError:
                logging.warning("Server used non-integer message id in message '%s'" % line)
                return
            if self._buffer_messages:
                self._buffer.append((msg_id, msg))
            else:
                self._handle_valid_message(msg_id, msg)

    def _handle_valid_message(self, msg_id, msg):
        """
        Handle the message.
        :param msg_id: the message id
        :param msg: the message
        """
        if msg_id == cmn.NEW_USER:
            self._ev_manager.post(events.PlayerJoinedEvent(msg))

        elif msg_id == cmn.USER_LEFT:
            self._ev_manager.post(events.PlayerLeftEvent(msg))

        elif msg_id == cmn.START_GAME:
            try:
                l = json.loads(msg)
            except ValueError:
                logging.warning("Could not decrypt player order '%s'." % msg)
                return
            self._ev_manager.post(events.StartGameEvent(l))

        elif msg_id == cmn.CARDS:
            try:
                l = json.loads(msg)
            except ValueError:
                logging.warning("Could not decrypt cards '%s'." % msg)
                return
            self._ev_manager.post(events.NewCardsEvent(l))

        elif msg_id == cmn.ASK_TRUMP:
            self._ev_manager.post(events.AskTrumpEvent())

        elif msg_id == cmn.FOUND_TRUMP:
            self._ev_manager.post(events.NewTrumpEvent(msg))

        elif msg_id == cmn.ASK_TRICKS:
            self._ev_manager.post(events.AskTricksEvent(int(msg)))

        elif msg_id == cmn.PLAYER_SAID_TRICKS:
            player, n = msg.split("#")
            n = int(n)
            self._ev_manager.post(events.PlayerSaidTricksEvent(player, n))

        else:
            logging.warning("TODO: Handle message (%d, %s)" % (msg_id, msg))
