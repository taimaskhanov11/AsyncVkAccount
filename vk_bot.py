import asyncio
import datetime
import inspect
import multiprocessing
import random
import re
import threading
import time
import urllib.error
import urllib.request
from multiprocessing import Process
from pprint import pprint
from threading import Thread

import aiohttp
import pandas as pd
import requests
import telebot
from aiovk import API, TokenSession
from aiovk.drivers import HttpDriver
from aiovk.longpoll import UserLongPoll
from colorama import init as colorama_init
from tqdm import tqdm, trange
from vk_api.longpoll import Event, VkEventType
from vk_api.vk_api import VkApiMethod

# from database.database import Numbers, Users
from database.apostgresql_tortoise_db import Input, Numbers, Users, init_tortoise
from interface.async_main import async_eel, init_eel, window_update
from log_settings import exp_log, prop_log
from settings import (LOG_COLORS, SIGNS, TEXT_HANDLER_CONTROLLER, TOKENS,
                      text_handler, VERSION, async_time_track, settings,
                      time_track, views, TALK_DICT_ANSWER_ALL, TALK_TEMPLATE)
from utilities import find_most_city, search_answer
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Generator,
    Generic,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)
# todo


users = []
unusers = []
USER_LIST = {}

colorama_init()


@async_time_track
async def upload_sql_users():
    users_all = await Users.all()
    for user in users_all:
        _id = user.user_id
        if user.blocked:
            unusers.append(_id)
            # print(USER_LIST)
        else:
            users.append(_id)
            USER_LIST[_id] = User(_id, user.state, user.name, user.city)


@async_time_track
async def update_users(user_id, name, mode='default', city=None):
    if TEXT_HANDLER_CONTROLLER['accept_interface']:
        await window_update(user_id, name, number='', mode='users' if mode else 'unusers')

    if mode:
        if mode == 'number':
            unusers.append(user_id)
            await Users.change_value(user_id, 'blocked', True)
        else:
            await Users.create(user_id=user_id, name=name, city=city, blocked=False)
            USER_LIST[user_id] = User(user_id, 1, name, city)
            users.append(user_id)
            return USER_LIST[user_id]
    else:
        unusers.append(user_id)


class ResponseTimeTrack:
    def __init__(self):
        self.start_time = time.monotonic()

    async def stop(self, check=False):
        end_time = time.monotonic()
        check_time_end = round(end_time - self.start_time, 6)
        text = f'Время полной проверки {check_time_end}s' if check else f'Время формирования ответа {check_time_end} s'

        await text_handler(SIGNS['time'], text, 'debug', color='blue',
                           off_interface=True, prop=True)


