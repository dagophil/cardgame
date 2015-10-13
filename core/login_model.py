import events


class LoginModel(object):
    """
    The model for the login view. Since all information can be stored in the input widgets, this model does nothing.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)

    def notify(self, event):
        """
        Handle the events.
        :param event: the event
        """
        pass
