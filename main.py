import asyncio
import multiprocessing
from multiprocessing import Process

from core.handlers.log_message import LogMessage
from settings import tg_id, tg_token, vk_tokens
from vk_bot import AdminAccount, upload_all_data_main


def split_list(a_list):
    half = len(a_list) // 2
    return a_list[:half], a_list[half:]


async def main(token, log_collector):
    vk = AdminAccount(token, tg_token, tg_id, log_collector)
    await vk.run_session()


def start(token, log_collector):
    loop = asyncio.new_event_loop()
    # loop = asyncio.get_event_loop()
    # asyncio.set_event_loop(loop)
    loop.run_until_complete(main(token, log_collector))
    # loop = asyncio.get_event_loop()
    # print(loop)
    # asyncio.new_event_loop()
    # asyncio.run(main(token))


def multi_main():
    # Thread(target=scr, daemon=True).start()
    # Thread(target=skd, daemon=True).start()
    upload_all_data_main(statusbar=False)
    LOG_COLLECTOR = multiprocessing.Queue()
    log = LogMessage(None, LOG_COLLECTOR)

    # LOG_COLLECTOR = {}
    # log_process = multiprocessing.Process(target=lp.run)
    # log_process.start()
    if len(vk_tokens) > 1:
        processes = [Process(target=start, args=(token, LOG_COLLECTOR), daemon=True) for token in vk_tokens]
        [pr.start() for pr in processes]
    else:
        print("Один токен")
        start(vk_tokens[0], LOG_COLLECTOR)

    log.run()


if __name__ == "__main__":
    # asyncio.run(main())
    multiprocessing.freeze_support()
    multi_main()
    # start()
    # main()
    # Thread(target=scr).start()  # todo #ph
    # Thread(target=send_keyboard).start()  # todo #key
