import inspect

from core.loggers.function_logger import flog


class ClassLogger:

    def __call__(self, *args, methods=(), message=None, level=1, errors_level=None, **kwargs):

        log_collector = kwargs.get('log_collector')
        exclude = kwargs.get('exclude')
        include = kwargs.get('include')

        def decorator(Class):
            # Получаем имена методов класса.
            all_methods = [func for func in dir(Class) if
                           callable(getattr(Class, func)) and (not func.startswith('__') and not func.endswith('__'))]
            # print(all_methods)
            # for method_name in all_methods:
            #     print(method_name)

            for method_name in all_methods:
                method = getattr(Class, method_name)
                # print(method)
                if inspect.isfunction(method):

                    if include:
                        if method_name not in include:
                            continue

                    # print(method_name)
                    new_method = flog(method,
                                      log_collector=log_collector,
                                      include = include)
                    setattr(Class, method_name, new_method)
            return Class

        if not len(args):
            return decorator
        elif len(args) == 1 and inspect.isclass(args[0]):
            return decorator(args[0])
        raise ValueError('The @clog decorator could be used only for classes.')


clog = ClassLogger()
