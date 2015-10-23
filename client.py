import sys
import argparse
import logging

import pygame
pygame.init()

import core.events as events
import core.common as cmn
from core.pygame_view import PygameView
from core.login_view import LoginView
from core.login_model import LoginModel
from core.login_controller import LoginController
from core.card_game_model import CardGameModel
from core.card_game_view import CardGameView
from core.card_game_controller import CardGameController


class TickerController(object):
    """
    Regularly sends a tick event to keep the game running (heart beat).
    """

    def __init__(self, ev_manager, fps=60):
        self._ev_manager = ev_manager
        self._ev_manager.register_listener(self)
        self._running = False
        self._fps = fps
        self._clock = pygame.time.Clock()

    def run(self):
        """
        Start the ticker.
        """
        self._running = True
        elapsed_time = 0
        while self._running:
            self._ev_manager.post(events.TickEvent(elapsed_time))
            elapsed_time = self._clock.tick(self._fps) / 1000.0  # elapsed time since last frame in seconds

    def notify(self, event):
        """
        Stop the ticker on the CloseModelEvent.
        """
        if isinstance(event, events.CloseCurrentModelEvent):
            self._running = False


class GameApp(object):
    """
    The game app.
    """

    def __init__(self, args):
        self._args = args
        self._ev_manager = events.EventManager()
        self._ev_manager.next_model_name = self._args.model
        self._ticker = TickerController(self._ev_manager, self.fps)
        self._models = {
            "Login": self._run_login_model,
            "CardGame": self._run_card_game_model
        }

    @property
    def fps(self):
        """
        Return the fps.
        :return: the fps
        """
        return self._args.fps

    @property
    def width(self):
        """
        Return the width.
        :return: the width
        """
        return self._args.width

    @property
    def height(self):
        """
        Return the height.
        :return: the height
        """
        return self._args.height

    def _run_login_model(self):
        """
        Load and run the login model.
        """
        logging.debug("Loading the login model.")

        # Create MVC.
        model = LoginModel(self._ev_manager)
        view = LoginView(self._ev_manager)
        controller = LoginController(self._ev_manager, model, view, self._args.login_file)

        # Initialize the components and start the ticker.
        self._ev_manager.post(events.InitModelEvent())
        self._ticker.run()

    def _run_card_game_model(self, network_controller, username):
        """
        Load and run the card game model.
        """
        logging.debug("Loading the card game model.")

        # Create MVC.
        model = CardGameModel(self._ev_manager)
        view = CardGameView(self._ev_manager)
        controller = CardGameController(self._ev_manager, model, view, network_controller, username)

        # Initialize the components and start the ticker.
        self._ev_manager.post(events.InitModelEvent())
        self._ticker.run()

    def run(self):
        """
        Start the game.
        """
        # Initialize the pygame view.
        PygameView.init(self.width, self.height)

        # Run the models after each other.
        while self._ev_manager.next_model_name is not None:
            if self._ev_manager.next_model_name in self._models:
                # Load and run the next model.
                model = self._models[self._ev_manager.next_model_name]
                self._ev_manager.next_model_name = None
                try:
                    model(*self._ev_manager.next_model_args, **self._ev_manager.next_model_kwargs)
                except:
                    # Tell the components that the app crashed, so additional cleanups can be done.
                    logging.warning("The app crashed. Performing additional cleanups.")
                    self._ev_manager.post(events.AppCrashedEvent())
                    raise
            else:
                logging.warning("Could not find model '%s'." % self._ev_manager.next_model_name)
                self._ev_manager.post(events.AppCrashedEvent())
                raise Exception("Could not find model '%s'." % self._ev_manager.next_model_name)

        # Quit when all models finished.
        pygame.quit()


parser = argparse.ArgumentParser(description="Wizard cardgame - Client")
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="show verbose output")
parser.add_argument("--debug", action="store_true",
                    help="show debug output")
parser.add_argument("--fps", type=int, default=60,
                    help="number of frames per second")
parser.add_argument("--width", type=int, default=1000,
                    help="window width")
parser.add_argument("--height", type=int, default=600,
                    help="window height")
parser.add_argument("--model", type=str, default="Login", choices=["Login"],
                    help="the model that is loaded on startup")
parser.add_argument("--login_file", type=str, default="recent_logins.txt",
                    help="file that stores the recent login data")


def main(args):
    """
    Set the logging level and start the pygame loop.
    :param args: command line arguments
    """
    # Set the logging level and create the logger.
    if args.verbose == 0:
        logging_level = logging.WARNING
    else:
        logging_level = logging.INFO
    if args.debug:
        logging_level = logging.DEBUG
    logging_handler = logging.StreamHandler(sys.stdout)
    logging_handler.setFormatter(cmn.ColoredFormatter())
    logging.root.addHandler(logging_handler)
    logging.root.setLevel(logging_level)

    # Create the game app.
    logging.info("Client is running.")
    app = GameApp(args)
    app.run()
    logging.info("Shutdown successful.")


if __name__ == "__main__":
    main(parser.parse_args())
    sys.exit(0)

