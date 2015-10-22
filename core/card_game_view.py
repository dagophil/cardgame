import events
from pygame_view import PygameView
from widgets import ImageWidget
from resource_manager import ResourceManager


BACKGROUND_IMAGE = "resources/bg_green.png"


class CardGameView(PygameView):

    def __init__(self, ev_manager):
        self._rm = ResourceManager.instance()
        bg_widget = self._create_widgets()
        super(CardGameView, self).__init__(ev_manager, bg_widget)

    def _create_widgets(self):
        """
        Create the widgets and return the background widget.
        :return: the background widget
        """
        # Create the background widget.
        bg = self._rm.get_image(BACKGROUND_IMAGE, self.screen.get_size())
        bg_widget = ImageWidget((0, 0), self.screen.get_size(), -1, bg)



        return bg_widget
