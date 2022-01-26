import asyncio
import multiprocessing
import queue
import threading
import time
from multiprocessing import Process

from loguru import logger
from tqdm import trange

import vk_bot
from core import validators
from core.database.models import DbUser
from core.database.tortoise_db import init_tortoise
from core.handlers.log_message import AsyncLogMessage, LogMessage
from core.handlers.log_router import log_handler
from core.handlers.validator_handler import validator_handler
from core.loggers.function_logger import flog
from core.message_handler import message_handler
from core.validators import scr, kbr
from settings import (bot_version, db_config, message_config, settings, tg_id,
                      tg_token, vk_tokens)


# from core import new_log_settings
def upload_all_data_main(statusbar=False):
    """Инициализация данных профиля"""
    try:
        logger.info(f"VkBot v{bot_version}", '', color='blue')
        logger.info(f'Загруженно токенов {len(vk_tokens)}: ')
        for a, b in enumerate(vk_tokens, 1):
            logger.info(f"    {b}")

        delay = f"[{message_config['delay_response_from']} - {message_config['delay_response_to']}] s"
        logger.info(f"    Задержка перед ответом : {delay}")
        delay = f"[{message_config['delay_typing_from']} - {message_config['delay_typing_to']}] s"
        logger.info(f"    Длительность отображения печати : {delay}")
        # todo
        logger.info('Проверка прокси:')
        for proxy in settings['proxy']:
            logger.success('    PROXY {proxy} IS WORKING'.format(proxy=proxy))

        if statusbar:
            for _ in trange(300, colour='green', smoothing=0.1, unit_scale=True):
                time.sleep(0.001)
        # if is_bad_proxy(proxy):
        #     await TextHandler(SIGNS['magenta'], f"    BAD PROXY {proxy}", log_type='error', full=True)
        # else:
        #     await TextHandler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING')
    except Exception as e:
        logger.exception(e)


async def asyncio_start(log_message, thread_log_collector):
    loop = asyncio.get_event_loop()
    accounts = []
    for token in vk_tokens:
        # acc_log_message = AsyncLogMessage(async_log_collector)
        acc_log_message = LogMessage(thread_log_collector)

        acc_log_message('start_type', f'АСИНХРОННО {token}')
        accounts.append(vk_bot.AdminAccount(token, tg_token, tg_id, acc_log_message))
    [loop.create_task(acc.run_session()) for acc in accounts]
    # await log_message.run_async_worker()


def asyncio_main():
    # async_log_collector = asyncio.Queue()
    thread_log_collector = queue.Queue()
    # log_message = AsyncLogMessage(async_log_collector)
    log_message = LogMessage(thread_log_collector)
    init_logging_main(log_message)
    loop = asyncio.new_event_loop()
    loop.create_task(asyncio_start(log_message, thread_log_collector))
    worker_thread = threading.Thread(target=log_message.run_thread_worker)
    # worker_thread = logger.catch(worker_thread)
    worker_thread.start()

    # print('asd')
    loop.run_forever()

    # loop.run_until_complete(asyncio_start(log_message, thread_log_collector))


def init_logging_main(log_message: LogMessage) -> None:
    log_handler.init_choice_logging(
        'vk_bot',
        *vk_bot.__all__,
        log_collector=log_message
    )
    vk_bot.find_most_city = flog(vk_bot.find_most_city, log_collector=log_message)
    # utils.find_most_city = flog(utils.find_most_city, log_collector=log_collector)
    validators.UserValidator = validator_handler(
        validators.UserValidator,
        log_collector=log_message,
        exclude=['validate'])  # todo
    message_handler.MessageHandler = log_handler(
        message_handler.MessageHandler,
        include=[
            # 'run_worker',
            'search_answer',
            'uploaded_photo_from_dir',
            'uploaded_photo',
            'unverified_delaying',
            'send_delaying_message',
            'save_message'])


async def process_start(token, log_collector):
    log_message = LogMessage(log_collector)
    log_message('start_type', f'ПРОЦЕСС {token}')
    vk = vk_bot.AdminAccount(token, tg_token, tg_id, log_message)
    await vk.run_session()


def process_main(token, log_collector):
    init_logging_main(LogMessage(log_collector))
    loop = asyncio.new_event_loop()
    loop.run_until_complete(process_start(token, log_collector))
    # asyncio.run(main(token))


async def thread_start(token, log_collector):
    log_message = LogMessage(log_collector)
    log_message('start_type', f'ПОТОК {token}')
    vk = vk_bot.AdminAccount(token, tg_token, tg_id, log_message)
    await vk.run_session()


def thread_main(token, log_collector):
    init_logging_main(LogMessage(log_collector))
    loop = asyncio.new_event_loop()
    loop.run_until_complete(thread_start(token, log_collector))
    # asyncio.run(main(token))


def run_queue_on_thread():
    log_collector = queue.Queue()
    log_message = LogMessage(log_collector)
    if len(vk_tokens) > 1:
        threads = []
        for token in vk_tokens:
            threads.append(threading.Thread(target=thread_main, args=(token, log_collector), daemon=True))
        [th.start() for th in threads]
        threading.Thread(target=log_message.run_process_worker).start()
    else:
        threading.Thread(target=log_message.run_process_worker).start()
        print("Один токен")
        process_main(vk_tokens[0], log_collector)


def run_queue_on_process():
    log_collector = multiprocessing.Queue()
    log_message = LogMessage(log_collector)
    if len(vk_tokens) > 1:
        processes = []
        for token in vk_tokens:
            processes.append(Process(target=process_main, args=(token, log_collector), daemon=True))
        [pr.start() for pr in processes]
        log_message.run_process_worker()
    else:
        log_process = multiprocessing.Process(target=log_message.run_process_worker)  # todo
        log_process.start()
        print("Один токен")
        process_main(vk_tokens[0], log_collector)


def main():
    try:
        threading.Thread(target=scr).start()
        threading.Thread(target=kbr).start()

        upload_all_data_main(statusbar=False)

        match settings['startup_type']:
            case 'async':
                asyncio_main()
            case 'process':
                run_queue_on_process()
            case 'thread':
                run_queue_on_thread()
            case _:
                logger.critical('Неправильный тип запуска')

    finally:
        logger.critical('Ошибка при запуске')

        pass
        # asyncio.run(delete_all())


async def delete_all():
    await init_tortoise(*db_config.values())
    await DbUser.delete_all()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    # asyncio.run(main())
    # asyncio.run(delete_all())
    # delete_all()
    main()
