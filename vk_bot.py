import asyncio
import datetime
import functools
import inspect
import multiprocessing
import random
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process
from pprint import pprint
from threading import Thread
# from typing import (TYPE_CHECKING, Any, AsyncGenerator,   Awaitable,
#                     Generator, Generic, Iterator, List, Optional, Type,
#                     TypeVar, Union)

import aiohttp
import pandas as pd
import requests
import telebot
from aiovk import API, TokenSession
from aiovk.drivers import HttpDriver
from aiovk.exceptions import VkAuthError
from aiovk.longpoll import UserLongPoll
from colorama import init as colorama_init
from tortoise import Tortoise
from tqdm import tqdm, trange
from vk_api.longpoll import Event, VkEventType
from vk_api.vk_api import VkApiMethod

# from database.database import Numbers, Users
from database.apostgresql_tortoise_db import (Account, Input, Message, Numbers,
                                              Users, init_tortoise)
from interface.async_main import async_eel, init_eel, window_update
from log_settings import exp_log, not_answer_log, prop_log
from settings import (LOG_COLORS, TALK_DICT_ANSWER_ALL, TALK_TEMPLATE,
                      TEXT_HANDLER_CONTROLLER, TOKENS, VERSION,
                      async_time_track, log, settings, signs, text_handler,
                      time_track, views)
from utilities import find_most_city, search_answer

# todo


users = []
unusers = []
USER_LIST = {}

colorama_init()


@async_time_track
async def upload_sql_users():  # todo
    users_all = await Users.all()
    for user in users_all:
        _id = user.user_id
        USER_LIST[_id] = User(_id, user.state, user.name, user.city)
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
        await text_handler(signs['time'], f'{func.__name__:<36} запущен поток проверки состояния', 'debug',
                           off_interface=True, talk=False, prop=True)
        # await func(*args, **kwargs)

    return wrapper

@log
class ResponseTimeTrack:
    def __init__(self):
        self.start_time = time.monotonic()

    async def stop(self, check=False):
        end_time = time.monotonic()
        check_time_end = round(end_time - self.start_time, 6)
        text = f'Время полной проверки {check_time_end}s' if check else f'Время формирования ответа {check_time_end} s'

        await text_handler(signs['time'], text, 'debug', color='blue',
                           off_interface=True, prop=True)



@log
class User:

    def __init__(self, user_id, state, name, city):
        self.user_id = user_id
        self.state = state
        self.name = name
        self.city = city

        self.len_template = len(TALK_TEMPLATE)
        self.half_template = self.len_template // 2
        self.block_template = 0
        self.last_answer_time = 0

    async def append_to_exel(self, user_id, text, name):  # todo убрать
        time = datetime.datetime.now().replace(microsecond=0)
        excel_data_df = pd.read_excel('username.xlsx')
        data = pd.DataFrame({
            'UserID': [user_id],
            'Name': [name],
            'Url': [f"https://vk.com/id{user_id}"],
            'Number': [text],
            'Date': [time]
        })
        res = excel_data_df.append(data)
        res.to_excel('username.xlsx', index=False)
        # print(res)
        return data

    async def add_state(self):
        self.state += 1
        await Users.add_state(self.user_id)

    async def number_success(self, overlord, text):
        await self.append_to_exel(self.user_id, text, self.name)  # todo
        await Numbers.create(user_id=self.user_id, name=self.name, city=self.city, text=text)
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await window_update(self.user_id, self.name, text, mode='numbers')

        await text_handler(signs['mark'], f'{self.user_id} / {self.name} Номер получен добавление в unusers')
        overlord.send_status_tg(f'бот {overlord.info["first_name"]} {overlord.info["last_name"]}\n'
                                f'Полученные данные:\n'
                                f'name      {self.name}\n'
                                f'id        {self.user_id}\n'
                                f'url       https://vk.com/id{self.user_id}\n'
                                f'number    {text}')

        await overlord.update_users(self.user_id, self.name, mode='number')

    async def act(self, text, overlord):
        await self.add_state()
        if self.state >= self.half_template:
            result = re.findall('\d{4,}', text)
            if result:
                await self.number_success(overlord, text)
                return False

            # print(self.len_template)
            if self.state >= self.len_template + 1:
                return False
            res = random.choice(TALK_TEMPLATE[f"state{self.state}"])
            return res

        else:
            res = random.choice(TALK_TEMPLATE[f"state{self.state}"])
            return res

