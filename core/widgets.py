import pygame
import logging
from actions import Action
import numpy


BLINK_TIME = 0.5


def pass_func(*args, **kwargs):
    pass


class Widget(object):
    """
    Parent of all widget objects.
    """

    def __init__(self, position, size, z_index, visible=True):
        self.position = numpy.array(position, dtype=numpy.int32)
        self.size = size
        self.z_index = z_index
        self._widgets = []
        self.hovered = False
        self._focused = False
        self.pressed = False
        self.visible = visible
        self._actions = []
        self._opacity = 1

    @property
    def focused(self):
        return self._focused

    @focused.setter
    def focused(self, f):
        if self._focused and not f:
            self.handle_lost_focus()
        elif not self._focused and f:
            self.handle_got_focus()
        self._focused = f

    def unfocus(self):
        """
        Remove focus from the current widget and all sub widgets.
        """
        self.focused = False
        for w in self._widgets:
            w.unfocus()

    def unpress(self):
        """
        Remove the pressed state from the current widget and all sub widgets.
        """
        self.pressed = False
        for w in self._widgets:
            w.unpress()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, o):
        if o <= 0:
            self._opacity = 0
            self.visible = False
        elif o >= 1:
            self._opacity = 1
        else:
            self._opacity = o

    def add_widget(self, w):
        """
        Add the widget to the container.
        :param w: the widget
        """
        assert isinstance(w, Widget)
        if w not in self._widgets:
            self._widgets.append(w)

    def remove_widget(self, w):
        """
        Remove the widget from the container.
        :param w: the widget
        """
        if w in self._widgets:
            self._widgets.remove(w)

    def add_action(self, a):
        """
        Add the action to the widget.
        :param a: the action
        """
        assert isinstance(a, Action)
        self._actions.append(a)

    def clear_actions(self):
        """
        Clear the action list.
        """
        self._actions = []

    def show(self):
        """
        Show the widget.
        """
        self.visible = True
        self.opacity = 1

    def hide(self):
        """
        Hide the widget.
        """
        self.visible = False

    def hover(self, x, y):
        """
        Set the hovered state.
        :param x: x coordinate
        :param y: y coordinate
        """
        previously_hovered = self.hovered
        self.hovered = self.contains(x, y)
        x -= self.position[0]
        y -= self.position[1]
        for w in self._widgets:
            w.hover(x, y)
        if previously_hovered and not self.hovered:
            self.handle_mouse_leave()
        if not previously_hovered and self.hovered:
            self.handle_mouse_enter()
        if self.hovered:
            self.handle_hover(x, y)

    def mouse_down(self, x, y):
        """
        Set the focused and the pressed state.
        :param x: x coordinate
        :param y: y coordinate
        :return: True, if the widget contains (x, y)
        """
        x_sub = x-self.position[0]
        y_sub = y-self.position[1]

        sub_pressed = False
        self._widgets.sort(key=lambda ww: ww.z_index)
        for w in reversed(self._widgets):
            if not w.visible:
                continue
            if sub_pressed:
                w.unfocus()
                w.unpress()
            elif w.mouse_down(x_sub, y_sub):
                sub_pressed = True

        contains = self.contains(x, y)
        if not contains or sub_pressed:
            self.pressed = False
            self.focused = False
        else:
            self.focused = True
            self.pressed = True
            self.handle_mouse_down(x, y)
        return contains

    def mouse_up(self, x, y):
        """
        Set the pressed state to false.
        :param x: x coordinate
        :param y: y coordinate
        :return: True, if the widget contains (x, y)
        """
        x_sub = x-self.position[0]
        y_sub = y-self.position[1]
        sub_hovered = [w.mouse_up(x_sub, y_sub) for w in self._widgets]
        sub_hovered = any(sub_hovered)

        pressed = self.pressed
        self.pressed = False
        contains = self.contains(x, y)
        if contains:
            self.handle_mouse_up(x, y)
            if pressed and not sub_hovered:
                self.handle_clicked(x, y)
        return contains

    def handle_hover(self, x, y):
        """
        Callback for occurring hover events.
        :param x: x coordinate
        :param y: y coordinate
        """
        pass

    def handle_mouse_enter(self):
        """
        Callback for the mouse enter event.
        """
        pass

    def handle_mouse_leave(self):
        """
        Callback for the mouse leave event.
        """
        pass

    def handle_lost_focus(self):
        """
        Callback for occurring focus events.
        """
        pass

    def handle_got_focus(self):
        """
        Callback for occurring focus events.
        """
        pass

    def handle_mouse_down(self, x, y):
        """
        Callback for occurring mouse down events.
        :param x: x coordinate
        :param y: y coordinate
        """
        pass

    def handle_mouse_up(self, x, y):
        """
        Callback for occurring mouse up events.
        :param x: x coordinate
        :param y: y coordinate
        """
        pass

    def handle_clicked(self, x, y):
        """
        Callback for click events.
        :param x: x coordinate
        :param y: y coordinate
        """
        pass

    def unhandle_clicked(self):
        """
        Reset the handle_clicked to the default.
        """
        self.handle_clicked = pass_func

    def contains(self, x, y):
        """
        Return whether (x, y) is inside the widget.
        :param x: x coordinate
        :param y: y coordinate
        :return: whether (x, y) is inside the widget
        """
        x_in = self.position[0] <= x <= self.position[0] + self.size[0]
        y_in = self.position[1] <= y <= self.position[1] + self.size[1]
        return x_in and y_in

    def get_widget_at(self, x, y):
        """
        Return the widget at the given coordinate.
        :param x: x coordinate
        :param y: y coordinate
        :return: the widget at (x, y)
        """
        if not self.contains(x, y):
            return None
        else:
            x -= self.position[0]
            y -= self.position[1]
            wlist = [w for w in self._widgets if w.contains(x, y)]
            if len(wlist) == 0:
                return self
            else:
                wlist.sort(key=lambda ww: ww.z_index)
                return wlist[-1].get_widget_at(x, y)

    def get_focused_widget(self):
        """
        Return the focused widget (or None).
        :return: the focused widget
        """
        if self.focused:
            return self
        else:
            for w in self._widgets:
                foc = w.get_focused_widget()
                if foc is not None:
                    return foc
        return None

    def render(self, surface):
        """
        If it is visible, render the widget.
        Do not overwrite this method in subclasses, overwrite _render instead. The _render method will get a surface of
        the widget's size, so the translation by self.position is not necessary.
        :param surface: the surface
        """
        r = pygame.Rect(self.position, self.size)
        r_clipped = r.clip(surface.get_rect())

        if self.visible and self.opacity > 0 and r_clipped.size > (0, 0):  # only draw visible widgets
            if self.opacity < 1 or r != r_clipped:
                # Draw the surface on a temporary surface.
                s = pygame.Surface(self.size, flags=pygame.SRCALPHA)
                self._render(s)

                # Apply the transparency.
                if self.opacity < 1:
                    alphas = pygame.surfarray.pixels_alpha(s)
                    alphas *= self.opacity
                    del alphas

                # Get the visible area.
                if r != r_clipped:
                    s = s.subsurface(r_clipped.topleft - self.position, r_clipped.size)

                # Copy the result.
                surface.blit(s, r_clipped.topleft)
            else:
                s = surface.subsurface(self.position, self.size)
                self._render(s)

    def _render(self, surface):
        """
        Overwrite this method in your subclass X of Widget to implement the drawing. At the end, you should call
        super(X, self)._render(surface), so the sub widgets are rendered as well.
        Keep in mind that surface already has the widget's size, so the translation by self.position is not necessary.
        :param surface: the surface
        """
        self._widgets.sort(key=lambda ww: ww.z_index)
        for w in self._widgets:
            w.render(surface)

    def update(self, elapsed_time):
        """
        Update the widget.
        """
        for a in self._actions[:]:
            if a.act(self, elapsed_time):
                self._actions.remove(a)
        for w in self._widgets:
            w.update(elapsed_time)