class ControlMeta(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        # pprint(attrs)
        for key, val in attrs.items():

            # todo update
            # match inspect.isfunction(val):
            #     case '__init__' | 'act' | 'parse_event' | 'start_send_message' | 'send_status_tg':
            #         pass
            #     case

            if inspect.isfunction(val):

                if key in ('__init__', 'act', 'parse_event', 'start_send_message', 'send_status_tg'):
                    continue
                # print(val)
                if asyncio.iscoroutinefunction(val):
                    prop_log.debug(f'async {val}')
                    attrs[key] = async_time_track(val)
                else:
                    prop_log.debug(f'sync {val}')
                    attrs[key] = time_track(val)
        return super().__new__(mcs, name, bases, attrs, **kwargs)


class User(metaclass=ControlMeta):

    def __init__(self, user_id, state, name, city):
        self.user_id = user_id
        self.state = state
        self.name = name
        self.city = city

        self.len_template = len(TALK_TEMPLATE)
        self.half_template = self.len_template // 2
        self.block_template = 0
        self.last_answer_time = 0

    async def append_to_exel(self, user_id, text, name):
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

    async def act(self, text, overlord):

        if self.half_template <= self.state <= self.len_template + 1:
            result = re.findall('\d{4,}', text)
            if result:
                # DONE
                # self.append_to_exel(self.user_id, text, self.name) #todo
                await Numbers.create(user_id=self.user_id, name=self.name, city=self.city, text=text)
                if TEXT_HANDLER_CONTROLLER['accept_interface']:
                    await window_update(self.user_id, self.name, text, mode='numbers')

                await text_handler(SIGNS['mark'], f'{self.user_id} / {self.name} Номер получен добавление в unusers')
                overlord.send_status_tg(f'бот {overlord.info["first_name"]} {overlord.info["last_name"]}\n'
                                        f'Полученные данные:\n'
                                        f'name      {self.name}\n'
                                        f'id        {self.user_id}\n'
                                        f'url       https://vk.com/id{self.user_id}\n'
                                        f'number    {text}')

                await update_users(self.user_id, self.name, mode='number')
                # todo добавление в unuser после номера
                return False

            if self.state == self.len_template + 1:
                # self.state += 1
                await self.add_state()
                return False
            res = random.choice(TALK_TEMPLATE[f"state{self.state}"])
            # self.state += 1
            await self.add_state()

            return res

        else:
            if self.state >= self.len_template + 2:
                return False
            else:
                res = random.choice(TALK_TEMPLATE[f"state{self.state}"])
                await self.add_state()

                # self.state += 1
                return res


class VkUserControl(metaclass=ControlMeta):

    def __init__(self, vk_token, loop=None, ):
        # super().__init__(*args, **kwargs)

        self.token = vk_token
        # self.session = vk_api.VkApi(token=token, api_version='5.131')
        # self.session = TokenSession(self.token)
        self.loop = loop
        if loop:
            self.session = TokenSession(self.token, driver=HttpDriver(loop=loop))
        else:
            self.session = TokenSession(self.token)
        self.tg_bot = telebot.TeleBot(settings['telegram_token'])
        self.vk = API(self.session)
        # self.longpoll = VkLongPoll(self.session)
        self.longpoll = UserLongPoll(self.vk, mode=1, version=3)
        self.users_block = {}
        self.validators = (self.photo_validator, self.age_validator, self.count_friends_validator, self.mens_validator,)
        self.DEFAULT_EVENT_CLASS = Event
        self.info = None
        self.block_message_count = 2
        self.signal_end = False
        self.message_threads = []

    def run(self):
        # print('Текущий поток', multiprocessing.current_process(), threading.current_thread())#todo
        print(multiprocessing.current_process())
        print(threading.current_thread())
        self.loop.run_until_complete(self.run_session())
        # await self.run_session()

    def send_status_tg(self, text):
        print('отправка')
        self.tg_bot.send_message(settings['user_id'], text)

    async def get_user_info(self, user_id):
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.vk.users.get(user_ids=user_id,
                                      fields='sex, bdate, has_photo, city')
        return res[0]

    async def sen_message(self, user, text):
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

    async def send_activity(self, user_id):
        req = f'https://api.vk.com/method/messages.setActivity?user_id={user_id}&type=typing&access_token={self.token}&v=5.131'
        async with aiohttp.ClientSession() as session:
            await session.get(url=req)
            # async with session.get(url=req) as response:
            #     pass

    def start_send_message(self, auth_user, text):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # print(asyncio.get_event_loop())

        # loop = asyncio.get_event_loop()
        # print(loop)
        loop.run_until_complete(self.thread_send_message(auth_user, text, loop))

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

            # Сон для задержки между сообщениями

            # todo доделать last_answer_time
            # while auth_user.last_answer_time > time.time():
            #     # print(f'Жду {settings["delay_between_messages"]} сек')
            #     await asyncio.sleep(settings['delay_between_messages'] + 1)

            auth_user.last_answer_time = time.time() + settings['delay_between_messages']

            # todo
            # now = time.time()
            await vk.messages.setActivity(user_id=auth_user.user_id, type='typing')
            # print(time.time() - now)
            # await self.vk('messages.set_activity', user_id=user_id, type='typing')#todo
            # now = time.time()
            # await self.send_activity(user_id)
            # print(time.time() - now)
            # print('asd')
            # print(res)
            # answ = requests.get(req)
            # print(answ)
            # рандомный сон
            delay_typing_from, delay_typing_to = settings['delay_typing_from'], settings['delay_typing_to']
            random_sleep_typing = random.randint(delay_typing_from, delay_typing_to)

            await asyncio.sleep(random_sleep_typing)

            # await self.sen_message(user_id, text)

            await vk.messages.send(user_id=auth_user.user_id,
                                   message=text,
                                   random_id=0)
            # loop.close()
        # await self.sen_message(user_id, text)  # отправка ответа

        # self.session.method('messages.send', {'user_id': user_id,
        #                                       'message': text,
        #                                       'random_id': 0, })

        USER_LIST[auth_user.user_id].block_template = 0

    async def initialization_menu(self):
        await async_eel.changeText(f'{self.info["first_name"]} {self.info["last_name"]}', 'text1')()
        photo = self.info.get('photo_max_orig')
        if photo:
            res = requests.get(photo).content
            file = f'{self.info["id"]}.png'
            with open(f'interface/www/media/{file}', 'wb') as ff:
                ff.write(res)
            await text_handler(SIGNS['green'], 'Фото загружено')
            await async_eel.giveAvatar(file)()

    async def user_info_view(self, info, friend_list, age, has_photo):
        await text_handler(SIGNS['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}",
                           'warning')
        await text_handler(SIGNS['yellow'], f"{friend_list['count']} - Количество друзей", 'warning')
        await text_handler(SIGNS['yellow'], f'Возраст - {age}', 'warning')
        await text_handler(SIGNS['yellow'], f'Фото {has_photo}', 'warning')

    async def get_self_info(self):
        res = await self.vk.users.get(fields=['photo_max_orig'])
        self.info = res[0]

    def parse_event(self, raw_event):
        return self.DEFAULT_EVENT_CLASS(raw_event)

    def get_api(self):
        """ Возвращает VkApiMethod(self)

            Позволяет обращаться к методам API как к обычным классам.
            Например vk.wall.get(...)
        """

        return VkApiMethod(self)

    async def run_session(self):
        # await asyncio.sleep(1)
        print(threading.current_thread())
        print(self.loop)
        print(asyncio.get_event_loop())
        # print(asyncio.new_event_loop())
        # print(self.parse_event.__name__, 'parse_event')
        # print(self.get_self_info.__name__,  'get_self_info')
        # await init_tortoise()
        # await Tortoise.init(
        #     db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        #     modules={'models': ['database.apostgresql_tortoise_db']}
        # )
        await self.get_self_info()
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await self.initialization_menu()

        while True:
            try:
                async for event_a in self.longpoll.iter():
                    # print(event_a)
                    if event_a[0] != 4:
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
                            await text_handler(SIGNS['red'], f'Новое сообщение от {user} / Черный список / : {text}',
                                               'error')  # todo
                            continue

                        elif user in users:
                            auth_user = USER_LIST[user]
                            if auth_user.block_template < self.block_message_count:
                                name = auth_user.name
                                city = auth_user.city

                                await text_handler(SIGNS['green'], f'Новое сообщение от {name} / {user} - {text}',
                                                   'info')  # todo

                                # answer = await search_answer(text, city) #todo
                                answer = await Input.find_output(text, city)
                                template = await auth_user.act(text, self)  # todo

                                # Сохранение состояния в файл
                                if template:
                                    # await self.thread_send_message(user, f"{answer} {template}")
                                    # loop = asyncio.new_event_loop()
                                    # loop = asyncio.get_event_loop()
                                    # executor = ThreadPoolExecutor(5)
                                    # loop.set_default_executor(executor)
                                    task = Thread(target=self.start_send_message,
                                                  args=(auth_user, f"{answer} {template}"))
                                    self.message_threads.append(task)
                                    task.start()

                                else:
                                    await text_handler(SIGNS['red'], f"{user} / {name} / Стадия 7 или больше / Игнор",
                                                       'error')

                                await res_time_track.stop()

                                # check_time_end = round(time.time() - check_time_start, 6)
                                # await TextHandler(SIGNS['time'], f'Время формирования ответа {check_time_end} s',
                                #                   'debug',
                                #                   # todo сделать функцией
                                #                   off_interface=True, prop=True)

                        else:  # Если нету в базе
                            info = await self.get_user_info(user)
                            # print(info)
                            name = info['first_name']
                            await text_handler(SIGNS['yellow'],
                                               f'Новое сообщение от {name} / {user} / Нету в базе - {text}',
                                               'warning')

                            closed = info["can_access_closed"]
                            add_status = await self.check_status_friend(user)
                            await text_handler(SIGNS['yellow'], f"Статус дружбы {add_status}", 'warning')

                            if not closed:
                                if add_status == 0:
                                    if user not in self.users_block:
                                        self.users_block[user] = 0

                                    if self.users_block[user] > 1:
                                        continue
                                    await self.sen_message(user, random.choice(
                                        TALK_DICT_ANSWER_ALL['private']['выход']))

                                    self.users_block[user] += 1
                                    continue

                                elif add_status == 2:
                                    await text_handler(SIGNS['yellow'], f"Добавление в друзья", 'warning')
                                    await self.add_friend(user)

                                elif add_status == 1:
                                    await self.sen_message(user,
                                                           "было бы круто если бы ты принял заявку в друзья &#128522;")
                                    continue

                            if add_status == 2:
                                await text_handler(SIGNS['yellow'], f"Добавление в друзья", 'warning')
                                await self.add_friend(user)

                            friend_list = await self.get_friend(user)
                            # print(friend_list)

                            m_f_count = [i['sex'] for i in friend_list['items']]

                            female = m_f_count.count(1)
                            male = m_f_count.count(2)
                            age = info.get('bdate')
                            has_photo = info['has_photo']

                            await self.user_info_view(info, friend_list, age, has_photo)

                            count_friend = friend_list['count']
                            valid = await self.all_validators(has_photo, age, count_friend,
                                                              (male, female, count_friend))
                            # if self.age_validator(age) and self.count_friends_validator(count_friend) and has_photo:
                            if valid:
                                # todo выбрать между много проц поточ и одним
                                await text_handler(SIGNS['mark'],
                                                   f'{user} / {name} / Прошел все проверки / Добавлен в users',
                                                   'info')
                                # поиск города
                                city = await find_most_city(friend_list)
                                auth_user = await update_users(user, name, city=city)

                                template = await auth_user.act(text, self)
                                # answer = await search_answer(text, city)
                                answer =  await Input.find_output(text, city)

                                current_answer = f"{answer} {template}" if (
                                        answer or template) else await search_answer('привет', friend_list)

                                # todo update current_answer
                                # match answer, template:
                                #     case str(answer)|str(template):
                                #         print()

                                # todo
                                # await self.sen_message(user, current_answer)

                                await res_time_track.stop(check=True)

                                # check_time_end = round(time.time() - check_time_start, 6)
                                # await TextHandler(SIGNS['time'], f'Время полной проверки {check_time_end} s', 'debug',
                                #                   off_interface=True, prop=True)

                                # loop = asyncio.new_event_loop()
                                # loop = asyncio.get_event_loop()
                                # executor = ThreadPoolExecutor(5)
                                # loop.set_default_executor(executor)

                                task = Thread(target=self.start_send_message,
                                              args=(auth_user, f"{current_answer}"))
                                self.message_threads.append(task)
                                task.start()
                                continue

                            # verification_failed(user, name)

                            await text_handler(SIGNS['red'], f'{user} {name} Проверку не прошел / Добавлен в unusers',
                                               'error')
                            await update_users(user, name, False)

            except Exception as e:
                # raise
                exp_log.exception(e)
                print('ПЕРЕПОДКЛЮЧЕНИЕ...')  # todo
                await text_handler(SIGNS['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error')

    # def all_validators(self, age, count_friends, friends, male):
    # todo
    async def all_validators(self, *args) -> bool:
        validators = (await func(value) for func, value in zip(self.validators, args))
        async for valid in validators:
            if not valid:
                return False
        return True

    # async def all_validators(self, *args):
    #        validators = (await func(value) for func, value in zip(self.validators, args))
    #        async for valid in validators:
    #            if not valid:
    #                return False
    #        return True

    async def photo_validator(self, photo) -> bool:
        validator = views['validators']['photo_validator']

        await text_handler(SIGNS['yellow'], validator['check'], 'warning')

        # todo update
        # match bool(photo):
        #     case True:
        #         await TextHandler(SIGNS['yellow'], validator['success'])
        #         return True
        #     case False:
        #         await TextHandler(SIGNS['red'], validator['failure'], 'error')
        #         return False

        if photo:
            await text_handler(SIGNS['yellow'], validator['success'])
            return True
        else:
            await text_handler(SIGNS['red'], validator['failure'], 'error')
            return False

    async def age_validator(self, age: str | int) -> bool:
        validator = views['validators']['age_validator']

        await text_handler(SIGNS['yellow'], validator['check'], 'warning')
        try:
            if age:
                # print(age)
                age = age[-1:-5:-1]
                age = age[-1::-1]
                # print(age)
                date = 2021 - int(age)
                if date >= 20:
                    await text_handler(SIGNS['green'], validator['success'])
                    return True
                else:
                    await text_handler(SIGNS['red'], validator['failure'], 'error')
                    return False
            else:
                return True  # todo
        except Exception as e:
            exp_log.exception(e)
            return True

    async def count_friends_validator(self, count: int) -> bool:
        validator = views['validators']['count_friends_validator']

        await text_handler(SIGNS['yellow'], validator['check'], 'warning')
        # count = session.method('status.get', {'user_id': user_id})
        if 24 <= count <= 1001:
            await text_handler(SIGNS['green'], validator['success'])
            return True
        else:
            await text_handler(SIGNS['red'], validator['failure'], 'error')
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
        await text_handler(SIGNS['yellow'], f' девушек - {female}', 'warning', )
        await text_handler(SIGNS['yellow'], f'Количество парней - {male}', 'warning', )
        await text_handler(SIGNS['yellow'], validator['check'], 'warning', )
        res = male / friends * 100
        if round(res) <= 35:
            await text_handler(SIGNS['red'], validator['failure'], 'error')
            return False
        else:
            await text_handler(SIGNS['yellow'], validator['success'].format(res))
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


red_point = LOG_COLORS['error'][1]
green_point = LOG_COLORS['info'][1]
yellow_point = LOG_COLORS['warning'][1]


# sign #todo


async def upload_all_data_main(statusbar=True):
    """Инициализация данных профиля и сохранений в базе"""
    try:
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await async_eel.AddVersion(f"VkBot v{VERSION}")()
        # cprint("VkBotDir 1.6.3.1", 'bright yellow')
        await text_handler(f"VkBot v{VERSION}", '', color='blue')

        await init_tortoise()

        await text_handler(SIGNS['magenta'], f'Загруженно токенов {len(TOKENS)}: ', color='magenta')
        for a, b in enumerate(TOKENS, 1):
            await text_handler(SIGNS['magenta'], f"    {b}", color='magenta')

        delay = f"[{settings['delay_response_from']} - {settings['delay_response_to']}] s"
        await text_handler(SIGNS['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{settings['delay_typing_from']} - {settings['delay_typing_to']}] s"
        await text_handler(SIGNS['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        answer2 = f"Данные для разговора загружены"
        await text_handler(SIGNS['mark'], answer2)

        answer1 = 'template.json'
        await text_handler(SIGNS['mark'], f'Файл {answer1} для шаблонов загружен')

        # Выгрузка стадий и юзеров
        await upload_sql_users()

        # todo
        answer2 = 'userstate.json'
        await text_handler(SIGNS['mark'], f'Файл {answer2} для этапов ИИ загружен')
        await text_handler(SIGNS['magenta'], 'Проверка прокси:', color='magenta')
        for proxy in settings['proxy']:
            await text_handler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING'.format(proxy=proxy))
        time.sleep(1)

        if statusbar:
            for i in trange(300, colour='green', smoothing=0.1,unit_scale=True):
                time.sleep(0.001)

        # with tqdm(total=100, colour='green') as pbar:
        #     for i in range(100):
        #         time.sleep(0.1)
        #         pbar.update(0.1)

        # if is_bad_proxy(proxy):
        #     await TextHandler(SIGNS['magenta'], f"    BAD PROXY {proxy}", log_type='error', full=True)
        # else:
        #     await TextHandler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING')
    except Exception as e:
        exp_log.exception(e)