@log
class MessageLoop:

    def __init__(self, token):
        self.token = token
        # self.loop = asyncio.new_event_loop()
        # self.session = TokenSession(self.token, driver=HttpDriver(loop=self.loop))
        # self.vk = API(self.session)

    def create_message_task_(self, auth_user, text):
        self.loop.create_task(self.create_message(auth_user, text))
        # self.loop.run_forever()
        print('СОЗДАН')

    async def create_message_task(self, auth_user, text):
        await self.queue.put((self.create_message, (auth_user, text,)))

    async def create_message(self, auth_user, text):
        print('WORK')
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

        auth_user.last_answer_time = time.time() + settings['delay_between_messages']

        # todo доделать ответы между посленими сообщениями
        await self.vk.messages.setActivity(user_id=auth_user.user_id, type='typing')
        # await self.vk('messages.set_activity', user_id=user_id, type='typing')#todo

        # рандомный сон
        delay_typing_from, delay_typing_to = settings['delay_typing_from'], settings['delay_typing_to']
        random_sleep_typing = random.randint(delay_typing_from, delay_typing_to)

        await asyncio.sleep(random_sleep_typing)

        await self.vk.messages.send(user_id=auth_user.user_id,
                                    message=text,
                                    random_id=0)

        USER_LIST[auth_user.user_id].block_template = 0

    async def test(self, x):
        await asyncio.sleep(2)
        print('test', x)

    async def main(self):
        self.session = TokenSession(self.token, driver=HttpDriver(loop=self.loop))
        self.vk = API(self.session)
        self.queue = asyncio.Queue()
        await self.queue.put((self.test, (3,)))
        while True:
            print('queue')
            print(self.queue)
            await asyncio.sleep(0)
            func, args = await self.queue.get()
            print(func, args)
            # await self.queue.put((self.test,(3,) ))
            # await func(*args)
            self.loop.create_task(func(*args))
            print('СОЗДАН')
            # await func()

    def create_thread(self):
        print('Текущий поток', multiprocessing.current_process(), threading.current_thread())  # todo
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # loop = asyncio.new_event_loop()
        # self.loop.run_forever()
        self.loop.create_task(self.main())
        self.loop.run_forever()

    def run(self):
        thr = Thread(target=self.create_thread)
        thr.start()
        # thr.join()

