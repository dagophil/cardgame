from widgets import ImageWidget, Button
import pygame


def warning_widget(position, size, text, font, screen_size=None, text_color=(255, 255, 255, 255), z_index=99,
                   fill=(0, 0, 0, 160), close_on_click=True):
    """
    Create an ImageWidget with the given text. If screen_size is given, position is ignored and the widget is centered.
    :param position: the position
    :param size: the widget size
    :param text: the text
    :param font: the font
    :param screen_size: the screen size
    :param text_color: the text color
    :param z_index: the z index
    :param fill: the fill color
    :return: the widget
    """
    # Create the widget.
    if screen_size is None:
        x, y = position
    else:
        x = (screen_size[0] - size[0]) / 2
        y = (screen_size[1] - size[1]) / 2
    font_obj = font.render(text, True, text_color)
    offset_x = (size[0] - font_obj.get_width()) / 2
    offset_y = (size[1] - font_obj.get_height()) / 2
    warning_bg = pygame.Surface(size, flags=pygame.SRCALPHA)
    warning_bg.fill(fill)
    warning_bg.blit(font_obj, (offset_x, offset_y))
    warning = ImageWidget((x, y), size, z_index, warning_bg, visible=False)

    # Attach the click function.
    if close_on_click:
        def warning_clicked(xx, yy):
            warning.hide()
            warning.clear_actions()
        warning.handle_clicked = warning_clicked

    return warning


def simple_button(position, size, text, font, text_color=(255, 255, 255, 255), z_index=0):
    """
    Create a simple ButtonWidget.
    :param position: the position
    :param size: the size
    :param text: the text
    :param font: the font
    :param text_color: the text color
    :param z_index: the z index
    :return: the widget
    """
    font_obj = font.render(text, True, text_color)
    offset_x = (size[0] - font_obj.get_width()) / 2
    offset_y = (size[1] - font_obj.get_height()) / 2
    offset = (offset_x, offset_y)
    btn_bg = pygame.Surface(size, flags=pygame.SRCALPHA)
    btn_bg.fill((0, 0, 0, 128))
    btn_bg.blit(font_obj, offset)
    btn_hover = pygame.Surface(size, flags=pygame.SRCALPHA)
    btn_hover.fill((0, 0, 0, 160))
    btn_hover.blit(font_obj, offset)
    btn_pressed = pygame.Surface(size, flags=pygame.SRCALPHA)
    btn_pressed.fill((0, 0, 0, 200))
    btn_pressed.blit(font_obj, offset)
    btn = Button(position, size, z_index, btn_bg, btn_hover, btn_pressed)
    return btn
