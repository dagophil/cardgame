import events


class LoginModel(object):
    """
    The client's model of the game.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)

        self._host = ""
        self._port = ""

    def notify(self, event):
        """
        Handle the events.
        :param event: the event
        """
        pass
