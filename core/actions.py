class Action(object):
    """
    Parent class for all actions.
    """

    def act(self, w, elapsed_time):
        """
        Perform the action on the widget. Return whether the action is finished.
        :param w: the widget
        :param elapsed_time: the elapsed time since the last frame
        :return: True if the action is finished, else False.
        """
        return True


class DelayedAction(Action):
    """
    Wait the given time, then perform the action.
    """

    def __init__(self, delay, action):
        self.delay = delay
        self.action = action
        self._elapsed_time = 0

    def act(self, w, elapsed_time):
        """
        If the delay is over, call the action from the stored event.
        """
        self._elapsed_time += elapsed_time
        if self._elapsed_time >= self.delay:
            return self.action.act(w, elapsed_time)


class HideAction(Action):
    """
    Hide the widget.
    """

    def act(self, w, elapsed_time):
        """
        Hide the widget.
        """
        w.hide()
        return True


class FadeOutAction(Action):
    """
    Apply a fade out effect.
    """

    def __init__(self, time):
        self.time = float(time)
        self._elapsed_time = 0

    @property
    def _t(self):
        return (self.time - self._elapsed_time) / self.time

    def act(self, w, elapsed_time):
        """
        Apply the fade out effect.
        """
        last_t = self._t
        self._elapsed_time += elapsed_time
        new_t = self._t
        if self._elapsed_time >= self.time:
            w.opacity = 0
            return True
        else:
            w.opacity *= new_t / last_t
            return False
