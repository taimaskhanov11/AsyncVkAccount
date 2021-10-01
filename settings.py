import functools
import inspect
import json
import os
import pathlib
import time
from more_termcolor import colored
from logs.log_settings import talk_log, prop_log

# import pkgutil
# import pathlib
# import importlib
# import pathlib
# print(LOG_DIR)
# BASE_DIR = os.path.dirname(os.getcwd())
# # my_path = os.path.join(BASE_DIR, "logs/log_settings.py")
# my_path = os.path.join(BASE_DIR, "logs/log_settings.py")

# # np = importlib.import_module('log_settings', path)
# path2= pathlib.Path(my_path)
# print(pathlib.Path.home())

set_dir = os.path.join(os.path.dirname(__file__), 'settings.json')
print(pathlib.Path(__file__).parent)
# print(set_dir)

# print(set_dir)


with open(set_dir, 'r', encoding='utf-8-sig') as f:
    settings = json.load(f)

VERSION = settings['version']
TEXT_HANDLER_CONTROLLER = settings['text_handler_controller']
SIGNS = settings['signs']
LOG_COLORS = settings['log_colors']

if TEXT_HANDLER_CONTROLLER['accept_interface']:
    from interface.async_main import interface


async def TextHandler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
    if not color:
        color = LOG_COLORS[log_type][0]
    if TEXT_HANDLER_CONTROLLER['accept_logging']:
        if talk:
            talk_log.__getattribute__(log_type)(f'{sign} {text}')
        if prop:
            prop_log.__getattribute__(log_type)(text)

    if TEXT_HANDLER_CONTROLLER['accept_printing']:
        p_sign = colored(sign, f'bright {color}')
        if prop:
            if TEXT_HANDLER_CONTROLLER['accept_print_property']:
                print(f'{p_sign} {text}')
        else:
            print(f'{p_sign} {text}')

    if TEXT_HANDLER_CONTROLLER['accept_interface']:
        if not off_interface:
            await interface(sign, text, color, full)


def time_track(func):
    path = os.path.basename(inspect.getsourcefile(func))

    def wrapper(*args, **kwargs):
        now = time.time()
        res = func(*args, **kwargs)
        end = time.time() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        print(func_name)
        TextHandler(SIGNS['time'], f'{func_name:<36} {execute_time}', 'debug',
                    off_interface=True, talk=False, prop=True)
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return wrapper


def async_time_track(func):
    path = os.path.basename(inspect.getsourcefile(func))

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        now = time.time()
        res = await func(*args, **kwargs)
        end = time.time() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        await TextHandler(SIGNS['time'], f'{func_name:<36} {execute_time}', 'debug',
                          off_interface=True, talk=False, prop=True)
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return wrapper
