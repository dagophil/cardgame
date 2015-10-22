import events
import logging


class LoginModel(object):
    """
    The model for the login view. Since all information can be stored in the input widgets, this model does nothing.
    """

    def __init__(self, ev_manager):
        assert isinstance(ev_manager, events.EventManager)
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self.username = ""
        self.host = ""
        self.port = ""

    def notify(self, event):
        """
        Handle the events.
        :param event: the event
        """
        if isinstance(event, events.AttachCharEvent):
            name = event.entity_name
            c = event.char
            if name == "username":
                self.username += c
            elif name == "host":
                self.host += c
            elif name == "port":
                self.port += c
            else:
                logging.warning("LoginModel got unknown entity name: %s" % name)

        elif isinstance(event, events.RemoveCharEvent):
            name = event.entity_name
            n = event.n
            if name == "username":
                self.username = self.username[:-n]
            elif name == "host":
                self.host = self.host[:-n]
            elif name == "port":
                self.port = self.port[:-n]
            else:
                logging.warning("LoginModel got unknown entity name: %s" % name)

        elif isinstance(event, events.CloseCurrentModelEvent):
            self._ev_manager.unregister_listener(self)
