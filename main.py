import asyncio
import multiprocessing
from multiprocessing import Process

from settings import tg_id, tg_token, vk_tokens
from vk_bot import AdminAccount, upload_all_data_main


def split_list(a_list):
    half = len(a_list) // 2
    return a_list[:half], a_list[half:]


async def main(token):
    vk = AdminAccount(token, tg_token, tg_id)
    await vk.run_session()


def start(token):
    loop = asyncio.new_event_loop()
    # loop = asyncio.get_event_loop()
    # asyncio.set_event_loop(loop)
    loop.run_until_complete(main(token))
    # loop = asyncio.get_event_loop()
    # print(loop)
    # asyncio.new_event_loop()
    # asyncio.run(main(token))


def multi_main():
    # Thread(target=scr, daemon=True).start()
    # Thread(target=skd, daemon=True).start()

    upload_all_data_main(statusbar=False)
    if len(vk_tokens) > 1:
        processes = [Process(target=start, args=(token,)) for token in vk_tokens]
        [pr.start() for pr in processes]

        # while True:
        #     time.sleep(0.5)
        #     for i in processes:
        #         print(i.is_alive())
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

