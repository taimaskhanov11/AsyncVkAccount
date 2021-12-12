import asyncio
import functools
import inspect
import os
import time

# from core.handlers.text_handler import text_handler
from settings import settings, signs

accept_handling = settings['text_handler_controller']['accept_handling']  # todo


class FunctionLogger:

    def __call__(self, *args, **kwargs):
        log_collector = kwargs.get('log_collector')
        # print(log_collector)
        # if not log_collector:
        #     print('*'*40)
        #     print(args, kwargs)
        exclude = kwargs.get('exclude')
        include = kwargs.get('include')
        print(args)

        def error_logger(func):
            # if func.__name__ == 'find_most_city':
            #     print(func, "FIND")

            path = os.path.basename(inspect.getsourcefile(func))

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):

                now = time.monotonic()  # todo
                # await asyncio.to_thread(text_handler, signs['tg'], f'НАЧАЛО {func.__name__}|{args} {kwargs}', 'info',
                #                         prop=True)

                # text_handler( signs['tg'], f'НАЧАЛО {func.__name__}|{args} {kwargs}', 'info',
                #                         prop=True)
                # print(log_collector,1, 'a')
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
                # print(log_collector)
                # print(func.__name__,1, 'a')

                if accept_handling:
                    # print(func.__name__, 2, 'a')

                    log_collector('prog_log', f'{func_name:<36} {execute_time:<19} {"|async":<6}| {args} {kwargs}')
                    # print(func.__name__, 3, 'a')

                    # await asyncio.to_thread(text_handler, signs['time'],
                    #                         f'{func_name:<36} {execute_time:<19} {"|async":<6}| {args} {kwargs} ',
                    #                         'debug',
                    #                         off_interface=True, talk=False, prop=True)

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
                # print(func.__name__,1)

                if accept_handling:
                    print(func_name)
                    log_collector('prog_log', f'{func_name:<36} {execute_time:<19} {"|sync":<6}| {args} {kwargs}')
                    # print(func.__name__, 3)

                    #
                    # text_handler(signs['time'], f'{func_name:<36} {execute_time:<19} {"|sync":<6}| {args} {kwargs}',
                    #              'debug',
                    #              off_interface=True, talk=False, prop=True)

                return res

            if include:
                if func.__name__ not in include:
                    return func

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        if not len(args):
            return error_logger
        elif len(args) == 1 and callable(args[0]):
            return error_logger(args[0])
        raise ValueError('You used the logging decorator incorrectly. Read the documentation.')


flog = FunctionLogger()
