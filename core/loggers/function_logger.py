import functools
import inspect
import os
import time

from loguru import logger

from core.handlers.log_message import LogMessage


# from core.new_log_settings import logger

class FunctionLogger:

    def __call__(self,
                 *args,
                 log_collector: LogMessage,
                 **kwargs):
        exclude: list = kwargs.get('exclude')
        include: list = kwargs.get('include')
        if not args:
            log_collector('exp_log_error', f'Nor args {self}{args}{kwargs}')

        def error_logger(func):
            path = os.path.basename(inspect.getsourcefile(func))

            @logger.catch
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                now = time.monotonic()  # todo
                # todo добавить начало и конец
                res = await func(*args, **kwargs)
                end = time.monotonic() - now
                execute_time = f'{"Executed time"} {round(end, 5)}'
                func_name = f'{path}/{func.__name__}'
                log_collector('prog_log', f'{func_name:<36} {execute_time:<19} {"|async":<6}| {args} {kwargs}')
                return res

            @logger.catch
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                now = time.monotonic()
                res = func(*args, **kwargs)
                end = time.monotonic() - now
                execute_time = f'{"Executed time"} {round(end, 5)}'
                func_name = f'{path}/{func.__name__}'
                log_collector('prog_log', f'{func_name:<36} {execute_time:<19} {"|sync":<6}| {args} {kwargs}')
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
