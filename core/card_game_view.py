import events
from pygame_view import PygameView
from widgets import ImageWidget
from resource_manager import ResourceManager
import special_widgets
import logging
import actions
import math
import common as cmn


BACKGROUND_IMAGE = "resources/bg_green.png"
FONT = "resources/fonts/opensans/OpenSans-Regular.ttf"
FONT_ITALIC = "resources/fonts/opensans/OpenSans-Italic.ttf"
FONT_BOLD = "resources/fonts/opensans/OpenSans-Bold.ttf"
FONT_SIZE = 16


def get_card_image(card):
    """
    Return the filename of the image of the given card.
    :param card: the card
    :return: the filename
    """
    if "L" in card:
        card_name = "loser"
    elif "W" in card:
        card_name = "wizard"
    else:
        card_name = card
    s = "resources/card_deck/" + card_name + ".png"
    return s


def get_color_image(color):
    """
    Return the filename of the image of the given color.
    :param color: the color
    :return: the filename
    """
    if color == "W":
        color_name = "all"
    else:
        color_name = color
    s = "resources/colors/" + color_name + ".png"
    return s


def cmp_colors_first(a, b):
    """
    Compare two cards a, b for color sorting.
    :param a: the first card
    :param b: the second card
    :return: the sorting
    """
    # Compare the colors.
    ca = cmn.NUMERIC_COLOR_VALUES[a[0]]
    cb = cmn.NUMERIC_COLOR_VALUES[b[0]]
    if ca != cb:
        return cmp(ca, cb)

    # Compare the values.
    va = cmn.NUMERIC_VALUES[a[1]]
    vb = cmn.NUMERIC_VALUES[b[1]]
    return cmp(va, vb)


class CardGameView(PygameView):

    def __init__(self, ev_manager):
        self._rm = ResourceManager.instance()
        self._font = self._rm.get_font(FONT, FONT_SIZE)
        self._warnings = {}
        self.username = None
        self._player_positions = {}
        self._card_widgets = {}
        self._trump_widgets = {}
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

        # Create the chat widget.
        chat_box = special_widgets.warning_widget((10, self.screen.get_height()-260), (260, 200), "chat", self._font,
                                                  close_on_click=False)
        chat_box.visible = True
        bg_widget.add_widget(chat_box)

        # Create the trump widgets.
        trump_pos = (200, 180)
        trump_size = (125, 125)
        for color in ["W", "H", "D", "S", "C"]:
            im_filename = get_color_image(color)
            im = self._rm.get_image(im_filename, trump_size)
            im_w = ImageWidget(trump_pos, trump_size, 0, im)
            im_w.opacity = 0
            bg_widget.add_widget(im_w)
            self._trump_widgets[color] = im_w

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

    def _show_cards(self, cards):
        """
        Create the card widgets.
        :param cards: the cards
        """
        self._card_widgets = {}
        card_size = (130, 184)
        x_min = 290
        x_delta = 50
        y = 400
        cards.sort(cmp_colors_first)
        for i, card in enumerate(cards):
            card_image_name = get_card_image(card)
            im = self._rm.get_image(card_image_name)
            w = ImageWidget((x_min+i*x_delta, y), card_size, i, im)
            self._background_widget.add_widget(w)
            self._card_widgets[card] = w

    def _show_trump(self, trump):
        """
        Show the trump widget.
        :param trump: the trump
        """
        visible_w = None
        for w_name in self._trump_widgets:
            w = self._trump_widgets[w_name]
            if w.visible:
                visible_w = w

        def fade_in_new_trump():
            if trump != "L":
                self._trump_widgets[trump].add_action(actions.FadeInAction(0.5))

        if visible_w is None:
            fade_in_new_trump()
        else:
            a = actions.FadeOutAction(0.5)
            a.handle_finished = fade_in_new_trump
            visible_w.add_action(a)

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
            self._show_cards(event.cards)

        elif isinstance(event, events.NewTrumpEvent):
            self._show_trump(event.trump)
