import asyncio
import functools
import inspect
import os
import time

from more_termcolor import colored

from interface.async_main import interface
from log_settings import prop_log, talk_log, exp_log
from settings import views, signs, text_settings, log_colors

__all__ = [
    'text_handler',
    # 'func_handler',
    'validator_handler',
    'log_handler'
]


def text_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
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


async def async_text_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True,
                             prop=False):
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

    if text_settings['accept_interface']:
        if not off_interface:
            await interface(sign, text, color, full)


def sync_text_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
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

    if text_settings['accept_interface']:
        if not off_interface:
            asyncio.create_task(interface(sign, text, color, full))


def time_track(func):
    path = os.path.basename(inspect.getsourcefile(func))

    # loop = asyncio.get_event_loop()
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        # print(func_name)
        sync_text_handler(signs['time'], f'{func_name:<36} {execute_time} | sync', 'debug',
                          off_interface=True, talk=False, prop=True)
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
        await async_text_handler(signs['time'], f'{func_name:<36} {execute_time} | async', 'debug',
                                 off_interface=True, talk=False, prop=True)
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return async_wrapper


def new_async_func(func):
    path = os.path.basename(inspect.getsourcefile(func))

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = await func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'

        # sync_text_handler(signs['time'], f'{func_name:<36} {execute_time} | async', 'debug',
        #                    off_interface=True, talk=False, prop=True)
        await asyncio.to_thread(sync_text_handler, signs['time'], f'{func_name:<36} {execute_time} | async', 'debug',
                                off_interface=True, talk=False, prop=True)
        return res

    return async_wrapper


def func_handler(func):
    path = os.path.basename(inspect.getsourcefile(func))

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = await func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        await asyncio.to_thread(sync_text_handler, signs['time'], f'{func_name:<36} {execute_time} | async', 'debug',
                                off_interface=True, talk=False, prop=True)
        return res

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        sync_text_handler(signs['time'], f'{func_name:<36} {execute_time} | sync', 'debug',
                          off_interface=True, talk=False, prop=True)
        return res

    if inspect.iscoroutinefunction(func):
        return async_wrapper

    return sync_wrapper


# Configure time track

def answer_cache(func, data):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, data, **kwargs)
        return res

    return wrapper


class ControlMeta(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        # pprint(attrs)
        for key, val in attrs.items():

            # todo update for match case
            if inspect.isfunction(val):

                if key in ('__init__', 'act', 'parse_event', 'start_send_message', 'send_status_tg',
                           '_start_send_message_executor'):
                    continue
                # print(val)
                if asyncio.iscoroutinefunction(val):
                    prop_log.debug(f'async {val}')
                    # attrs[key] = async_time_track(val)
                    attrs[key] = new_async_func(val)
                else:
                    prop_log.debug(f'sync {val}')
                    attrs[key] = time_track(val)
        return super().__new__(mcs, name, bases, attrs, **kwargs)


class Router:

    def __call__(self, *args, **kwargs):
        # print(args)

        def decorator(obj):
            # print(obj)
            # print(inspect.isfunction(obj), obj)
            if inspect.isfunction(obj):
                # print(obj)
                return func_handler(obj)
            else:
                all_methods = [func for func in dir(obj) if
                               callable(getattr(obj, func)) and (not func.startswith('__') and not func.endswith('__'))]
                # print(all_methods)
                # for method_name in all_methods:
                #     print(method_name)

                for method_name in all_methods:
                    method = getattr(obj, method_name)
                    # print(method)
                    if inspect.isfunction(method):
                        # print(method_name)
                        new_method = func_handler(method)
                        setattr(obj, method_name, new_method)
                return obj

        if not len(args):
            return decorator
        elif len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        raise ValueError('You used the logging decorator incorrectly. Read the documentation.')
        # return decorator


def validator_handler(func):
    validator = views['validators'][func.__name__]

    def wrapper(*args, **kwargs):
        sync_text_handler(signs['yellow'], validator['check'], 'warning')
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            print(e)
            res = False
            exp_log.exception(e)

        if func.__name__ == 'mens_validator':
            if res[0]:
                sync_text_handler(signs['yellow'], validator['success'].format(res[1]))
            else:
                sync_text_handler(signs['red'], validator['failure'], 'error').format(res[1])
        else:
            if res:
                sync_text_handler(signs['yellow'], validator['success'])
            else:
                sync_text_handler(signs['red'], validator['failure'], 'error')
            return res

    return wrapper


log_handler = Router()
