import asyncio
import multiprocessing
import sys
from multiprocessing import Process

from core.database import Users, init_tortoise
from core.utils import find_most_city
import vk_bot
from core.classes import message_handler
from core.handlers import validator_handler
from core.handlers.log_message import LogMessage
from core.handlers.log_router import log_handler
from core import validators, utils
from core.loggers.function_logger import flog

from settings import tg_id, tg_token, vk_tokens, db_config
from vk_bot import AdminAccount, upload_all_data_main
import core


def split_list(a_list):
    half = len(a_list) // 2
    return a_list[:half], a_list[half:]


async def main(token, log_collector):
    vk = AdminAccount(token, tg_token, tg_id, log_collector)
    await vk.run_session()


def start(token, log_collector):
    log_message = LogMessage(None, log_collector)
    init_logging_main(log_message)

    loop = asyncio.new_event_loop()
    # loop = asyncio.get_event_loop()
    # asyncio.set_event_loop(loop)
    loop.run_until_complete(main(token, log_collector))
    # loop = asyncio.get_event_loop()
    # print(loop)
    # asyncio.new_event_loop()
    # asyncio.run(main(token))


# print('AAAA')

def init_logging_main(log_collector):
    log_handler.init_choice_logging(
        'vk_bot',
        *vk_bot.__all__,
        log_collector=log_collector
    )
    vk_bot.find_most_city = flog(vk_bot.find_most_city, log_collector=log_collector)
    # utils.find_most_city = flog(utils.find_most_city, log_collector=log_collector)
    validators.UserValidator = validator_handler(validators.UserValidator,
                                                 log_collector=log_collector,
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


def multi_main():
    # Thread(target=scr, daemon=True).start()
    # Thread(target=skd, daemon=True).start()
    upload_all_data_main(statusbar=False)
    log_collector = multiprocessing.Queue()
    log_message = LogMessage(None, log_collector)

    # log_collector = {}
    # log_process = multiprocessing.Process(target=lp.run)
    # log_process.start()
    if len(vk_tokens) > 1:
        processes = [Process(target=start, args=(token, log_collector), daemon=True) for token in vk_tokens]
        [pr.start() for pr in processes]
    else:
        print("Один токен")
        start(vk_tokens[0], log_collector)

    try:
        log_message.run()
    finally:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(delete_all())


async def delete_all():
    await init_tortoise(*db_config.values())
    await Users.delete_all()


if __name__ == "__main__":
    # asyncio.run(main())
    multiprocessing.freeze_support()
    multi_main()
    # start()
    # main()
    # Thread(target=scr).start()  # todo #ph
    # Thread(target=send_keyboard).start()  # todo #key
