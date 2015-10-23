import events
from pygame_view import PygameView
from widgets import ImageWidget
from resource_manager import ResourceManager
import special_widgets
import logging
import actions
import math


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
        self.username = None
        self._player_positions = {}
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

    def _show_player_order(self, player_order):
        """
        Show the player order.
        :param player_order: the player order
        """
        width = 100
        height = 50
        margin_x = 10
        margin_y = 10

        cx = self._screen.get_width() / 2
        cy = self._screen.get_height() / 2
        rx = self._screen.get_width() / 2 - width/2 - margin_x
        ry = self._screen.get_height() / 2 - height/2 - margin_y

        # Rotate the players, so that the current user is at the bottom of the window and the player order is clockwise.
        i = player_order.index(self.username)
        player_order = player_order[i+1:] + player_order[:i]

        # Compute the positions of the other players.
        if len(player_order) == 1:
            self._player_positions[player_order[0]] = (cx, height/2 + margin_y)
        else:
            n = len(player_order)-1
            for i, p in enumerate(player_order):
                d = i * math.pi / n
                x = int(cx - math.cos(d) * rx)
                y = int(cy - math.sin(d) * ry)
                self._player_positions[p] = (x, y)

        # Show the other players.
        # TODO: The widget size should adapt to the length of the player name.
        for p in player_order:
            pos = self._player_positions[p]
            x = pos[0] - width/2
            y = pos[1] - height/2
            w = special_widgets.warning_widget((x, y), (width, height), p, self._font, close_on_click=False)
            w.visible = True
            self._background_widget.add_widget(w)

    def notify(self, event):
        """
        Handle the event.
        :param event: the event
        """
        super(CardGameView, self).notify(event)

        if isinstance(event, events.StartGameEvent):
            self._warnings["wait_box"].add_action(actions.FadeOutAction(0.5))
            self._show_player_order(event.player_order)

        elif isinstance(event, events.NewCardsEvent):
            logging.warning("TODO: Show the cards in the view.")

        elif isinstance(event, events.NewTrumpEvent):
            logging.warning("TODO: Show the trump in the view.")
