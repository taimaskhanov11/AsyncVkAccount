import asyncio
import multiprocessing

from core.handlers import text_handler
from core.log_settings import exp_log, not_answer_log
from settings import signs


class LogMessage:

    def __init__(self, log_collector_queue):
        self.queue = log_collector_queue

    def __call__(self, func_name, *args):
        self.queue.put((func_name, args))

    def run_process_worker(self):
        """Для запуска в отдельном процессе"""
        while True:
            func_name, args = self.queue.get()
            # print(func_name, args)
            func = getattr(self, func_name)
            # print(func_name, args)
            func(*args)

    async def run_async_worker(self):
        while True:
            func_name, args = await self.queue.get()
            # print('func', '=', func_name, args)
            func = getattr(self, func_name)
            # func(*args)
            await asyncio.gather(
                asyncio.to_thread(func, *args)
            )
            self.queue.task_done()

            # print('task_done')
    @staticmethod
    def start_type(text):
        text_handler(signs['green'],
                     text,
                     'info',)



    @staticmethod
    def prog_log(text):
        text_handler(signs['time'],
                     text,
                     'debug',
                     talk=False, prop=True)

    @staticmethod
    def exp_log_error(e):
        exp_log.error(e)

    @staticmethod
    def blacklist_message(name, text):
        text_handler(signs['red'],
                     f'Новое сообщение от {name}/Черный список/: {text}',
                     'error')

    @staticmethod
    def bad_word(name, user_id, ):
        text_handler(signs['red'],
                     f'{name}/{user_id}| Запрещенное слово, добавлен в unverified_users',
                     'error')

    @staticmethod
    def auth_error(e):
        text_handler(signs['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error'),
        exp_log.exception(e)

    @staticmethod
    def acc_block_error(e, token):
        exp_log.error(e)
        text_handler(signs['version'], f'Ошибка токена {token}', 'error',
                     color='red')

    @staticmethod
    def process_info(name, loop_name, process_name, thread_name):
        text_handler(signs['queue'], f'{name}\n'
                                     f'Текущий цик событий {loop_name}\n'
                                     f'Текущий поток {process_name}, {thread_name}', color='magenta')

    @staticmethod
    def new_user_message(first_name, user_id, text):
        text_handler(signs['green'],
                     f'Новое сообщение от {first_name}/{user_id}/Нету в базе - {text}',
                     'warning')

    @staticmethod
    def auth_user_message(name, user_id, text):
        text_handler(signs['green'],
                     f'Новое сообщение от {name} / {user_id} - {text}...',
                     'info')  # todo

    @staticmethod
    def spam_message(name, user_id, text):
        text_handler(signs['yellow'],
                     f'Новое сообщение от {name} /{user_id}/SPAM  - {text}',
                     'warning'),  # todo

    @staticmethod
    def verification_successful(user_id, first_name):
        text_handler(signs['mark'],
                     f'{user_id} / {first_name} / Прошел все проверки / Добавлен в verified_users',
                     'info')

    @staticmethod
    def verification_failed(user_id, first_name):
        text_handler(signs['red'],
                     f'{user_id}/{first_name}/Проверку не прошел/Добавлен в unverified_users',
                     'error')

    @staticmethod
    def friend_status(add_status):
        text_handler(signs['yellow'], f"Статус дружбы {add_status}", 'warning')

    @staticmethod
    def adding_friend(name):
        text_handler(signs['yellow'], f"{name}/Добавление в друзья", 'warning')

    @staticmethod
    def friend_status_0(name):
        text_handler(signs['yellow'], f"{name}/Статус дружбы 0", 'warning')

    @staticmethod
    def stopping_loop(first_name, ):
        text_handler(signs['red'], f'{first_name} | Остановка цикла событий!', 'info',
                     color='red')

    @staticmethod
    def template_invalid(user_id, name):
        text_handler(signs['red'],
                     f"{user_id} / {name}"
                     f" / Стадия 7 или больше / Игнор / Проверка на номер ",
                     'error')

    @staticmethod
    def template_valid(self):
        pass

    @staticmethod
    def signal_checking(first_name):
        text_handler(signs['sun'],
                     f'{first_name} | Чекер сигнала запущен!',
                     color='cyan')

    @staticmethod
    def wait_for_verification(user_id, delay):
        text_handler(signs['time'], f'Ожидаем завершения проверки {user_id} {delay} sec', 'warning', 'cyan')
        exp_log.error(f'Ожидаем завершения проверки {user_id} {delay} sec')

    @staticmethod
    def time_track_stop(text):
        text_handler(signs['time'], text, 'debug', color='blue',
                     prop=True)

    @staticmethod
    def no_answer_found(user_id, name, text):
        not_answer_log.warning(f'{user_id} {name} --> {text}')

    """************************* Base functions ****************"""

    @staticmethod
    def number_success(user_id: int, name: str, text: str):
        text_handler(
            signs["number"],
            f"{user_id} / {name} Номер получен {text}| Добавление в unverified_users",
            'warning'
        )
        text_handler(
            signs["tg"],
            f"Отправка данных пользователя {name} в telegram",
            "warning",
            color="blue",
        ),

    """************************* MessageHandler functions ****************"""

    @staticmethod
    def run_worker_start(first_name):
        text_handler(signs['sun'], f'{first_name} | Обработчик сообщений запущен!',
                     color='blue')

    @staticmethod
    def run_worker_end(first_name):
        text_handler(signs['red'],
                     f'{first_name} | Завершение обработчика!', 'info',
                     color='red')

    @staticmethod
    def waiting_message(name, text, delay_for_acc):
        text_handler(signs['message'],
                     f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено',
                     'info', 'blue')
        text_handler(signs['queue'],
                     f'Ожидание очереди. Тайминг {delay_for_acc} s',
                     'info', 'cyan')

    @staticmethod
    def message_send_success(name, text):
        text_handler(signs['message'],
                     f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено',
                     'info', 'blue')

    """ValidatorHandler"""

    @staticmethod
    def validator_checking(text):
        text_handler(signs['yellow'], text, 'warning')

    @staticmethod
    def validator_success(text):
        text_handler(signs['yellow'], text)

    @staticmethod
    def validator_failure(text):
        text_handler(signs['red'], text, 'error')

    """PhotoUploader"""

    @staticmethod
    def photos_uploaded(name):
        text_handler(signs['version'], f'{name} | Фото выгружены', color='black')

    """MessageSenderFromDb"""

    @staticmethod
    def message_db_worker_start(name):
        text_handler(signs['sun'], f'{name} | Обработчик сообщений запущен из базы данных запущен!',
                     color='blue')

    @staticmethod
    def db_message_send(name, text):
        text_handler(signs['message'],
                     f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено',
                     'info', 'blue')

    @staticmethod
    def message_db_end(name):
        text_handler(signs['red'],
                     f'{name} | Завершение обработчика сообщений через бд!', 'info',
                     color='red')


class AsyncLogMessage(LogMessage):

    def __call__(self, func_name, *args):
        # print(func_name, *args,'AsyncLogMessage' )
        self.queue.put_nowait((func_name, args))


