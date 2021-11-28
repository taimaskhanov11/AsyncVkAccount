import asyncio
import collections
import multiprocessing
import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

import telebot
from aiovk import API, TokenSession
from aiovk.drivers import HttpDriver
from aiovk.exceptions import VkAuthError
from aiovk.longpoll import UserLongPoll
from colorama import init as colorama_init
from tortoise import Tortoise
from tqdm import trange
from vk_api.longpoll import Event, VkEventType

from core.classes import BaseUser
from core.database import (Account, Input, Message, Users,
                           init_tortoise)
from core.handlers.text_handler import text_handler
from core.handlers.log_handler import log_handler
from core.log_settings import exp_log, not_answer_log
from core.utils import find_most_city
from core.validators import (age_validator, count_friends_validator,
                             mens_validator, photo_validator)
from settings import *

# from typing import (TYPE_CHECKING, Any, AsyncGenerator,   Awaitable,
#                     Generator, Generic, Iterator, List, Optional, Type,
#                     TypeVar, Union)

# todo


# BaseUser = log_handler(BaseUser)


__all__ = [
    'upload_sql_users',
    'ResponseTimeTrack',
    'VkUserControl',
    'upload_all_data_main',
]


users = []
unusers = []
user_list = {}
colorama_init()


async def upload_sql_users():  # todo
    users_all = await Users.all()
    for user in users_all:
        _id = user.user_id
        user_list[_id] = BaseUser(_id, user.state, user.name, user.city)
        if user.blocked:
            unusers.append(_id)
            # print(USER_LIST)
        else:
            users.append(_id)


def create_thread_deco(func):
    # @functools.wraps(func)
    print(func.__name__)

    def run(function, *args):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(function(*args))

    async def wrapper(*args, **kwargs):
        print(args)
        # func = functools.partial(*args, **kwargs)
        Thread(target=run, args=(func, *args)).start()
        text_handler(signs['time'], f'{func.__name__:<36} запущен поток проверки состояния', 'debug',
                     off_interface=True, talk=False, prop=True)
        # await func(*args, **kwargs)

    return wrapper


class ResponseTimeTrack:
    def __init__(self):
        self.start_time = time.monotonic()

    def stop(self, check=False):
        end_time = time.monotonic()
        check_time_end = round(end_time - self.start_time, 6)
        text = f'Время полной проверки {check_time_end}s' if check else f'Время формирования ответа {check_time_end} s'

        text_handler(signs['time'], text, 'debug', color='blue',
                     off_interface=True, prop=True)


