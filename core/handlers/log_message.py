import asyncio
import multiprocessing
import threading
import time

from core.handlers import text_handler
from core.log_settings import exp_log, not_answer_log
from settings import signs


class LogMessage:

    def __init__(self, overlord, log_collector_queue: multiprocessing.Queue):
        # self.overlord = overlord
        self.queue = log_collector_queue

    # def run(self, queue: multiprocessing.Queue):

    def __call__(self, func_name, *args):
        self.queue.put((func_name, args))

    def run(self):
        """Для запуска в отдельном процессе"""
        while True:
            func_name, args = self.queue.get()
            # print(func_name, args)
            func = getattr(self, func_name)
            print(func_name, args)
            func(*args)

    def prog_log(self, text):
        text_handler(signs['time'],
                     text,
                     'debug',
                     off_interface=True, talk=False, prop=True)

    def blacklist_message(self, name, text):
        text_handler(signs['red'],
                     f'Новое сообщение от {name}/Черный список/: {text}',
                     'error')

    def bad_word(self, name, user_id, ):
        text_handler(signs['red'],
                     f'{name}/{user_id}| Запрещенное слово, добавлен в unverified_users',
                     'error')

    def auth_error(self, e):
        text_handler(signs['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error'),
        exp_log.exception(e)

    def acc_block_error(self, e, token):
        exp_log.error(e)
        text_handler(signs['version'], f'Ошибка токена {token}', 'error',
                     color='red')

    def process_info(self, loop_name, process_name, thread_name):
        text_handler(signs['queue'], f'Текущий цик событий {loop_name}', color='magenta')
        text_handler(signs['queue'], f'Текущий поток {process_name}, {thread_name}',
                     color='magenta')  # todo

    def new_user_message(self, first_name, user_id, text):
        text_handler(signs['green'],
                     f'Новое сообщение от {first_name}/{user_id}/Нету в базе - {text}',
                     'warning')

    def auth_user_message(self, name, user_id, text):
        text_handler(signs['green'],
                     f'Новое сообщение от {name} / {user_id} - {text[:40]}...',
                     'info')  # todo

    def spam_message(self, name, user_id, text):
        text_handler(signs['yellow'],
                     f'Новое сообщение от {name} /{user_id}/SPAM  - {text}',
                     'warning'),  # todo

    def verification_successful(self, user_id, first_name):
        text_handler(signs['mark'],
                     f'{user_id} / {first_name} / Прошел все проверки / Добавлен в verified_users',
                     'info')

    def verification_failed(self, user_id, first_name):
        text_handler(signs['red'],
                     f'{user_id}/{first_name}/Проверку не прошел/Добавлен в unverified_users',
                     'error')

    def friend_status(self, add_status):
        text_handler(signs['yellow'], f"Статус дружбы {add_status}", 'warning')

    def adding_friend(self, name):
        text_handler(signs['yellow'], f"{name}/Добавление в друзья", 'warning')

    def friend_status_0(self, name):
        text_handler(signs['yellow'], f"{name}/Статус дружбы 0", 'warning')

    def stopping_loop(self, first_name, ):
        text_handler(signs['red'], f'{first_name} | Остановка цикла событий!', 'info',
                     color='red')

    def template_invalid(self, user_id, name):
        text_handler(signs['red'],
                     f"{user_id} / {name}"
                     f" / Стадия 7 или больше / Игнор / Проверка на номер ",
                     'error')

    def template_valid(self):
        pass

    def signal_checking(self, first_name):
        text_handler(signs['sun'],
                     f'{first_name} | Чекер сигнала запущен!',
                     color='cyan')

    def wait_for_verification(self, user_id, delay):
        text_handler(signs['time'], f'Ожидаем завершения проверки {user_id} {delay} sec', 'warning', 'cyan')
        exp_log.error(f'Ожидаем завершения проверки {user_id} {delay} sec')

    def time_track_stop(self, text):
        text_handler(signs['time'], text, 'debug', color='blue',
                     off_interface=True, prop=True)

    def no_answer_found(self, user_id, name, text):
        not_answer_log.warning(f'{user_id} {name} --> {text}')

    """MessageHandler functions"""

    def run_worker_start(self, first_name):
        text_handler(signs['sun'], f'{first_name} | Обработчик сообщений запущен!',
                     color='blue')

    def run_worker_end(self, first_name):
        text_handler(signs['red'],
                     f'{first_name} | Завершение обработчика!', 'info',
                     color='red')

    def waiting_message(self, name, text, delay_for_acc):
        text_handler(signs['message'],
                     f'Сообщение пользователю {name} c тексом: `{text[:40]}...` ⇑Отправлено',
                     'info', 'blue')
        text_handler(signs['queue'],
                     f'Ожидание очереди. Тайминг {delay_for_acc} s\n',
                     'info', 'cyan')

    def message_send_success(self, name, text):
        text_handler(signs['message'],
                     f'Сообщение пользователю {name} c тексом: `{text[:40]}...` ⇑Отправлено',
                     'info', 'blue')


