import inspect
import sys

from core.handlers.log_message import LogMessage
from core.loggers.class_logger import clog, flog


class Router:

    def __call__(self, *args, **kwargs):
        # print(*args, kwargs)
        log_collector = kwargs.get('log_collector')
        exclude = kwargs.get('exclude')
        include = kwargs.get('include')

        def decorator(obj):

            if include:
                if obj.__name__ not in include:
                    return obj

            if inspect.isfunction(obj):
                return flog(obj, log_collector=log_collector)
            elif inspect.isclass(obj):
                return clog(obj, log_collector=log_collector)
            else:
                print(obj)

        if not len(args):
            return decorator
        elif len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        raise ValueError('You used the logging decorator incorrectly. Read the documentation.')
        # return decorator

    @staticmethod
    def init_module_logging(module):
        current_module = sys.modules[module]
        for v_name in dir(current_module):
            v = getattr(current_module, v_name)
            setattr(current_module, v_name, log_handler(v))

    @staticmethod
    def init_choice_logging(module: str,
                            *obj,
                            log_collector: LogMessage,
                            **kwargs):
        current_module = sys.modules[module]
        for v_name in dir(current_module):
            if v_name in obj:
                v = getattr(current_module, v_name)
                setattr(current_module, v_name, log_handler(v, log_collector=log_collector))


log_handler = Router()
