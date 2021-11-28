from more_termcolor import colored

from core.log_settings import prop_log, talk_log
from settings import log_colors, settings, text_settings

accept_handling = settings['text_handler_controller']['accept_handling']


def text_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
    if not accept_handling:
        return

    if not color:
        color = log_colors[log_type][0]

    if text_settings['accept_logging']:
        if talk:
            talk_log.__getattribute__(log_type)(f'{sign} {text}')
        if prop:
            if talk:
                prop_log.__getattribute__('info')(text)
            else:
                prop_log.__getattribute__(log_type)(text)

    if text_settings['accept_printing']:
        p_sign = colored(sign, f'bright {color}')
        if prop:
            if text_settings['accept_print_property']:
                print(f'{p_sign} {text}')
        else:
            print(f'{p_sign} {text}')
