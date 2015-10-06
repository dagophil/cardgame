import string
import logging
import colorama


# colorama shortcuts.
RED = colorama.Fore.RED
BLUE = colorama.Fore.BLUE
BOLD = colorama.Style.BRIGHT
RESET = colorama.Style.RESET_ALL


# The client states:
PENDING = 0
WAIT_FOR_NAME = 1
ACCEPTED = 2

# The user message ids.
NEW_USER = 100
USER_LEFT = 101
CHAT = 102

# The game message ids
START_GAME = 200
CARDS = 201
ASK_TRICKS = 202
SAY_TRICKS = 203
PLAYER_SAID_TRICKS = 204
ASK_CARD = 205
SAY_CARD = 206
ASK_TRUMP = 207
SAY_TRUMP = 208
FOUND_TRUMP = 209

# The errors:
FORBIDDEN_USERNAME = 400
TAKEN_USERNAME = 401
UNKNOWN_MESSAGE = 402
NOT_YOUR_TURN = 403
INVALID_NUM_TRICKS = 404
INVALID_TRUMP = 405
INVALID_CARD = 406

# The names of the colors.
COLOR_NAMES = {"D": "Diamonds",
               "H": "Hearts",
               "S": "Spades",
               "C": "Clubs",
               "W": "Wizard",
               "L": "Loser"}

# The characters that are allowed to be sent over network:
ALLOWED_CHARS = string.letters + string.digits + string.punctuation
CHAR_TRANS_TABLE = None


def _create_char_trans_table():
    """
    Fill the character transformation table, so that it only keeps the characters from ALLOWED_CHARS, all other
    characters will be replaced with spaces.
    """
    global CHAR_TRANS_TABLE
    l = [" "] * 256
    for c in ALLOWED_CHARS:
        l[ord(c)] = c
    CHAR_TRANS_TABLE = "".join(l)
_create_char_trans_table()


def handshake_fun(x):
    """
    The handshake function.
    :param x: some number
    :return: transformation of x
    """
    # TODO: Change this to something more complicated.
    return x
    # return 3*x+1


class ColoredFormatter(logging.Formatter):
    """
    A logging formatter with colored output.

    Example:
    logging_level = logging.DEBUG
    logging_handler = logging.StreamHandler(sys.stdout)
    logging_handler.setFormatter(ColoredFormatter())
    logging.root.addHandler(logging_handler)
    logging.root.setLevel(logging_level)
    """

    def __init__(self):
        super(ColoredFormatter, self).__init__()
        self.format_strings = {logging.DEBUG: BOLD+BLUE + "DEBUG:" + RESET + " %(message)s",
                               logging.INFO: BOLD + "INFO:" + RESET + " %(message)s",
                               logging.WARNING: BOLD+RED + "WARNING:" + RESET + " %(message)s",
                               logging.ERROR: BOLD+RED + "ERROR:" + RESET + " %(message)s"}
        self.default_string = "LOG: %(message)s"

    def format(self, record):
        self._fmt = self.format_strings.get(record.levelno, self.default_string)
        return super(ColoredFormatter, self).format(record)