@log
class VkUserControl:

    def __init__(self, vk_token, loop=None, ):
        # super().__init__(*args, **kwargs)

        self.token = vk_token
        # self.session = vk_api.VkApi(token=token, api_version='5.131')
        # self.session = TokenSession(self.token)
        self.loop = loop
        self.driver = HttpDriver(loop=loop) if loop else None
        self.session = TokenSession(self.token, driver=self.driver)
        self.tg_bot = telebot.TeleBot(settings['telegram_token'])
        self.vk = API(self.session)

        self.longpoll = UserLongPoll(self.vk, mode=1, version=3)
        self.users_block = {}
        self.validators = (self.photo_validator, self.age_validator, self.count_friends_validator, self.mens_validator,)
        self.DEFAULT_EVENT_CLASS = Event
        self.info = None
        self.block_message_count = 2
        self.message_threads = []
        self.state_answer_count = len(TALK_TEMPLATE) + 4
        self.executor = ThreadPoolExecutor()
        self.table_account = None
        self.signal_end = False
        self.start_status = True
        self.message_loop = MessageLoop(self.token)  # todo

    def send_status_tg(self, text):
        print('отправка')
        self.tg_bot.send_message(settings['user_id'], text)

    async def get_user_info(self, user_id):
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.vk.users.get(user_ids=user_id,
                                      fields='sex, bdate, has_photo, city')
        return res[0]

    async def send_message(self, user, text):
        await self.vk.messages.send(user_id=user,
                                    message=text,
                                    random_id=0)

    async def get_friend(self, user_id):
        try:
            # return self.vk.friends.get(user_id=user_id)
            res = await self.vk.friends.search(user_id=user_id, fields="sex, city", count=1000)
            # print(res)
            return res
        except Exception as e:
            print(f'{e}')
            return False

    async def check_status_friend(self, user_id):
        try:
            res = await self.vk.friends.areFriends(user_ids=user_id)
            # print(res)
            return res[0]['friend_status']
        except Exception as e:
            print(f'{e} Ошибка')
            return 'private'

    async def add_friend(self, user_id):
        await self.vk.friends.add(user_id=user_id)

    def check_and_add_friend(self, user_id):  # todo
        pass

    def _start_send_message_executor(self, auth_user, text):
        loop = asyncio.new_event_loop()
        loop.set_default_executor(self.executor)
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.thread_send_message(auth_user, text, loop))

    async def _create_message_executor(self, auth_user, current_answer):
        # loop = asyncio.get_event_loop()
        # loop.set_default_executor(self.executor)
        # await loop.run_in_executor(self.executor, self._start_send_message_executor, auth_user, current_answer) #todo
        task = Thread(target=self._start_send_message_executor, args=(auth_user, current_answer))
        self.message_threads.append(task)
        task.start()

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

            auth_user.last_answer_time = time.time() + settings['delay_between_messages']

            # todo доделать ответы между посленими сообщениями
            await vk.messages.setActivity(user_id=auth_user.user_id, type='typing')
            # await self.vk('messages.set_activity', user_id=user_id, type='typing')#todo

            # рандомный сон
            delay_typing_from, delay_typing_to = settings['delay_typing_from'], settings['delay_typing_to']
            random_sleep_typing = random.randint(delay_typing_from, delay_typing_to)

            await asyncio.sleep(random_sleep_typing)

            await vk.messages.send(user_id=auth_user.user_id,
                                   message=text,
                                   random_id=0)

        USER_LIST[auth_user.user_id].block_template = 0

    async def initialization_menu(self):
        await async_eel.changeText(f'{self.info["first_name"]} {self.info["last_name"]}', 'text1')()
        photo = self.info.get('photo_max_orig')
        if photo:
            res = requests.get(photo).content
            file = f'{self.info["id"]}.png'
            with open(f'interface/www/media/{file}', 'wb') as ff:
                ff.write(res)
            await text_handler(signs['green'], 'Фото загружено')
            await async_eel.giveAvatar(file)()

    async def user_info_view(self, info, count_friend, age, has_photo):
        await text_handler(signs['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}", 'warning')
        await text_handler(signs['yellow'], f"{count_friend} - Количество друзей", 'warning')
        await text_handler(signs['yellow'], f'Возраст - {age}', 'warning')
        await text_handler(signs['yellow'], f'Фото {has_photo}', 'warning')

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

    def get_api(self):
        """ Возвращает VkApiMethod(self)

            Позволяет обращаться к методам API как к обычным классам.
            Например vk.wall.get(...)
        """

        return VkApiMethod(self)

    async def create_response(self, text, auth_user):

        template = await auth_user.act(text, self)  # todo
        if template:
            answer = await Input.find_output(text, auth_user.city)
            if not answer:
                not_answer_log.warning(f'{auth_user.user_id} {auth_user.name} --> {text}')

            current_answer = f'{answer} {template}'
            answer = answer or '<ответ не найден>'
            # if self.send_message_loop:
            #     print('добавлен в поток')
            #     self.send_message_loop.create_task(self.thread_send_message(auth_user, text, self.send_message_loop))
            # else: #TODO
            # print(self.message_loop.loop)
            # self.message_loop.create_message_task(auth_user, current_answer)  # todo добавлен send message_loop
            # await self.message_loop.create_message_task(auth_user, current_answer)  # todo добавлен send message_loop
            # self.message_loop.loop.create_task(self.message_loop.create_message(auth_user, text))  # todo добавлен send message_loop
            await self._create_message_thread(auth_user, current_answer)  # todo добавлен send message_loop
            # await self._create_message_executor(auth_user, f'{answer} {template}')
        else:
            answer = 'Игнор/Проверка на номер'
            template = 'Игнор/Проверка на номер'
            await text_handler(signs['red'],
                               f"{auth_user.user_id} / {auth_user.name} / Стадия 7 или больше / Игнор / Проверка на номер ",
                               'error')

        table_user = await Users.get(user_id=auth_user.user_id)  # todo
        await Message.create(
            account=self.table_account,
            user=table_user,
            text=text,
            answer_question=answer,
            answer_template=template,
        )

    async def block_account_message(self):
        await text_handler(signs['red'], 'Ошибка авторизации!!!', 'error')
        await text_handler(signs['yellow'], 'Возможно вы ввели неправильный токен или аккаунт ЗАБЛОКИРОВАН!',
                           'error', color='red')
        await text_handler(signs['version'], f'Ваш токен {self.token}',
                           'error', color='red')

    async def update_users(self, user_id, name, mode: str | bool = 'default', city=None):
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await window_update(user_id, name, number='', mode='users' if mode else 'unusers')

        if mode:
            if mode == 'number':
                unusers.append(user_id)
                await Users.change_value(user_id, 'blocked', True)
            else:
                await Users.create(account=self.table_account, user_id=user_id, name=name, city=city)
                USER_LIST[user_id] = User(user_id, 0, name, city)
                users.append(user_id)
                return USER_LIST[user_id]
        else:
            unusers.append(user_id)

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

    async def run_session(self):
        # await asyncio.sleep(1)
        print(asyncio.get_event_loop())
        print('Текущий поток', multiprocessing.current_process(), threading.current_thread())  # todo

        try:
            await self.get_self_info()
        except VkAuthError as e:
            print(e)
            await self.block_account_message()
            exp_log.error(e)
            exit()

        # func = lambda x, *args: Thread(target=self.create_signals_thread, args=(x, *args,)).start()
        # func(self.check_signals, self.info['id'])
        # self.message_loop.run()

        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await self.initialization_menu()
        print(self.info)
        while True:
            try:
                async for event_a in self.longpoll.iter():
                    # print(event_a)
                    if event_a[0] != 4:
                        await asyncio.sleep(0)
                        continue
                    event = self.parse_event(event_a)
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                        text = event.text.lower()
                        user = event.user_id

                        # check_time_start = time.time()
                        res_time_track = ResponseTimeTrack()

                        if self.signal_end:
                            for task in self.message_threads:
                                task.join()
                            return

                        if user in unusers:

                            auth_user = USER_LIST[user]
                            await text_handler(signs['red'],
                                               f'Новое сообщение от {auth_user.name} / Черный список / : {text}',
                                               'error')  # todo
                            table_user = await Users.get(user_id=auth_user.user_id)  # todo
                            await Message.create(
                                account=self.table_account,
                                user=table_user,
                                text=text,
                                answer_question='ПОЛЬЗОВАТЕЛЬ В ЧЕРНОМ СПИСКЕ',
                                answer_template='ПОЛЬЗОВАТЕЛЬ В ЧЕРНОМ СПИСКЕ',
                            )

                        elif user in users:
                            auth_user = USER_LIST[user]
                            if auth_user.state > self.state_answer_count:
                                await text_handler(signs['red'],
                                                   f'Новое сообщение от {user} / Черный список / : {text}',
                                                   'error')  # todo

                                unusers.append(auth_user.user_id)
                                table_user = await Users.get(user_id=auth_user.user_id)
                                table_user.blocked = True
                                await table_user.save()

                            elif auth_user.block_template < self.block_message_count:
                                await text_handler(signs['green'],
                                                   f'Новое сообщение от {auth_user.name} / {user} - {text}',
                                                   'info')  # todo

                                await self.create_response(text, auth_user)

                                await res_time_track.stop()



                        else:  # Если нету в базе
                            info = await self.get_user_info(user)
                            # print(info)
                            name = info['first_name']
                            await text_handler(signs['yellow'],
                                               f'Новое сообщение от {name} / {user} / Нету в базе - {text}',
                                               'warning')

                            closed = info["can_access_closed"]
                            add_status = await self.check_status_friend(user)
                            await text_handler(signs['yellow'], f"Статус дружбы {add_status}", 'warning')

                            if not closed:
                                if add_status == 0:
                                    if user not in self.users_block:
                                        self.users_block[user] = 0

                                    if self.users_block[user] > 1:
                                        continue
                                    await self.send_message(user, random.choice(
                                        TALK_DICT_ANSWER_ALL['private']['выход']))

                                    self.users_block[user] += 1
                                    continue

                                elif add_status == 2:
                                    await text_handler(signs['yellow'], f"Добавление в друзья", 'warning')
                                    await self.add_friend(user)

                                elif add_status == 1:
                                    await self.send_message(user,
                                                            "было бы круто если бы ты принял заявку в друзья &#128522;")
                                    continue

                            if add_status == 2:
                                await text_handler(signs['yellow'], f"Добавление в друзья", 'warning')
                                await self.add_friend(user)

                            friend_list = await self.get_friend(user)
                            # print(friend_list)

                            m_f_count = [i['sex'] for i in friend_list['items']]

                            female = m_f_count.count(1)
                            male = m_f_count.count(2)
                            age = info.get('bdate')
                            has_photo = info['has_photo']
                            count_friend = friend_list['count']

                            await self.user_info_view(info, count_friend, age, has_photo)

                            valid = await self.all_validators(has_photo, age, count_friend,
                                                              (male, female, count_friend))
                            if valid:
                                await text_handler(signs['mark'],
                                                   f'{user} / {name} / Прошел все проверки / Добавлен в users',
                                                   'info')
                                # поиск города
                                city = await find_most_city(friend_list)
                                auth_user = await self.update_users(user, name, city=city)

                                await self.create_response(text, auth_user)

                                await res_time_track.stop(check=True)
                                continue
                            else:
                                # verification_failed(user, name)

                                await text_handler(signs['red'],
                                                   f'{user} {name} Проверку не прошел / Добавлен в unusers',
                                                   'error')
                                await self.update_users(user, name, False)

            except VkAuthError as e:
                print(e)
                exp_log.error(e)
                await self.block_account_message()
                await Account.blocking(self.info['id'])
                return

            except Exception as e:
                # raise
                exp_log.exception(e)
                print('ПЕРЕПОДКЛЮЧЕНИЕ...')  # todo
                await text_handler(signs['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error')

    # def all_validators(self, age, count_friends, friends, male):
    # todo
    async def all_validators(self, *args) -> bool:
        validators = (await func(value) for func, value in zip(self.validators, args))
        async for valid in validators:
            if not valid:
                return False
        return True

    async def photo_validator(self, photo) -> bool:
        validator = views['validators']['photo_validator']

        await text_handler(signs['yellow'], validator['check'], 'warning')

        # todo update
        # match bool(photo):
        #     case True:
        #         await TextHandler(SIGNS['yellow'], validator['success'])
        #         return True
        #     case False:
        #         await TextHandler(SIGNS['red'], validator['failure'], 'error')
        #         return False

        if photo:
            await text_handler(signs['yellow'], validator['success'])
            return True
        else:
            await text_handler(signs['red'], validator['failure'], 'error')
            return False

    async def age_validator(self, age: str | int) -> bool:
        validator = views['validators']['age_validator']

        await text_handler(signs['yellow'], validator['check'], 'warning')
        try:
            if age:
                # print(age)
                age = age[-1:-5:-1]
                age = age[-1::-1]
                # print(age)
                date = 2021 - int(age)
                if date >= 20:
                    await text_handler(signs['green'], validator['success'])
                    return True
                else:
                    await text_handler(signs['red'], validator['failure'], 'error')
                    return False
            else:
                return True  # todo
        except Exception as e:
            exp_log.exception(e)
            return True

    async def count_friends_validator(self, count: int) -> bool:
        validator = views['validators']['count_friends_validator']

        await text_handler(signs['yellow'], validator['check'], 'warning')
        # count = session.method('status.get', {'user_id': user_id})
        if 24 <= count <= 1001:
            await text_handler(signs['green'], validator['success'])
            return True
        else:
            await text_handler(signs['red'], validator['failure'], 'error')
            return False

    async def mens_validator(self, info: tuple) -> bool:
        validator = views['validators']['mens_validator']
        """
        Проверка соотношения м/ж
        if m<=35%:
            :return: False
            :rtype: bool
        else:
            :return: True
            :rtype: bool
        """
        male, female, friends = info
        await text_handler(signs['yellow'], f' девушек - {female}', 'warning', )
        await text_handler(signs['yellow'], f'Количество парней - {male}', 'warning', )
        await text_handler(signs['yellow'], validator['check'], 'warning', )
        res = male / friends * 100
        if round(res) <= 35:
            await text_handler(signs['red'], validator['failure'], 'error')
            return False
        else:
            await text_handler(signs['yellow'], validator['success'].format(res))
            return True


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


async def upload_all_data_main(statusbar=False):
    """Инициализация данных профиля и сохранений в базе"""
    try:
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await async_eel.AddVersion(f"VkBot v{VERSION}")()
        # cprint("VkBotDir 1.6.3.1", 'bright yellow')
        await text_handler(f"VkBot v{VERSION}", '', color='blue')

        await init_tortoise()

        await text_handler(signs['magenta'], f'Загруженно токенов {len(TOKENS)}: ', color='magenta')
        for a, b in enumerate(TOKENS, 1):
            await text_handler(signs['magenta'], f"    {b}", color='magenta')

        delay = f"[{settings['delay_response_from']} - {settings['delay_response_to']}] s"
        await text_handler(signs['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{settings['delay_typing_from']} - {settings['delay_typing_to']}] s"
        await text_handler(signs['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        # Выгрузка стадий и юзеров
        await upload_sql_users()

        # todo
        await text_handler(signs['magenta'], 'Проверка прокси:', color='magenta')
        for proxy in settings['proxy']:
            await text_handler(signs['magenta'], '    PROXY {proxy} IS WORKING'.format(proxy=proxy))
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
