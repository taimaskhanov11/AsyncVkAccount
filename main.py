import asyncio
import multiprocessing
import threading
from multiprocessing import Process

import vk_bot
import queue
from core import validators
from core.database.models import DbUser
from core.database.tortoise_db import init_tortoise
from core.handlers.log_message import LogMessage, AsyncLogMessage
from core.handlers.log_router import log_handler
from core.handlers.validator_handler import validator_handler
from core.loggers.function_logger import flog
from core.message_handler import message_handler
from settings import db_config, tg_id, tg_token, vk_tokens, settings


async def asyncio_start(log_message, async_log_collector):
    loop = asyncio.get_event_loop()
    accounts = []
    for token in vk_tokens:
        acc_log_message = AsyncLogMessage(async_log_collector)
        acc_log_message('start_type', f'АСИНХРОННО {token}')
        accounts.append(vk_bot.AdminAccount(token, tg_token, tg_id, acc_log_message))
    [loop.create_task(acc.run_session()) for acc in accounts]
    await log_message.run_async_worker()


def asyncio_main():
    async_log_collector = asyncio.Queue()
    log_message = AsyncLogMessage(async_log_collector)
    init_logging_main(log_message)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(asyncio_start(log_message, async_log_collector))


def init_logging_main(log_message: LogMessage) -> None:
    log_handler.init_choice_logging(
        'vk_bot',
        *vk_bot.__all__,
        log_collector=log_message
    )
    vk_bot.find_most_city = flog(vk_bot.find_most_city, log_collector=log_message)
    # utils.find_most_city = flog(utils.find_most_city, log_collector=log_collector)
    validators.UserValidator = validator_handler(validators.UserValidator,
                                                 log_collector=log_message,
                                                 exclude=['validate'])  # todo
    message_handler.MessageHandler = log_handler(message_handler.MessageHandler,
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
        vk_bot.upload_all_data_main(statusbar=False)

        match settings['startup_type']:
            case 'async':
                asyncio_main()
            case 'process':
                run_queue_on_process()
            case 'thread':
                run_queue_on_thread()
            case _:
                print('Неправильный тип запуска')

    finally:
        pass
        # asyncio.run(delete_all())


async def delete_all():
    await init_tortoise(*db_config.values())
    await DbUser.delete_all()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    # asyncio.run(main())
    main()

