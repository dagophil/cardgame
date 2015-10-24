import numpy
import logging


class Action(object):
    """
    Parent class for all actions.
    """

    def __init__(self):
        self.finished = False

    def act(self, w, elapsed_time):
        """
        If not finished, perform the action. Return whether the action is finished.
        Do not overwrite this method in subclasses. Overwrite _act instead.
        :param w: the widget
        :param elapsed_time: the elapsed time since the last frame
        :return: True if the action is finished, else False.
        """
        if not self.finished:
            self.finished = self._act(w, elapsed_time)
            if self.finished:
                self.handle_finished()
        return self.finished

    def _act(self, w, elapsed_time):
        """
        Perform the action on the widget. Return whether the action is finished.
        :param w: the widget
        :param elapsed_time: the elapsed time since the last frame
        :return: True if the action is finished, else False.
        """
        pass

    def handle_finished(self):
        """
        Callback that is called after the action is finished.
        """
        pass


class DelayedAction(Action):
    """
    Wait the given time, then perform the action.
    """

    def __init__(self, delay, action):
        super(DelayedAction, self).__init__()
        self.delay = delay
        self.action = action
        self._elapsed_time = 0

    def _act(self, w, elapsed_time):
        """
        If the delay is over, call the action from the stored event.
        """
        self._elapsed_time += elapsed_time
        if self._elapsed_time >= self.delay:
            return self.action.act(w, elapsed_time)


class ChainedAction(Action):
    """
    Perform the given actions one after each other.
    """

    def __init__(self, *actions):
        super(ChainedAction, self).__init__()
        self.actions = list(actions)

    def _act(self, w, elapsed_time):
        """
        Act with the current action.
        """
        if len(self.actions) == 0:
            return True
        else:
            use_next_action = self.actions[0].act(w, elapsed_time)
            if use_next_action:
                self.actions = self.actions[1:]
            return len(self.actions) == 0


class HideAction(Action):
    """
    Hide the widget.
    """

    def _act(self, w, elapsed_time):
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
        super(FadeOutAction, self).__init__()
        self.time = float(time)
        self._elapsed_time = 0

    @property
    def _t(self):
        return (self.time - self._elapsed_time) / self.time

    def _act(self, w, elapsed_time):
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


class FadeInAction(Action):
    """
    Apply a fade in effect.
    """

    def __init__(self, time):
        super(FadeInAction, self).__init__()
        self.time = float(time)
        self._elapsed_time = 0
        self._init_opacity = None

    @property
    def _t(self):
        return self._elapsed_time / self.time

    def _act(self, w, elapsed_time):
        """
        Apply the fade in effect.
        """
        if self._init_opacity is None:
            self._init_opacity = w.opacity
        if not w.visible:
            w.visible = True

        self._elapsed_time += elapsed_time
        t = self._t
        if self._elapsed_time >= self.time:
            w.opacity = 1
            return True
        else:
            w.opacity = t + (1-t) * self._init_opacity
            return False


class MoveByAction(Action):
    """
    Move the widget by the given amount in the given time.
    """

    def __init__(self, delta, time):
        super(MoveByAction, self).__init__()
        self.delta = numpy.array(delta, dtype=numpy.int32)
        self.time = time
        self._elapsed_time = 0
        self._current_delta = numpy.array([0, 0], dtype=numpy.int32)

    def _act(self, w, elapsed_time):
        """
        Do the movement.
        """
        self._elapsed_time += elapsed_time
        t = self._elapsed_time / float(self.time)
        if t >= 1:
            w.position += self.delta - self._current_delta
            return True
        else:
            delta = numpy.round(t * self.delta).astype(numpy.int32)
            w.position += delta - self._current_delta
            self._current_delta = delta
            return False

class MoveToAction(Action):
    """
    Move the widget to the given position in the given time.
    """

    def __init__(self, target_pos, time):
        super(MoveToAction, self).__init__()
        self.target_pos = numpy.array(target_pos, dtype=numpy.int32)
        self.time = time
        self._elapsed_time = 0
        self._init_pos = None

    def _act(self, w, elapsed_time):
        """
        Do the movement.
        """
        if self._init_pos is None:
            self._init_pos = w.position
        self._elapsed_time += elapsed_time
        t = self._elapsed_time / float(self.time)
        if t >= 1:
            w.position = self.target_pos
            return True
        else:
            w.position = t * (self.target_pos - self._init_pos) + self._init_pos
            return False