class ImageWidget(Widget):
    """
    A widget that contains a single image.
    """

    def __init__(self, position, size, z_index, img, style="stretch", *args, **kwargs):
        super(ImageWidget, self).__init__(position, size, z_index, *args, **kwargs)
        self._image = img
        self._scaled_image = img
        self._style = style
        if style == "stretch":
            self._image_func = self._stretch_image
        else:
            raise Exception("Unknown style: %s" % style)

    @property
    def image(self):
        return self._image_func()

    def _stretch_image(self):
        """
        Stretch the image to the widget size and return it.
        :return: the image
        """
        if self._scaled_image.get_size() != self.size:
            if self._image.get_size() == self.size:
                self._scaled_image = self._image
            else:
                self._scaled_image = pygame.transform.smoothscale(self._image, self.size)
        return self._scaled_image

    def _render(self, surface):
        """
        Render the image.
        :param surface: the surface
        """
        surface.blit(self.image, (0, 0))
        super(ImageWidget, self)._render(surface)


class Text(Widget):
    """
    A widget to show text.
    """

    def __init__(self, position, size, z_index, text, font, centered=True, color=(255, 255, 255, 255),
                 fill=(0, 0, 0, 0), *args, **kwargs):
        super(Text, self).__init__(position, size, z_index, *args, **kwargs)
        self.text = text
        self.font = font
        self.centered = centered
        self.color = color
        self.fill = fill
        if not centered:
            logging.warning("Text Widget is only implemented for centered text.")
        # TODO:
        # Add "finalized" property, that draws the text to an image and renders that image instead of always
        # re-rendering the text.

    def _render(self, surface):
        """
        Render the text.
        :param surface: the surface
        """
        tmp = pygame.Surface(surface.get_size(), flags=pygame.SRCALPHA)
        tmp.blit(surface, (0, 0))
        tmp.fill(self.fill)
        font_obj = self.font.render(self.text, True, self.color)
        x = (surface.get_width() - font_obj.get_width()) / 2
        y = (surface.get_height() - font_obj.get_height()) / 2
        if x < 0 and y < 0:
            x = 0
            y = 0
            s = font_obj.subsurface((-x, -y), surface.get_size())
        elif x < 0:
            x = 0
            s = font_obj.subsurface((-x, 0), (surface.get_width(), font_obj.get_height()))
        elif y < 0:
            y = 0
            s = font_obj.subsurface((0, -y), (font_obj.get_width(), surface.get_height()))
        else:
            s = font_obj
        tmp.blit(s, (x, y))
        surface.blit(tmp, (0, 0))


