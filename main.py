import asyncio
import multiprocessing
from multiprocessing import Process
from threading import Thread

from interface.async_main import init_eel
from settings import text_settings, tokens
from vk_bot import VkUserControl, upload_all_data_main


def run_threads2_1(token, loop):
    # loop1 = asyncio.new_event_loop()
    upload_all_data_main()
    asyncio.set_event_loop(loop)
    # asyncio.get_event_loop()
    vk = VkUserControl(token, loop=loop)
    # loop1.create_task(vk.run_session())
    # loop1.run_forever()
    loop.run_until_complete(vk.run_session())


def run_threads2(data):
    print(data)
    # print(sys.prefix)
    # print(multiprocessing.current_process())
    workers = []
    for i in data:
        loop = asyncio.new_event_loop()
        # workers.append(Thread(target=run_threads2_1, args=(i, loop)))
        workers.append(VkUserControl(i, loop))
    print(workers)
    for i in workers:
        i.start()
    for i in workers:
        i.join()

def split_list(a_list):
    half = len(a_list) // 2
    return a_list[:half], a_list[half:]

def run_multiproc4():
    data = split_list(tokens)
    print(f'Выгружены данные токенов в количестве {len(tokens)}\n'
          f'Начинаю запуск бота в двухпроцессорном режиме')
    for i in tokens:
        print(i)
    # окго для контроля #todo
    worker = [Process(target=run_threads2, args=(i,)) for i in data]
    for i in worker:


        i.start()
def two_thread_loop():
    import asyncio
    from threading import Thread

    def hello(thread_name):
        print('hello from thread {}!'.format(thread_name))

    event_loop_a = asyncio.new_event_loop()
    event_loop_b = asyncio.new_event_loop()

    def callback_a():
        asyncio.set_event_loop(event_loop_a)
        asyncio.get_event_loop().call_soon(lambda: hello('a'))
        event_loop_a.run_forever()

    def callback_b():
        asyncio.set_event_loop(event_loop_b)
        asyncio.get_event_loop().call_soon(lambda: hello('b'))
        event_loop_b.run_forever()

    thread_a = Thread(target=callback_a, daemon=True)
    thread_b = Thread(target=callback_b, daemon=True)
    thread_a.start()
    thread_b.start()


async def main(token=None):
    if text_settings['accept_interface']:
        await init_eel()
    await upload_all_data_main(statusbar=False)
    # run_threads(TOKENS)  # todo
    vk = VkUserControl(token or tokens[0])
    await vk.run_session()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(vk.run_session())

    # asyncio.run_coroutine_threadsafe(vk.run_session(), loop)
    # loop.run_forever()
    # asyncio.run(vk.run_session())


def main2():
    two_thread_loop()


def main3(loop1):
    # loop1 = asyncio.new_event_loop()
    upload_all_data_main()
    asyncio.set_event_loop(loop1)
    asyncio.get_event_loop()
    vk = VkUserControl(tokens[0], loop=loop1)
    # loop1.create_task(vk.run_session())
    # loop1.run_forever()
    loop1.run_until_complete(vk.run_session())


def main4(loop2):
    # loop2 = asyncio.new_event_loop()
    upload_all_data_main()
    asyncio.set_event_loop(loop2)
    asyncio.get_event_loop()
    vk = VkUserControl(tokens[0], loop=loop2)
    # loop2.create_task(vk.run_session())
    # loop2.run_forever()
    loop2.run_until_complete(vk.run_session())


def many_loops():
    loop1 = asyncio.new_event_loop()
    loop2 = asyncio.new_event_loop()
    thread_a = Thread(target=main3, args=(loop1,))
    thread_b = Thread(target=main4, args=(loop2,))
    thread_a.start()
    thread_b.start()
    thread_a.join()
    thread_b.join()


def start(token):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(token))
    #
    asyncio.run(main(token))


def multi_main():
    # token1 = '9e9a3ac3f141f84ea7ace8d0759465097b32928480d7bf952536b8e334f0f48c85a8f0347564cbdd3a387'
    # token2 = '3a1ef0834325b306e8390699bbd0b781c9fd83b385a1b837df67c77043e6a5f34ff656683cea10157b783'
    for token in tokens:
        # start(token)
        Process(target=start, args=(token,)).start()
    # Process(target=start).start()


if __name__ == '__main__':
    # asyncio.run(main())
    multiprocessing.freeze_support()
    # multi_main()
    start(tokens[0])
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
