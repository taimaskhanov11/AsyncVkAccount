import inspect
import sys

from core.loggers.class_logger import clog, flog
from settings import settings

accept_handling = settings['text_handler_controller']['accept_handling']


class Router:

    def __call__(self, *args, **kwargs):
        # print(*args, kwargs)
        log_collector = kwargs.get('log_collector')
        exclude = kwargs.get('exclude')
        include = kwargs.get('include')

        def decorator(obj):

            # Если отключен хендлер возвращаем тот же объект
            if not accept_handling:
                return obj

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

    def init_module_logging(self, module):
        current_module = sys.modules[module]
        for v_name in dir(current_module):
            v = getattr(current_module, v_name)
            setattr(current_module, v_name, log_handler(v))

    def init_choice_logging(self, module, *obj, **kwargs):
        log_collector = kwargs.get('log_collector')
        # print(log_collector)

        current_module = sys.modules[module]
        # print(current_module)
        for v_name in dir(current_module):
            if v_name in obj:
                v = getattr(current_module, v_name)
                print(v)
                print(current_module)
                setattr(current_module, v_name, log_handler(v, log_collector=log_collector))


log_handler = Router()
