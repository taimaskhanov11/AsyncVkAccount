import asyncio
import multiprocessing
from multiprocessing import Process
from threading import Thread

from settings import tg_id, tg_token, vk_tokens
from vk_bot import AdminAccount, upload_all_data_main
from core.handlers.validator_handler import scr, skd


def split_list(a_list):
    half = len(a_list) // 2
    return a_list[:half], a_list[half:]


async def main(token):
    await upload_all_data_main(statusbar=False)
    vk = AdminAccount(token, tg_token, tg_id)
    await vk.run_session()


def start(token):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(token))
    asyncio.run(main(token))


def multi_main():
    # Thread(target=scr).start()
    # Thread(target=skd).start()
    if len(vk_tokens) > 1:
        for token in vk_tokens:
            Process(target=start, args=(token,)).start()
    else:
        print("Один токен")
        start(vk_tokens[0])


if __name__ == "__main__":
    # asyncio.run(main())
    multiprocessing.freeze_support()
    multi_main()
    # start()
    # main()
    # Thread(target=scr).start()  # todo #ph
    # Thread(target=send_keyboard).start()  # todo #key

