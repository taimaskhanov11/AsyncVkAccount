import asyncio
import multiprocessing
from multiprocessing import Process

from settings import tg_id, tg_token, vk_tokens
from vk_bot import AdminAccount, upload_all_data_main


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

# todo добавить мультипроцессорность

# todo добавить прокси
# todo добавить для каждого пользователя класс с выгрузкой основных методов при первом запустке

# todo добавить отображение в консоли блока если

# todo тесты
# todo убрать ошибку со скрином

# todo запись общения в файл write_in_file

# todo писать сообщения
# todo добавить многопроцессорность
# todo соединят и отпавлять как одно
# todo вынести весь текст в отдельный файл
# todo класс мета для декораторов
# todo доработать мультипроцессорность
