import asyncio
import multiprocessing
import threading
from multiprocessing import Process

from tortoise import Tortoise

import settings
import vk_bot
from core import validators
from core.classes import base_user
from core.database.models import DbUser
from core.database.tortoise_db import init_tortoise
from core.handlers.log_message import AsyncLogMessage, LogMessage
from core.handlers.log_router import log_handler
from core.handlers.validator_handler import validator_handler
from core.loggers.function_logger import flog
from core.message_handler import message_handler
from settings import db_config, tg_id, tg_token, vk_tokens

conversation_stages = {f'state{i}': [f'test{i}_1', f'test{i}_2'] for i in range(100)}
settings.conversation_stages = conversation_stages
vk_bot.conversation_stages = conversation_stages
base_user.conversation_stages = conversation_stages



async def user_creator_start(log_message):
    try:
        loop = asyncio.get_event_loop()
        accounts = [vk_bot.AdminAccount(token, tg_token, tg_id, log_message) for token in vk_tokens]
        [loop.create_task(acc.run_session()) for acc in accounts]
        await log_message.run_async_worker()
    finally:
        await delete_all()


def user_creator():
    vk_bot.upload_all_data_main(statusbar=False)
    async_log_collector = asyncio.Queue()
    log_message = AsyncLogMessage(async_log_collector)
    init_logging_main(log_message)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(user_creator_start(log_message))


async def start(token, log_collector):
    vk = vk_bot.AdminAccount(token, tg_token, tg_id, log_collector)
    await vk.run_session()


def main(token, log_collector):
    log_message = LogMessage(log_collector)
    init_logging_main(log_message)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(start(token, log_collector))
    # asyncio.run(main(token))


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



def run_queue_on_process(log_message: LogMessage, log_collector):
    if len(vk_tokens) > 1:
        processes = [Process(target=main, args=(token, log_collector), daemon=True) for token in vk_tokens]
        [pr.start() for pr in processes]
        print(Tortoise._connections)
        log_message.run_process_worker()
    else:
        log_process = multiprocessing.Process(target=log_message.run_process_worker)  # todo
        log_process.start()
        print("Один токен")
        main(vk_tokens[0], log_collector)


def multi_main():
    try:
        vk_bot.upload_all_data_main(statusbar=False)
        log_collector = multiprocessing.Queue()
        # log_collector = Queue()
        log_message = LogMessage(log_collector)
        # run_queue_on_thread(log_message, log_collector)
        run_queue_on_process(log_message, log_collector)

    finally:
        pass



async def delete_all():
    await init_tortoise(*db_config.values())
    await DbUser.delete_all()


if __name__ == "__main__":
    # multiprocessing.freeze_support()
    # asyncio.run(main())
    # multi_main()
    user_creator()
    asyncio.run(delete_all())

