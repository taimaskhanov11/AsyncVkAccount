import asyncio
import functools
import inspect
import os
import time

from core.handlers.text_handler import text_handler
from settings import settings, signs

accept_handling = settings['text_handler_controller']['accept_handling']  # todo


class FunctionLogger:

    def __call__(self, *args, **kwargs):
        def error_logger(func):
            path = os.path.basename(inspect.getsourcefile(func))

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):

                now = time.monotonic()  # todo
                # await asyncio.to_thread(text_handler, signs['tg'], f'НАЧАЛО {func.__name__}|{args} {kwargs}', 'info',
                #                         prop=True)

                # text_handler( signs['tg'], f'НАЧАЛО {func.__name__}|{args} {kwargs}', 'info',
                #                         prop=True)
                res = await func(*args, **kwargs)
                # await asyncio.to_thread(text_handler, signs['tg'], f'КОНЕЦ {func.__name__}|{args} {kwargs}', 'info',
                #                         prop=True)

                # text_handler( signs['tg'], f'КОНЕЦ {func.__name__}|{args} {kwargs}', 'info',
                #                         prop=True)

                end = time.monotonic() - now

                execute_time = f'{"Executed time"} {round(end, 5)}'
                func_name = f'{path}/{func.__name__}'
                # print(func.__name__)
                # print(func)
                # print(text_handler.__name__)
                # print(text_handler)
                # print(path)
                if accept_handling:
                    await asyncio.to_thread(text_handler, signs['time'],
                                            f'{func_name:<36} {execute_time:<19} {"|async":<6}| {args} {kwargs} ',
                                            'debug',
                                            off_interface=True, talk=False, prop=True)
                    # text_handler(signs['time'],
                    #              f'{func_name:<36} {execute_time:<19} {"|async":<6}| {args} {kwargs} ',
                    #              'debug',
                    #              off_interface=True, talk=False, prop=True)
                return res

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                now = time.monotonic()

                # text_handler(signs['tg'], f'НАЧАЛО {func.__name__}|{args} {kwargs}', 'info', prop=True)
                res = func(*args, **kwargs)
                # text_handler(signs['tg'], f'КОНЕЦ {func.__name__}|{args} {kwargs}', 'info', prop=True)

                end = time.monotonic() - now
                execute_time = f'{"Executed time"} {round(end, 5)}'
                func_name = f'{path}/{func.__name__}'
                if accept_handling:
                    text_handler(signs['time'], f'{func_name:<36} {execute_time:<19} {"|sync":<6}| {args} {kwargs}',
                                 'debug',
                                 off_interface=True, talk=False, prop=True)
                return res

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        if not len(args):
            return error_logger
        elif len(args) == 1 and callable(args[0]):
            return error_logger(args[0])
        raise ValueError('You used the logging decorator incorrectly. Read the documentation.')


flog = FunctionLogger()
