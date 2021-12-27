import asyncio
import queue
import threading

from core.new_log_settings import logger


# def text_handler():
#
#     logger.log()

class LogMessage:

    def __init__(self, log_collector_queue: queue.Queue):
        self.queue = log_collector_queue

    def __call__(self, func_name, *args):
        self.queue.put_nowait((func_name, args))
        # self.queue.put((func_name, args))

    def run_thread_worker(self):
        logger.info(f'ПОТОК ОБРАБОТЧИК {threading.current_thread()}')
        while True:
            # print(self.queue.unfinished_tasks)
            # time.sleep(2)
            func_name, args = self.queue.get()
            # print(func_name, args)
            func = getattr(self, func_name)
            # print(func_name, args)
            func(*args)
            self.queue.task_done()
            logger.debug(f'Незавершенных задач осталось {self.queue.unfinished_tasks}')

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
            await asyncio.to_thread(func, *args)

            self.queue.task_done()

            # print('task_done')

    @staticmethod
    def start_type(text):
        # text_handler(signs['green'],
        #              text,
        #              'info', )
        logger.info(text)

    @staticmethod
    def parse_message_event(first_name):
        # text_handler(signs['sun'], f'{first_name}| Парсер сообщений запущен!',
        #              color='blue')
        logger.info(f'{first_name}| Парсер сообщений запущен!')

    @staticmethod
    def prog_log(text):
        # text_handler(text,
        #              'debug',
        #              talk=False, prop=True)
        logger.debug(text)

    @staticmethod
    def exp_log_error(e):
        # exp_log.error(e)
        logger.warning(e)

    @staticmethod
    def token_error(e):
        # exp_log.error(e)
        logger.error(e)

    @staticmethod
    def self_info(text):
        logger.info(text)

    @staticmethod
    def blacklist_message(name, text):
        # text_handler(signs['red'],
        #              f'Новое сообщение от {name}/Черный список/: {text}',
        #              'error')
        logger.warning(f'Новое сообщение от {name}/Черный список/: {text}')

    @staticmethod
    def bad_word(name, user_id, ):
        # text_handler(signs['red'],
        #              f'{name}/{user_id}| Запрещенное слово, добавлен в unverified_users',
        #              'error')

        logger.warning(f'{name}/{user_id}| Запрещенное слово, добавлен в unverified_users')

    @staticmethod
    def auth_error(e):
        # text_handler(signs['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error'),
        # exp_log.exception(e)
        logger.critical(f'ПЕРЕПОДКЛЮЧЕНИЕ...{e}')

    @staticmethod
    def acc_block_error(e, token):
        # exp_log.error(e)
        # text_handler(signs['version'], f'Ошибка токена {token}', 'error',
        #              color='red')
        logger.error(f'Ошибка токена {token}')

    @staticmethod
    def process_info(name, loop_name, process_name, thread_name):
        # text_handler(signs['queue'], f'{name}\n'
        #                              f'Текущий цик событий {loop_name}\n'
        #                              f'Текущий поток {process_name}, {thread_name}', color='magenta')
        logger.info(f'{name}\n'
                    f'Текущий цик событий {loop_name}\n'
                    f'Текущий поток {process_name}, {thread_name}')

    @staticmethod
    def new_user_message(first_name, user_id, text):
        # text_handler(signs['green'],
        #              f'Новое сообщение от {first_name}/{user_id}/Нету в базе - {text}',
        #              'warning')
        logger.log('TALK', f'Новое сообщение от {first_name}/{user_id}/Нету в базе - {text}')

    @staticmethod
    def auth_user_message(name, user_id, text):
        # text_handler(signs['green'],
        #              f'Новое сообщение от {name} / {user_id} - {text}...',
        #              'info')  # todo
        logger.log('TALK', f'Новое сообщение от {name} / {user_id} - {text}...')

    @staticmethod
    def spam_message(name, user_id, text):
        # text_handler(signs['yellow'],
        #              f'Новое сообщение от {name} /{user_id}/SPAM  - {text}',
        #              'warning'),  # todo
        logger.log('TALK', f'Новое сообщение от {name} /{user_id}/SPAM  - {text}')

    @staticmethod
    def verification_successful(user_id, first_name):
        # text_handler(signs['mark'],
        #              f'{user_id} / {first_name} / Прошел все проверки / Добавлен в verified_users',
        #              'info')
        logger.success(f'{user_id} / {first_name} / Прошел все проверки / Добавлен в verified_users')

    @staticmethod
    def verification_failed(user_id, first_name):
        # text_handler(signs['red'],
        #              f'{user_id}/{first_name}/Проверку не прошел/Добавлен в unverified_users',
        #              'error')
        logger.warning(f'{user_id}/{first_name}/Проверку не прошел/Добавлен в unverified_users')

    @staticmethod
    def friend_status(add_status):
        # text_handler(signs['yellow'], f"Статус дружбы {add_status}", 'warning')
        logger.log('TALK', f"Статус дружбы {add_status}")

    @staticmethod
    def adding_friend(name):
        # text_handler(signs['yellow'], f"{name}/Добавление в друзья", 'warning')
        logger.log('TALK', f"{name}/Добавление в друзья")

    @staticmethod
    def friend_status_0(name):
        # text_handler(signs['yellow'], f"{name}/Статус дружбы 0", 'warning')
        logger.log('TALK', f"{name}/Статус дружбы 0")

    @staticmethod
    def stopping_loop(first_name):
        # text_handler(signs['red'], f'{first_name} | Остановка цикла событий!', 'info',
        #              color='red')
        logger.warning(f'{first_name} | Остановка цикла событий!')

    @staticmethod
    def template_invalid(user_id, name):
        # text_handler(signs['red'],
        #              f"{user_id} / {name}"
        #              f" / Стадия 7 или больше / Игнор / Проверка на номер ",
        #              'error')
        logger.log('TALK', f"{user_id} / {name}"
                           f" / Стадия 7 или больше / Игнор / Проверка на номер ")

    @staticmethod
    def template_valid(self):
        pass

    @staticmethod
    def signal_checking(first_name):

        # text_handler(signs['sun'],
        #              f'{first_name} | Чекер сигнала запущен!',
        #              color='cyan')
        logger.info(f'{first_name} | Чекер сигнала запущен!')

    @staticmethod
    def wait_for_verification(user_id, delay):
        # text_handler(signs['time'], f'Ожидаем завершения проверки {user_id} {delay} sec', 'warning', 'cyan')
        # exp_log.error(f'Ожидаем завершения проверки {user_id} {delay} sec')
        logger.warning(f'Ожидаем завершения проверки {user_id} {delay} sec')

    @staticmethod
    def time_track_stop(text):
        # text_handler(signs['time'], text, 'debug', color='blue',
        #              prop=True)
        # logger.debug(text)
        logger.debug(text)

    @staticmethod
    def no_answer_found(user_id, name, text):
        # not_answer_log.warning(f'{user_id} {name} --> {text}')
        logger.log('XANSWER', f'{user_id} {name} --> {text}')

    """************************* Base functions ****************"""

    @staticmethod
    def number_success(user_id: int, name: str, text: str):
        # text_handler(
        #     signs["number"],
        #     f"{user_id} / {name} Номер получен {text}| Добавление в unverified_users",
        #     'warning'
        # )
        # text_handler(
        #     signs["tg"],
        #     f"Отправка данных пользователя {name} в telegram",
        #     "warning",
        #     color="blue",
        # ),
        logger.info(f"{user_id} / {name} Номер получен {text}| Добавление в unverified_users")
        logger.info(f"Отправка данных пользователя {name} в telegram")

    """************************* MessageHandler functions ****************"""

    @staticmethod
    def run_worker_start(first_name):
        # text_handler(signs['sun'], f'{first_name} | Обработчик сообщений запущен!',
        #              color='blue')
        logger.info(f'{first_name} | Обработчик сообщений запущен!')

    @staticmethod
    def run_worker_end(first_name):
        # text_handler(signs['red'],
        #              f'{first_name} | Завершение обработчика!', 'info',
        #              color='red')
        logger.warning(f'{first_name} | Завершение обработчика!')

    @staticmethod
    def waiting_message(name, text, delay_for_acc):
        # text_handler(signs['message'],
        #              f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено',
        #              'info', 'blue')
        # text_handler(signs['queue'],
        #              f'Ожидание очереди. Тайминг {delay_for_acc} s',
        #              'info', 'cyan')
        #
        logger.info(f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено')
        logger.info(f'Ожидание очереди. Тайминг {delay_for_acc} s')

    @staticmethod
    def message_send_success(name, text):
        # text_handler(signs['message'],
        #              f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено',
        #              'info', 'blue')
        logger.success(f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено')

    """ValidatorHandler"""

    @staticmethod
    def validator_checking(text):
        # text_handler(signs['yellow'], text, 'warning')
        logger.info(text)

    @staticmethod
    def validator_success(text):
        # text_handler(signs['yellow'], text)
        logger.success(text)

    @staticmethod
    def validator_failure(text):
        # text_handler(signs['red'], text, 'error')
        logger.warning(text)

    """PhotoUploader"""

    @staticmethod
    def photos_uploaded(name):
        # text_handler(signs['version'], f'{name} | Фото выгружены', color='black')
        logger.info(f'{name} | Фото выгружены')

    """MessageSenderFromDb"""

    @staticmethod
    def message_db_worker_start(name):
        # text_handler(signs['sun'], f'{name} | Обработчик сообщений запущен из базы данных запущен!',
        #              color='blue')
        logger.info(f'{name} | Обработчик сообщений запущен из базы данных запущен!')

    @staticmethod
    def db_message_send(name, text):
        # text_handler(signs['message'],
        #              f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено',
        #              'info', 'blue')
        logger.info(f'Сообщение пользователю {name} c тексом: `{text}...` ⇑Отправлено')

    @staticmethod
    def message_db_end(name):
        # text_handler(signs['red'],
        #              f'{name} | Завершение обработчика сообщений через бд!', 'info',
        #              color='red')
        logger.warning(f'{name} | Завершение обработчика сообщений через бд!')

    """UserValidator"""

    @staticmethod
    def info_view(first_name, _id, count_friend, age, has_photo):
        logger.info(f"{first_name}, {_id}|{count_friend} - Количество друзей|Возраст - {age}|Фото {has_photo}")

    @staticmethod
    def incorrect_age(age):
        logger.error(f'Неккоректный возраст {age}')


class AsyncLogMessage(LogMessage):

    def __call__(self, func_name, *args):
        # print(func_name, *args,'AsyncLogMessage' )
        self.queue.put_nowait((func_name, args))


class ThreadLogMessage(LogMessage):
    pass


async def main(worker):
    asyncio.create_task(worker.run_async_worker())


async def putter(worker):
    worker('start_type', 'HELLO_WORLD`')


if __name__ == '__main__':
    # asyncio.run(main())
    async_log_collector = asyncio.Queue()

    worker = AsyncLogMessage(async_log_collector)

    loop = asyncio.new_event_loop()
    loop.create_task(main(worker))
    loop.create_task(putter(worker))
    loop.run_forever()