# @log_handler
class VkUserControl:
    validators = (photo_validator, age_validator, count_friends_validator, mens_validator)

    def __init__(self, vk_token):
        # super().__init__(*args, **kwargs)

        self.token = vk_token
        # self.session = vk_api.VkApi(token=token, api_version='5.131')
        # self.session = TokenSession(self.token)
        self.loop = asyncio.get_event_loop()
        # self.driver = HttpDriver(loop=loop) if loop else None
        # self.session = TokenSession(self.token, driver=self.driver)
        self.session = TokenSession(self.token)
        self.tg_bot = telebot.TeleBot(settings['telegram_token'])
        self.vk = API(self.session)

        self.longpoll = UserLongPoll(self.vk, mode=1, version=3)
        self.users_block = collections.defaultdict(int)
        self.DEFAULT_EVENT_CLASS = Event
        self.info = None
        self.block_message_count = 20
        self.message_threads = []
        self.state_answer_count = len(conversation_stages) + 4
        self.executor = ThreadPoolExecutor()
        self.table_account = None
        self.signal_end = False
        self.start_status = True
        self.delay_typing = (settings['delay_typing_from'], settings['delay_typing_to'])
        self.acc_delay = settings['delay_between_messages_for_account']



        self.message_queue = asyncio.Queue()

    def send_status_tg(self, text):
        print('отправка')
        self.tg_bot.send_message(settings['user_id'], text)

    async def get_user_info(self, user_id):
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.vk.users.get(user_ids=user_id,
                                      fields='sex, bdate, has_photo, city')
        return res[0]





    async def send_message(self, user_id, text):
        await self.vk.messages.setActivity(user_id=user_id, type='typing')
        await asyncio.sleep(random.randint(*self.delay_typing))

        await self.vk.messages.send(user_id=user_id,
                                    message=text,
                                    random_id=0)


    async def get_friend(self, user_id):
        return await self.vk.friends.search(user_id=user_id, fields="sex, city", count=1000)

    async def add_friend(self, user_id):
        await self.vk.friends.add(user_id=user_id)

    def check_and_add_friend(self, user_id):  # todo
        pass

        # await loop.run_in_executor(self.executor, self.thread_send_message, auth_user, current_answer)

    async def _create_message_thread(self, auth_user, current_answer):  # todo
        task = Thread(target=self.start_send_message, args=(auth_user, current_answer))
        self.message_threads.append(task)
        task.start()

    def start_send_message(self, auth_user, text):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # self.message_loop = loop
        # loop.create_task(self.thread_send_message(auth_user, text, loop))
        # loop.run_forever()

        loop.run_until_complete(self.thread_send_message(auth_user, text, loop))
        # loop.run_until_complete(self.thread_send_message2(auth_user, text))

    async def thread_send_message(self, auth_user, text, loop):
        # async with TokenSession(self.token) as session:
        async with TokenSession(self.token, driver=HttpDriver(loop=loop)) as session:
            # session =
            vk = API(session)
            auth_user.block_template += 1
            # рандомный сон
            delay_response_from, delay_response_to = settings['delay_response_from'], settings['delay_response_to']

            random_sleep_answer = random.randint(delay_response_from, delay_response_to)
            # print(random_sleep_answer)

            await asyncio.sleep(random_sleep_answer)

            # todo Сон для задержки между сообщениями

            # todo доделать last_answer_time
            # while auth_user.last_answer_time > time.time():
            #     # print(f'Жду {settings["delay_between_messages"]} сек')
            #     await asyncio.sleep(settings['delay_between_messages'] + 1)
            # auth_user.last_answer_time = time.time() + settings['delay_between_messages']

            # todo доделать ответы между посленими сообщениями
            await vk.messages.setActivity(user_id=auth_user.user_id, type='typing')
            # await self.vk('messages.set_activity', user_id=user_id, type='typing')#todo

            # рандомный сон
            await asyncio.sleep(random.randint(*self.delay_typing))

            await vk.messages.send(user_id=auth_user.user_id,
                                   message=text,
                                   random_id=0)

        user_list[auth_user.user_id].block_template = 0

    def user_info_view(self, info, count_friend, age, has_photo):
        text_handler(signs['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}", 'warning')
        text_handler(signs['yellow'], f"{count_friend} - Количество друзей", 'warning')
        text_handler(signs['yellow'], f'Возраст - {age}', 'warning')
        text_handler(signs['yellow'], f'Фото {has_photo}', 'warning')

    async def get_self_info(self):
        res = await self.vk.users.get(fields=['photo_max_orig'])
        self.info = res[0]
        table_account = await Account.get_or_create(
            user_id=self.info['id'], defaults={
                'token': self.token,
                'name': self.info['first_name']
            },
        )
        self.table_account = table_account[0]

    def parse_event(self, raw_event):
        return self.DEFAULT_EVENT_CLASS(raw_event)

    async def send_delay_message(self, auth_user, text):
        auth_user.block_template += 1
        # рандомный сон
        delay_response_from, delay_response_to = settings['delay_response_from'], settings['delay_response_to']

        random_sleep_answer = random.randint(delay_response_from, delay_response_to)

        await asyncio.sleep(random_sleep_answer)

        # todo Сон для задержки между сообщениями

        # todo доделать last_answer_time
        # while auth_user.last_answer_time > time.time():
        #     # print(f'Жду {settings["delay_between_messages"]} сек')
        #     await asyncio.sleep(settings['delay_between_messages'] + 1)
        # auth_user.last_answer_time = time.time() + settings['delay_between_messages'] #TODO

        # todo доделать ответы между посленими сообщениями
        # await self.vk('messages.set_activity', user_id=user_id, type='typing')#todo

        # рандомный сон


        await self.message_queue.put((auth_user.user_id, auth_user.name, text))
        # await self.send_message(auth_user.user_id, text) #todo

        # user_list[auth_user.user_id].block_template = 0

    async def create_response(self, text, auth_user, table_user):

        template = await auth_user.act(text, self)  # todo
        if template:

            answer = await Input.find_output(text, auth_user.city)
            if not answer:
                await asyncio.to_thread(
                    not_answer_log.warning, f'{auth_user.user_id} {auth_user.name} --> {text}'
                )

            current_answer = f'{answer} {template}'
            answer = answer or '<ответ не найден>'

            asyncio.create_task(self.send_delay_message(auth_user, current_answer))

        else:
            answer = 'Игнор/Проверка на номер'
            template = 'Игнор/Проверка на номер'
            await asyncio.to_thread(text_handler(signs['red'],
                                                 f"{auth_user.user_id} / {auth_user.name} / Стадия 7 или больше / Игнор / Проверка на номер ",
                                                 'error'))

        await self.save_message(table_user, text, answer, template)

    def block_account_message(self):
        text_handler(signs['red'], 'Ошибка авторизации!!!', 'error')
        text_handler(signs['yellow'], 'Возможно вы ввели неправильный токен или аккаунт ЗАБЛОКИРОВАН!', 'error',
                     color='red')
        text_handler(signs['version'], f'Ваш токен {self.token}',
                     'error', color='red')

    async def update_users(self, user_id, name, mode=True, city=None):  # todo убрать
        table_user = await Users.create(account=self.table_account, user_id=user_id, name=name, city=city)
        user_list[user_id] = BaseUser(user_id, 0, name, city)
        users.append(user_id) if mode else unusers.append(user_id)
        return user_list[user_id], table_user

    # todo проверка состояния
    def create_signals_thread(self, func, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(*args))

    async def check_signals(self, user_id):
        await Tortoise.init(  # todo
            db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
            modules={'models': ['database.apostgresql_tortoise_db']}
        )
        print('проверка норм')
        self.table_account = await Account.get(user_id=user_id)
        while True:
            await asyncio.sleep(5)
            # await self.table_account.connection.
            await self.table_account.refresh_from_db(fields=['start_status'])
            if self.start_status:
                if not self.table_account.start_status:
                    self.start_status = False
            else:
                if self.table_account.start_status:
                    self.start_status = True

    async def check_friend_status(self, user_id, can_access_closed):
        add_status = await self.vk.friends.areFriends(user_ids=user_id)
        add_status = add_status[0]['friend_status']

        await asyncio.to_thread(text_handler, signs['yellow'], f"Статус дружбы {add_status}", 'warning')

        if add_status == 2:
            await asyncio.gather(
                asyncio.to_thread(
                    text_handler, signs['yellow'], f"Добавление в друзья", 'warning'
                ),
                self.add_friend(user_id)
            )
            return True

        if not can_access_closed:
            if add_status == 0:
                self.users_block[user_id] += 1
                if self.users_block[user_id] > 2:
                    return False
                await self.send_message(user_id, random.choice(
                    ai_logic['private']['выход']))

            elif add_status == 1:
                await self.send_message(user_id,
                                        "было бы круто если бы ты принял заявку в друзья &#128522;")
                return False

        return True

    async def check_user_validity(self, user_id, info, name, text) -> bool:
        friend_list = await self.get_friend(user_id)

        m_f_count = [i['sex'] for i in friend_list['items']]
        female = m_f_count.count(1)
        male = m_f_count.count(2)
        age = info.get('bdate')
        has_photo = info['has_photo']
        count_friend = friend_list['count']

        await asyncio.to_thread(self.user_info_view, info, count_friend, age, has_photo)

        valid = await self.all_validators(has_photo, age, count_friend,
                                          (male, female, count_friend), )

        if valid:
            # поиск города
            city = find_most_city(friend_list)
            auth_user, table_user = await self.update_users(user_id, name, city=city)

            await asyncio.to_thread(text_handler, signs['mark'],
                                    f'{user_id} / {name} / Прошел все проверки / Добавлен в users',
                                    'info')

            await self.create_response(text, auth_user, table_user)

            return True
        else:
            await asyncio.gather(self.update_users(user_id, name, False),
                                 asyncio.to_thread(text_handler,
                                                   signs['red'],
                                                   f'{user_id} {name} Проверку не прошел / Добавлен в unusers',
                                                   'error')
                                 )
            return False

    async def save_message(self, table_user, text, answer_question, answer_template):

        await Message.create(
            account=self.table_account,
            user=table_user,
            text=text,
            answer_question=answer_question,
            answer_template=answer_template,
        )

    def blacklist_message(self, auth_user, text):
        text_handler(signs['red'],
                     f'Новое сообщение от {auth_user.name} / Черный список / : {text}',
                     'error')

    async def run(self, event):
        text = event.text.lower()
        user_id = event.user_id

        res_time_track = ResponseTimeTrack()

        if user_id in unusers:
            auth_user = user_list[user_id]
            table_user = await Users.get(user_id=auth_user.user_id)  # todo
            await asyncio.gather(
                self.save_message(table_user, text, 'ЧС', 'ЧС'),  # todo
                asyncio.to_thread(self.blacklist_message, auth_user, text)
            )

        elif user_id in users:
            auth_user = user_list[user_id]
            table_user = await Users.get(user_id=auth_user.user_id)  # todo
            if auth_user.state > self.state_answer_count:
                unusers.append(auth_user.user_id)
                await asyncio.gather(
                    Users.block_user(auth_user.user_id),
                    asyncio.to_thread(self.blacklist_message, auth_user, text)
                )

            elif auth_user.block_template < self.block_message_count:
                await asyncio.gather(
                    self.create_response(text, auth_user, table_user),

                    asyncio.to_thread(text_handler(signs['green'],
                                                   f'Новое сообщение от {auth_user.name} / {user_id} - {text}',
                                                   'info'))  # todo

                )

                res_time_track.stop()

            else:
                await asyncio.gather(
                    asyncio.to_thread(text_handler, signs['yellow'],
                                      f'Новое сообщение от {auth_user.name} /{user_id}/SPAM  - {text}',
                                      'warning'),  # todo
                    self.save_message(table_user, text, 'блок', 'блок')
                )




        else:  # Если нету в базе

            info = await self.get_user_info(user_id)
            # print(info)
            name = info['first_name']

            await asyncio.to_thread(text_handler, signs['yellow'],
                                    f'Новое сообщение от {name} / {user_id} / Нету в базе - {text}',
                                    'warning')
            can_access_closed = info["can_access_closed"]

            friend_status = await self.check_friend_status(user_id, can_access_closed)
            if not friend_status:
                return False

            await self.check_user_validity(user_id, info, name, text)

            res_time_track.stop(check=True)

    async def worker(self):
        print('Обработчик сообщений запущен')
        while True:
            # Вытаскиваем 'рабочий элемент' из очереди.
            user_id, name, text = await self.message_queue.get()
            # print(user_id, text)
            # Задержка на 'sleep_for' секунд.

            await asyncio.gather(
                self.send_message(user_id, text),
                asyncio.to_thread(
                    text_handler, signs['message'],
                    f'Сообщение пользователю {name} c тексом: `{text}`\nОтправлено ⇑',
                    'info', 'blue'
                ),
                asyncio.to_thread(
                    text_handler, signs['queue'],
                    f'Ожидание очереди. Тайминг {self.acc_delay} s',
                    'info', 'cyan'
                ),
                asyncio.sleep(self.acc_delay)
            )

            self.message_queue.task_done()
            user_list[user_id].block_template = 0  # снятие блока после обработки

            # print(self.message_queue)

            # Сообщаем очереди, что 'рабочий элемент' обработан.
            # queue.task_done()

    async def run_session(self):
        # await asyncio.sleep(1)
        print(asyncio.get_event_loop())
        print('Текущий поток', multiprocessing.current_process(), threading.current_thread())  # todo

        try:
            await self.get_self_info()
        except VkAuthError as e:
            print(e)
            await asyncio.gather(
                asyncio.to_thread(self.block_account_message),
                asyncio.to_thread(exp_log.error, e)
            )
            exit()

        # func = lambda x, *args: Thread(target=self.create_signals_thread, args=(x, *args,)).start()
        # func(self.check_signals, self.info['id'])
        # self.message_loop.run()

        asyncio.create_task(self.worker())

        print(self.info['first_name'], self.info['last_name'])
        while True:
            try:
                async for event_a in self.longpoll.iter():
                    # print(event_a)
                    if event_a[0] != 4:
                        continue
                    # print(self.message_queue)
                    event = self.parse_event(event_a)

                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                        self.loop.create_task(self.run(event))

                    if self.signal_end:
                        for task in self.message_threads:
                            task.join()
                        return

            except VkAuthError as e:
                print(e)
                exp_log.error(e)
                await asyncio.gather(asyncio.to_thread(self.block_account_message),
                                     Account.blocking(self.info['id']), return_exceptions=True)
                return

            except Exception as e:
                await asyncio.gather(
                    asyncio.to_thread(text_handler, signs['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error'),
                    asyncio.to_thread(exp_log.exception, e)
                )
                print('ПЕРЕПОДКЛЮЧЕНИЕ...')  # todo

    async def all_validators(self, *args):
        tasks = [asyncio.to_thread(func, arg) for func, arg in zip(self.validators, args)]
        res = await asyncio.gather(*tasks, return_exceptions=True)
        if all(res):
            return True
        return False


def is_bad_proxy(pip):
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': pip})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req = urllib.request.Request('http://www.example.com')  # change the URL to test here
        sock = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        # print('Error code: ', e.code)
        return e.code
    except Exception as detail:
        # print("ERROR:", detail)
        return True
    return False


# @log_handler
async def upload_all_data_main(statusbar=False):
    """Инициализация данных профиля и сохранений в базе"""
    try:

        text_handler(f"VkBot v{bot_version}", '', color='blue')

        await init_tortoise()

        text_handler(signs['magenta'], f'Загруженно токенов {len(tokens)}: ', color='magenta')
        for a, b in enumerate(tokens, 1):
            text_handler(signs['magenta'], f"    {b}", color='magenta')

        delay = f"[{settings['delay_response_from']} - {settings['delay_response_to']}] s"
        text_handler(signs['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{settings['delay_typing_from']} - {settings['delay_typing_to']}] s"
        text_handler(signs['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        # Выгрузка стадий и юзеров
        await upload_sql_users()

        # todo
        text_handler(signs['magenta'], 'Проверка прокси:', color='magenta')
        for proxy in settings['proxy']:
            text_handler(signs['magenta'], '    PROXY {proxy} IS WORKING'.format(proxy=proxy))
        time.sleep(1)

        if statusbar:
            for i in trange(300, colour='green', smoothing=0.1, unit_scale=True):
                time.sleep(0.001)
        # if is_bad_proxy(proxy):
        #     await TextHandler(SIGNS['magenta'], f"    BAD PROXY {proxy}", log_type='error', full=True)
        # else:
        #     await TextHandler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING')
    except Exception as e:
        exp_log.exception(e)


log_handler.init_choice_logging(__name__,
                                *__all__)
