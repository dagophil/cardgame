import events
from login_model import LoginModel
from login_view import LoginView
from pygame_controller import PygameController


class LoginController(PygameController):
    """
    The GUI controller.
    """

    def __init__(self, ev_manager, model, view):
        super(LoginController, self).__init__(ev_manager)
        assert isinstance(model, LoginModel)
        assert isinstance(view, LoginView)
        self._model = model
        self._view = view

    def notify(self, event):
        """
        Handle the given event.
        :param event: the event
        """
        super(LoginController, self).notify(event)

        if isinstance(event, events.TickEvent):
            pass