class TextInput(Widget):
    """
    A widget for text input.
    """

    def __init__(self, position, width, z_index, font, padding=(0, 0, 0, 0), color=(255, 255, 255), fill=(0, 0, 0, 0),
                 text="", default_text="", default_font=None, *args, **kwargs):
        self.font = font
        self.padding = padding
        self.color = color
        self.fill = fill
        self.text = text
        self.default_text = default_text
        if default_font is None:
            self.default_font = font
        else:
            self.default_font = default_font
        self._blink_time = 0

        width += padding[1] + padding[3]
        height = font.get_linesize() + padding[0] + padding[2]
        super(TextInput, self).__init__(position, (width, height), z_index, *args, **kwargs)

    def update(self, elapsed_time):
        """
        Update the blink time.
        :param elapsed_time: time since last frame
        """
        self._blink_time += elapsed_time
        self._blink_time %= 2*BLINK_TIME
        super(TextInput, self).update(elapsed_time)

    def handle_got_focus(self):
        """
        Reset the blink timer.
        """
        self._blink_time = 0

    def _render(self, surface):
        """
        Render the widget.
        :param surface: the surface
        """
        s = pygame.Surface(self.size, flags=pygame.SRCALPHA)
        s.fill(self.fill)
        if self._blink_time < BLINK_TIME and self.focused:
            app = "|"
        else:
            app = ""
        if len(self.text) > 0 or self.focused:
            font_obj = self.font.render(self.text+app, True, self.color)
        else:
            font_obj = self.default_font.render(self.default_text+app, True, self.color)

        s.blit(font_obj, (self.padding[3], self.padding[0]))
        surface.blit(s, (0, 0))
        super(TextInput, self)._render(surface)


class Button(Widget):
    """
    A button widget.
    """

    def __init__(self, position, size, z_index, default_img, hover_img, pressed_img, *args, **kwargs):
        super(Button, self).__init__(position, size, z_index, *args, **kwargs)
        self.default_img = default_img
        self.hover_img = hover_img
        self.pressed_img = pressed_img

    def _render(self, surface):
        """
        Render the widget.
        :param surface:
        """
        img = self.default_img
        if self.pressed:
            img = self.pressed_img
        elif self.hovered:
            img = self.hover_img
        surface.blit(img, (0, 0))
        super(Button, self)._render(surface)
