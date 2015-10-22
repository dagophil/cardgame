import events
from pygame_view import PygameView
from widgets import ImageWidget
from resource_manager import ResourceManager
import special_widgets
import logging
import actions


BACKGROUND_IMAGE = "resources/bg_green.png"
FONT = "resources/fonts/opensans/OpenSans-Regular.ttf"
FONT_ITALIC = "resources/fonts/opensans/OpenSans-Italic.ttf"
FONT_BOLD = "resources/fonts/opensans/OpenSans-Bold.ttf"
FONT_SIZE = 16


class CardGameView(PygameView):

    def __init__(self, ev_manager):
        self._rm = ResourceManager.instance()
        self._font = self._rm.get_font(FONT, FONT_SIZE)
        self._warnings = {}
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

        # Create the waiting text.
        wait_box = special_widgets.warning_widget(None, (400, 100), "Waiting for other players", self._font,
                                                  screen_size=self.screen.get_size(), close_on_click=False)
        wait_box.visible = True
        bg_widget.add_widget(wait_box)
        self._warnings["wait_box"] = wait_box

        return bg_widget

    def notify(self, event):
        """
        Handle the event.
        :param event: the event
        """
        super(CardGameView, self).notify(event)

        if isinstance(event, events.StartGameEvent):
            self._warnings["wait_box"].add_action(actions.FadeOutAction(0.5))
            logging.warning("TODO: Show the player order in the view.")

        elif isinstance(event, events.NewCardsEvent):
            logging.warning("TODO: Show the cards in the view.")

        elif isinstance(event, events.NewTrumpEvent):
            logging.warning("TODO: Show the trump in the view.")
