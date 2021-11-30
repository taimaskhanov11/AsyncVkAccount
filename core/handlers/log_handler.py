import inspect
import sys

from settings import settings
from core.loggers.class_logger import clog,flog

accept_handling = settings['text_handler_controller']['accept_handling']


class Router:

    def __call__(self, *args, **kwargs):
        # print(args)

        def decorator(obj):
            # Если отключен хендлер возвращаем тот же объект
            if not accept_handling:
                return obj

            if inspect.isfunction(obj):
                return flog(obj)
            elif inspect.isclass(obj):
                return clog(obj)
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

    def init_choice_logging(self, module,*obj):
        current_module = sys.modules[module]
        for v_name in dir(current_module):
            if v_name in obj:
                v = getattr(current_module, v_name)
                setattr(current_module, v_name, log_handler(v))


log_handler = Router()
