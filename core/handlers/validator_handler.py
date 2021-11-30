from .text_handler import text_handler
from core.log_settings import exp_log
from settings import signs, views


def validator_handler(func):
    validator = views['validators'][func.__name__]

    def wrapper(*args, **kwargs):
        text_handler(signs['yellow'], validator['check'], 'warning')
        res = func(*args, **kwargs)
        if res:
            text_handler(signs['yellow'], validator['success'])
        else:
            text_handler(signs['red'], validator['failure'], 'error')
        # if func.__name__ == 'mens_validator':
        #     if res[0]:
        #         text_handler(signs['yellow'], validator['success'].format(res[1]))
        #     else:
        #         text_handler(signs['red'], validator['failure'], 'error').format(res[1])
        # else:
        #     if res:
        #         text_handler(signs['yellow'], validator['success'])
        #     else:
        #         text_handler(signs['red'], validator['failure'], 'error')
        return res

    return wrapper
