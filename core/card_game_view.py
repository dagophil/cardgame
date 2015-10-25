import events
from pygame_view import PygameView
from widgets import Widget, ImageWidget, Text
from resource_manager import ResourceManager
import special_widgets
import logging
import actions
import math
import common as cmn
import pygame


BACKGROUND_IMAGE = "resources/bg_green.png"
FONT = "resources/fonts/opensans/OpenSans-Regular.ttf"
FONT_ITALIC = "resources/fonts/opensans/OpenSans-Italic.ttf"
FONT_BOLD = "resources/fonts/opensans/OpenSans-Bold.ttf"
FONT_SIZE = 16


def get_card_image_filename(card):
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


def get_color_image_filename(color):
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
        self.elapsed_time = 0
        self.last_win_time = -5
        self._rm = ResourceManager.instance()
        self._font = self._rm.get_font(FONT, FONT_SIZE)
        self._warnings = {}
        self.username = None
        self._player_positions = {}
        self._card_widgets = {}
        self._trump_widgets = {}
        self._choose_trump_widget = None
        self._ask_tricks_widget = None
        self._user_move = False
        self._played_card_widgets = []
        self._said_tricks_widgets = {}
        self._user_move_widget = None
        bg_widget = self._create_widgets()
        super(CardGameView, self).__init__(ev_manager, bg_widget)

    @property
    def user_move(self):
        return self._user_move

    @user_move.setter
    def user_move(self, b):
        if b:
            self._user_move_widget.opacity = 0
            self._user_move_widget.clear_actions()
            self._user_move_widget.add_action(actions.FadeInAction(0.5))
        else:
            self._user_move_widget.clear_actions()
            self._user_move_widget.add_action(actions.FadeOutAction(0.5))
        self._user_move = b

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

        # Create the "invalid num tricks" warning.
        invalid_num_warning = special_widgets.warning_widget(None, (400, 100), "Invalid number of tricks", self._font,
                                                             screen_size=self.screen.get_size())
        bg_widget.add_widget(invalid_num_warning)
        self._warnings["invalid_num_tricks"] = invalid_num_warning

        # Create the chat widget.
        chat_box = special_widgets.warning_widget((10, self.screen.get_height()-260), (260, 200), "chat", self._font,
                                                  close_on_click=False)
        chat_box.visible = True
        bg_widget.add_widget(chat_box)

        # Create the "Your move" box.
        your_move_w = Text((self.screen.get_width()-140, self.screen.get_height()-60), (120, 40), 0, "Your move",
                           self._font, fill=(0, 0, 0, 160))
        your_move_w.opacity = 0
        bg_widget.add_widget(your_move_w)
        self._user_move_widget = your_move_w

        # Create the trump widgets.
        trump_pos = (180, 180)
        trump_size = (125, 125)
        for color in ["W", "H", "D", "S", "C"]:
            im_filename = get_color_image_filename(color)
            im = self._rm.get_image(im_filename, trump_size)
            im_w = ImageWidget(trump_pos, trump_size, 0, im)
            im_w.opacity = 0
            bg_widget.add_widget(im_w)
            self._trump_widgets[color] = im_w

        # Create the "choose trump" widgets.
        class ChooseHandler(object):
            def __init__(self, view, trump):
                self._view = view
                self._trump = trump
            def __call__(self, x, y):
                self._view._handle_choose_trump(self._trump)
        choose_size = (90, 90)
        choose_trump_bg = pygame.Surface((400, 170), flags=pygame.SRCALPHA)
        choose_trump_bg.fill((0, 0, 0, 160))
        font_obj = self._font.render("Choose the trump:", True, (255, 255, 255, 255))
        choose_trump_bg.blit(font_obj, ((choose_trump_bg.get_width()-font_obj.get_width())/2, 20))
        choose_trump_container = ImageWidget((self.screen.get_width()/2 - 200, 200), choose_trump_bg.get_size(), 99,
                                             choose_trump_bg, visible=False)
        for i, color in enumerate(["D", "S", "H", "C"]):
            im_filename = get_color_image_filename(color)
            im = self._rm.get_image(im_filename, choose_size)
            im_w = ImageWidget((i*(choose_size[0]+10), 70), choose_size, 0, im)
            choose_trump_container.add_widget(im_w)
            im_w.handle_clicked = ChooseHandler(self, color)
        bg_widget.add_widget(choose_trump_container)
        self._choose_trump_widget = choose_trump_container

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

        # Add the box for the said tricks.
        for p in player_order:
            pos = self._player_positions[p]
            x = pos[0] + width/2 + 10
            y = pos[1] - height/2
            w = Text((x, y), (80, height), 50, "0/0", self._font, fill=(0, 0, 0, 160))
            w.opacity = 0
            self._said_tricks_widgets[p] = w
            self._background_widget.add_widget(w)

    def show_cards(self, cards):
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
        class HandleCardClicked(object):
            def __init__(self, view, card):
                self._view = view
                self._card = card
            def __call__(self, x, y):
                self._view._handle_say_card(self._card)
        for i, card in enumerate(cards):
            card_image_name = get_card_image_filename(card)
            im = self._rm.get_image(card_image_name)
            w = ImageWidget((x_min+i*x_delta, y), card_size, i, im)
            w.handle_clicked = HandleCardClicked(self, card)
            self._background_widget.add_widget(w)
            self._card_widgets[card] = w

    def show_trump(self, trump):
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

    def ask_trump(self):
        """
        Ask the user for the trump.
        """
        for w in self._trump_widgets.values():
            w.clear_actions()
            w.opacity = 0
        self._choose_trump_widget.opacity = 0
        self._choose_trump_widget.add_action(actions.FadeInAction(0.5))

    def _handle_choose_trump(self, trump):
        """
        Send the chosen trump to the server.
        :param trump: the trump
        """
        self._choose_trump_widget.opacity = 0
        self._ev_manager.post(events.ChooseTrumpEvent(trump))

    def ask_tricks(self, n):
        """
        Ask the user for the number of tricks.
        :param n: the maximum number of tricks
        """
        # Create the container with the fade in effect.
        container = Widget((self.screen.get_width()/2-200, 100), (400, self.screen.get_height()-120), 40)
        container.opacity = 0
        container.add_action(actions.FadeInAction(0.5))
        self._ask_tricks_widget = container
        self._background_widget.add_widget(container)

        # Create the question text.
        text_w = special_widgets.warning_widget((0, 0), (400, 60), "How many tricks do you make?", self._font,
                                                close_on_click=False)
        text_w.visible = True
        container.add_widget(text_w)

        # Create the numbers.
        class ChooseHandler(object):
            def __init__(self, view, nn):
                self._view = view
                self._n = nn
            def __call__(self, x, y):
                self._view._handle_say_tricks(self._n)
        for i in xrange(n+1):
            size = (50, 50)
            pos = ((i % 6) * (size[0]+20), 80 + (i/6) * (size[1] + 20))
            w = special_widgets.warning_widget(pos, size, str(i), self._font, close_on_click=False)
            w.visible = True
            w.handle_clicked = ChooseHandler(self, i)
            container.add_widget(w)

    def _handle_say_tricks(self, n):
        """
        Broadcast the user input.
        :param n: the number
        """
        self._ev_manager.post(events.UserSaysTricksEvent(n))

    def show_invalid_num_tricks(self, n):
        """
        Show the warning, that an invalid number of tricks was chosen.
        :param n: the number
        """
        w = self._warnings["invalid_num_tricks"]
        w.show()
        w.add_action(actions.DelayedAction(3, actions.FadeOutAction(0.5)))

    def _handle_say_card(self, card):
        """
        Broadcast the card that the user wants to play.
        :param card: the card
        """
        if self.user_move:
            self._ev_manager.post(events.UserSaysCardEvent(card))

    def _player_played_card(self, player, card):
        """
        Show that the player played the card.
        :param player: the player
        :param card: the card
        """
        card_size = (130, 184)
        im_filename = get_card_image_filename(card)
        im = self._rm.get_image(im_filename)
        pos = self._player_positions[player]
        im_w = ImageWidget((pos[0]-card_size[0]/2, pos[1]-card_size[1]/2), card_size, 20+len(self._played_card_widgets), im)
        self._background_widget.add_widget(im_w)
        x = self.screen.get_width()/2 - 200 + len(self._played_card_widgets) * 60
        y = 150 + len(self._played_card_widgets) * 10
        im_w.add_action(actions.MoveToAction((x, y), 1))
        self._played_card_widgets.append(im_w)

    def show_user_move(self):
        """
        Show some info that it is the user's turn.
        """
        self.user_move = True

    def notify(self, event):
        """
        Handle the event.
        :param event: the event
        """
        super(CardGameView, self).notify(event)

        if isinstance(event, events.TickEvent):
            self.elapsed_time += event.elapsed_time

        elif isinstance(event, events.StartGameEvent):
            self._warnings["wait_box"].add_action(actions.FadeOutAction(0.5))
            self._show_player_order(event.player_order)

        elif isinstance(event, events.SayTricksEvent):
            self._background_widget.remove_widget(self._ask_tricks_widget)
            self._warnings["invalid_num_tricks"].hide()
            self._ask_tricks_widget = None

        elif isinstance(event, events.PlayerSaidTricksEvent):
            # TODO: Show the number of tricks that the player said.
            pass

        elif isinstance(event, events.SayCardEvent):
            x = self.screen.get_width()/2 - 200 + len(self._played_card_widgets) * 60
            y = 150 + len(self._played_card_widgets) * 10
            w = self._card_widgets[event.card]
            w.unhandle_clicked()
            w.z_index = 20 + len(self._played_card_widgets)
            self._played_card_widgets.append(w)
            w.add_action(actions.MoveToAction((x, y), 1))
            self.user_move = False

        elif isinstance(event, events.PlayerPlayedCardEvent):
            if event.player != self.username:
                self._player_played_card(event.player, event.card)

        elif isinstance(event, events.WinTrickEvent):

            class WidgetRemover(object):
                def __init__(self, view, ww):
                    self._view = view
                    self._w = ww
                def __call__(self):
                    self._view._background_widget.remove_widget(self._w)
            for w in self._played_card_widgets:
                a = actions.DelayedAction(4, actions.FadeOutAction(0.5))
                a.handle_finished = WidgetRemover(self, w)
                w.add_action(a)

            self._played_card_widgets = []
            self.last_win_time = self.elapsed_time
            logging.warning("TODO: Show that player %s won the trick." % event.player)
