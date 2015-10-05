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

# The misc message ids.
NEW_USER = 100
USER_LEFT = 101

# The errors:
FORBIDDEN_USERNAME = 400
UNKNOWN_MESSAGE = 401

# The characters that are allowed to be sent over network:
ALLOWED_CHARS = string.letters + string.digits + string.punctuation
CHAR_TRANS_TABLE = None


def _create_char_trans_table():
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
