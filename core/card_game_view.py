import events
from pygame_view import PygameView
import widgets


class CardGameView(PygameView):

    def __init__(self, ev_manager):
        # TODO: Change the widget.
        # TODO: The old MVC must unregister themselves from the event manager when the CloseCurrentModel is posted.
        super(CardGameView, self).__init__(ev_manager, widgets.Widget((0, 0), (10, 10), 0))
