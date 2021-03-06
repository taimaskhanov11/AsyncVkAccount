import functools
import inspect

from settings import views
from .log_message import LogMessage
from .log_router import log_handler


class ValidatorHandler:

    def __call__(self, *args,
                 log_collector: LogMessage,
                 **kwargs):
        exclude: list = kwargs.get('exclude')

        def decorator(Class):
            def func_decor(func):
                validator = views['validators'][func.__name__]

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    log_collector('validator_checking', validator['check'])
                    res = func(*args, **kwargs)
                    if res:
                        log_collector('validator_success', validator['success'])
                        # text_handler(signs['yellow'], validator['success'])
                    else:
                        log_collector('validator_failure', validator['failure'])
                        # text_handler(signs['red'], validator['failure'], 'error')
                    return res

                return wrapper

            # Получаем имена методов класса.
            all_methods = [func for func in dir(Class) if
                           callable(getattr(Class, func)) and (not func.startswith('__') and not func.endswith('__'))]

            for method_name in all_methods:
                method = getattr(Class, method_name)
                # print(method)
                if inspect.isfunction(method):

                    if method_name in exclude:
                        continue

                    if method_name in ['photo_validator', 'age_validator',
                                       'mens_validator', 'count_friends_validator']:
                        new_method = log_handler(func_decor(method), log_collector=log_collector)  # todo
                    else:
                        new_method = log_handler(method, log_collector=log_collector)
                    setattr(Class, method_name, new_method)
            return Class

        if not len(args):
            return decorator
        elif len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        raise ValueError('You used the logging decorator incorrectly. Read the documentation.')


validator_handler = ValidatorHandler()
