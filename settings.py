import asyncio
import functools
import inspect
import os
import time
from pathlib import Path

import json
from more_termcolor import colored

# import utilities
from interface.async_main import interface
from log_settings import prop_log, talk_log

BASE_DIR = Path(__file__).parent


def read_json(path, encoding='utf-8-sig'):
    with open(Path(BASE_DIR, path), 'r', encoding=encoding) as ff:
        return json.load(ff)


TALK_DICT_ANSWER_ALL = read_json('config/answers.json')
TALK_TEMPLATE = read_json('config/templatea.json')
settings = read_json('config/settings.json')
views = read_json('views_json/validators.json')

VERSION = settings['version']
TEXT_HANDLER_CONTROLLER = settings['text_handler_controller']
TOKENS = settings['tokens']

SIGNS = {
    "red": "✖",
    "green": "◯",
    "yellow": "⬤",
    "mark": "[✓]",
    "magenta": "►",
    "time": "⌛",
    "version": "∆"
}

LOG_COLORS = {
    "info": ["green", "◯"],
    "warning": ["yellow", "⬤"],
    "error": ["red", "✖"],
    "debug": ["white", "இ"]
}


async def text_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
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

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        # print(func_name)
        asyncio.create_task(text_handler(SIGNS['time'], f'{func_name:<36} {execute_time}', 'debug',
                                         off_interface=True, talk=False, prop=True))
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return sync_wrapper


def async_time_track(func):
    path = os.path.basename(inspect.getsourcefile(func))

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = await func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        await text_handler(SIGNS['time'], f'{func_name:<36} {execute_time}', 'debug',
                           off_interface=True, talk=False, prop=True)
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return async_wrapper


# Configure time track
def answer_cache(func, data):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, data, **kwargs)
        return res

    return wrapper

# utilities.search_answer = async_time_track(answer_cache(utilities.search_answer, TALK_DICT_ANSWER_ALL))
# utilities.find_most_city = async_time_track(utilities.find_most_city)
