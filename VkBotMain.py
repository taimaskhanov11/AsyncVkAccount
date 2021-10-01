from settings import VERSION, LOG_COLORS, TEXT_HANDLER_CONTROLLER, SIGNS, TextHandler, time_track, async_time_track

if TEXT_HANDLER_CONTROLLER['accept_interface']:
    from interface.async_main import interface, async_eel, window_update, init_eel
import threading
from pprint import pprint

from aiovk import TokenSession, API
from aiovk.drivers import HttpDriver
from aiovk.longpoll import UserLongPoll
from vk_api.vk_api import VkApiMethod

from database.database import Users, Numbers

import asyncio
import datetime
import json
import multiprocessing
import random
import re
from collections import Counter

import aiohttp
import pandas as pd
from multiprocessing import Process
from threading import Thread
import requests
import vk_api
import time

import urllib.request
import urllib.error

from more_termcolor import colored
from vk_api.longpoll import VkLongPoll, VkEventType, Event

from logs.log_settings import exp_log, talk_log, prop_log

from open_data import read_json, read_template, read_userstate, read_config
from colorama import init

init()

# log = logging.getLogger('VkBot_info')
# logging.root = logging.getLogger('main')

users = []
unusers = []

TALK_DICT_ANSWER_ALL = {}
TOKENS = []
TALK_TEMPLATE = {}
USER_STATE = {}
config = {}
USER_LIST = {}


@async_time_track
async def upload_sql_users():
    # global USER_LIST
    for user in Users.select():
        _id = user.user_id
        if user.type:
            users.append(_id)
            USER_LIST[_id] = User(_id, user.state, user.name, user.city)
            # print(USER_LIST)
        else:
            unusers.append(_id)


@async_time_track  # legacy
def upload_users():
    with open('users.txt', 'r') as ff:
        for i in ff:
            users.append(int(i.strip()))
    with open('unusers.txt', 'r') as ff:
        for i in ff:
            unusers.append(int(i.strip()))


@async_time_track
async def update_users(user_id, name, mode=True, city=None):
    if TEXT_HANDLER_CONTROLLER['accept_interface']:
        # mode =
        await window_update(user_id, name, number='', mode='users' if mode else 'unusers')
    # print(mode)

    if mode:
        if mode == 'number':
            unusers.append(user_id)
            await Users.change_value(user_id, 'type', False)
        else:
            await Users.create_user(user_id, name, city, 1)
            USER_LIST[user_id] = User(user_id, 1, name, city)
            users.append(user_id)
            return USER_LIST[user_id]
    else:
        unusers.append(user_id)


class User:

    def __init__(self, user_id, state, name, city):
        self.user_id = user_id
        self.state = state
        self.name = name
        self.city = city

        self.len_template = len(TALK_TEMPLATE)
        self.half_template = self.len_template // 2
        self.block_template = 0

    @async_time_track
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

    @async_time_track
    async def add_state(self):
        self.state += 1
        await Users.add_state(self.user_id)

    @async_time_track
    async def act(self, text):
        # print(TALK_TEMPLATE)

        if self.half_template <= self.state <= self.len_template + 1:
            result = re.findall('\d{4,}', text)
            if result:
                # self.append_to_exel(self.user_id, text, self.name) #todo
                await Numbers.create_user(self.user_id, self.name, self.city, text)
                if TEXT_HANDLER_CONTROLLER['accept_interface']:
                    await window_update(self.user_id, self.name, text, mode='numbers')
                await TextHandler(SIGNS['mark'], f'{self.user_id} / {self.name} Номер получен добавление в unusers')

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


class VkUserControl(Thread):

    def __init__(self, token, loop=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.token = token
        # self.session = vk_api.VkApi(token=token, api_version='5.131')
        # self.session = TokenSession(self.token)
        self.loop = loop
        if loop:
            self.session = TokenSession(self.token, driver=HttpDriver(loop=loop))
        else:
            self.session = TokenSession(self.token)
        self.vk = API(self.session)
        # self.longpoll = VkLongPoll(self.session)
        self.longpoll = UserLongPoll(self.vk, mode=1, version=3)
        self.users_block = {}
        # self.info = self.vk.users.get(fields=['photo_max_orig'])[0]
        # print(self.info) # фото валидатор
        # self.validators = (lambda x: x, self.age_validator, self.count_friends_validator, self.mens_validator,)
        self.validators = (self.photo_validator, self.age_validator, self.count_friends_validator, self.mens_validator,)
        self.DEFAULT_EVENT_CLASS = Event

    def run(self):
        # print('Текущий поток', multiprocessing.current_process(), threading.current_thread())#todo
        # asyncio.set_event_loop(self.loop)
        # loop = asyncio.get_event_loop()
        # asyncio.set_event_loop(self.loop)
        # self.loop = asyncio.get_event_loop()
        # print(;'')
        print(multiprocessing.current_process())
        print(threading.current_thread())
        self.loop.run_until_complete(self.run_session())
        # await self.run_session()

    @async_time_track
    async def get_user_info(self, user_id):
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.vk.users.get(user_ids=user_id,
                                      fields='sex, bdate, has_photo, city')
        # res = await self.vk.users.get(user_ids=user_id, fields='is_closed')
        # res = await self.vk('users.get', user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])

        print(res)
        return res[0]

    @async_time_track
    async def get_user_info2(self, user_id):
        res = self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        # res = await self.vk.users.get(user_ids=user_id, fields='bdate')
        # res = await self.vk('users.get', user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])

        print(res)
        return res[0]

    @async_time_track
    async def sen_message(self, user, text):
        await self.vk.messages.send(user_id=user,
                                    message=text,
                                    random_id=0)

    async def async_get_info(self, session, url):
        async with session.get(url=url) as response:
            res = await response.json()
            answer = res['response'][0]
            print(answer)
            return answer

    @async_time_track
    async def async_get_user_info2(self, user_id):
        fields = ['bdate', 'sex', 'has_photo', 'city']
        fields = ''.join([f'fields={field}&' for field in fields])
        url = f'https://api.vk.com/method/users.get?user_ids={user_id}&fields=bdate?sex&access_token=b78e0ae0dc9ff9434b9d7dd073da692e9d39e4de158da2d50cf7d3d88e59e7085815dd5f3ce24ba6d8ea7&v=5.131'

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as response:
                res = await response.json()
                print(res)

    @async_time_track
    async def async_get_user_info(self, user_id):

        fields = ['bdate', 'sex', 'has_photo', 'city']
        # fields = ['bdate', 'sex', 'has_photo']
        # fields = ''.join([f'fields={field}&' for field in fields])
        print(fields)
        # url = f'https://api.vk.com/method/users.get?user_ids={user_id}&fields=bdate&fields=sex&access_token=b78e0ae0dc9ff9434b9d7dd073da692e9d39e4de158da2d50cf7d3d88e59e7085815dd5f3ce24ba6d8ea7&v=5.131'
        # url = f'https://api.vk.com/method/users.get?user_ids={user_id}&{fields}access_token={self.token}&v=5.131'
        urls = []
        for field in fields:
            url = f'https://api.vk.com/method/users.get?user_ids={user_id}&fields={field}&access_token={self.token}&v=5.131'
            urls.append(url)

        async with aiohttp.ClientSession() as session:
            # url = f'https://api.vk.com/method/users.get?user_ids={user_id}&fields={field}&access_token={self.token}&v=5.131'
            tasks = []
            for url in urls:
                task = asyncio.create_task(self.async_get_info(session, url))
                tasks.append(task)
            res = await asyncio.gather(*tasks)
            pprint(res)
            return res
            # return answer
            # exit()

    async def get_page_data(self, session, user_id):
        try:
            url = 'https://api.vk.com/method/users.get?user_ids=222256657&fields=bdate&fields=sex&access_token=b78e0ae0dc9ff9434b9d7dd073da692e9d39e4de158da2d50cf7d3d88e59e7085815dd5f3ce24ba6d8ea7&v=5.131'
            # async with session.get(url=f'https://api.vk.com/method/users.get?user_ids={user_id}'
            #                            f'&fields=bdate&fields=sex&access_token={self.token}&v=5.131') as response:
            async with session.get(url=url) as response:

                res = await response.json()
                if res.json()['response'][0]['sex'] == 2:
                    print(res)
                    self.answer = True
                    return True
                else:
                    return False
        except Exception as e:
            print(e)
            raise
            pass

    async def async_thread_url_pars_friend(self, ids):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for user_id in ids:
                task = asyncio.create_task(self.get_page_data(session, user_id))
                tasks.append(task)

            res = await asyncio.gather(*tasks)
            print(len(res))  # todo
            print(res.count(True))
            return len(res), res.count(True)

    def thread_url_pars_friend(self, ids):
        res = []
        worker = [RequestSex(user_id=i, token=self.token) for i in ids]
        for i in worker:
            i.start()
            time.sleep(0.05)
        for i in worker:
            i.join()
        for i in worker:
            res.append(i.answer)

        return (len(res), res.count(True))

    @async_time_track
    async def get_friend(self, user_id):
        try:
            # return self.vk.friends.get(user_id=user_id)
            res = await self.vk.friends.search(user_id=user_id, fields="sex, city", count=1000)
            print(res)
            return res
        except Exception as e:
            print(f'{e}')
            return False

    def write_in_file(self, user, text, answer):
        with open(f'chat_files/{user}.txt', 'a', encoding='utf8') as ff:
            ff.write(
                f'Сообщение от пользователя {user} : {text}\n     Ответ : {answer} |Время {datetime.datetime.now().replace(microsecond=0)}\n\n')

    async def check_status_friend(self, user_id):
        try:
            res = await self.vk.friends.areFriends(user_ids=user_id)
            # print(res)
            return res[0]['friend_status']
        except Exception as e:
            print(f'{e} Ошибка')
            return 'private'

    @async_time_track
    async def add_friend(self, user_id):
        await self.vk.friends.add(user_id=user_id)

    def check_and_add_friend(self, user_id):  # todo
        pass

    @staticmethod
    @async_time_track
    def write_userstate(user, name, city):  # legacy
        # now = time.time()
        state = USER_LIST[user].state
        USER_STATE[str(user)] = {'state': state,
                                 'name': name,
                                 'city': city}

        with open('userstate.json', 'w', encoding='utf8') as ff:
            json.dump(USER_STATE, ff, indent=4, ensure_ascii=False)
        # end = round(time.time() - now, 6)
        # await TextHandler(SIGNS['time'], f'Время записи {end} s', 'debug',
        #             off_interface=True)

    async def send_activity(self, user_id):
        req = f'https://api.vk.com/method/messages.setActivity?user_id={user_id}&type=typing&access_token={self.token}&v=5.131'
        async with aiohttp.ClientSession() as session:
            await session.get(url=req)
            # async with session.get(url=req) as response:
            #     pass

    def start_send_message(self, user_id, text, loop):
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(self.thread_send_message(user_id, text, loop))

    @async_time_track
    async def thread_send_message(self, user_id, text, loop):
        async with TokenSession(self.token, driver=HttpDriver(loop=loop)) as session:
            # session =
            vk = API(session)
            USER_LIST[user_id].block_template += 1
            # рандомный сон
            delay_response_from, delay_response_to = config['delay_response_from'], config['delay_response_to']

            random_sleep_answer = random.randint(delay_response_from, delay_response_to)
            # print(random_sleep_answer)

            await asyncio.sleep(random_sleep_answer)

            # todo
            # now = time.time()
            await vk.messages.setActivity(user_id=user_id, type='typing')
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
            delay_typing_from, delay_typing_to = config['delay_typing_from'], config['delay_typing_to']
            random_sleep_typing = random.randint(delay_typing_from, delay_typing_to)

            await asyncio.sleep(random_sleep_typing)

            await vk.messages.send(user_id=user_id,
                                   message=text,
                                   random_id=0)
        # await self.sen_message(user_id, text)  # отправка ответа

        # self.session.method('messages.send', {'user_id': user_id,
        #                                       'message': text,
        #                                       'random_id': 0, })

        USER_LIST[user_id].block_template = 0

    @staticmethod
    @async_time_track
    async def find_most_city(friend_list):
        friends_city = [i['city']['title'] for i in friend_list['items'] if
                        i.get('city')]
        c_friends_city = Counter(friends_city)
        city = max(c_friends_city.items(), key=lambda x: x[1])[0]
        return city

    @async_time_track
    async def initialization_menu(self):
        await async_eel.changeText(f'{self.info["first_name"]} {self.info["last_name"]}', 'text1')()
        photo = self.info.get('photo_max_orig')
        if photo:
            res = requests.get(photo).content
            file = f'{self.info["id"]}.png'
            with open(f'interface/www/media/{file}', 'wb') as ff:
                ff.write(res)
            await TextHandler(SIGNS['green'], 'Фото загружено')
            await async_eel.giveAvatar(file)()

    @staticmethod
    @async_time_track
    async def user_info_view(info, friend_list, age, has_photo):
        await TextHandler(SIGNS['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}",
                          'warning')
        await TextHandler(SIGNS['yellow'], f"{friend_list['count']} - Количество друзей", 'warning')
        await TextHandler(SIGNS['yellow'], f'Возраст - {age}', 'warning')
        await TextHandler(SIGNS['yellow'], f'Фото {has_photo}', 'warning')

    @async_time_track
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

    @async_time_track
    async def run_session(self):
        # await asyncio.sleep(1)
        print(threading.currentThread())
        print(self.loop)
        await self.get_self_info()
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await self.initialization_menu()

        while True:
            try:
                async for event_a in self.longpoll.iter():
                    # print(event_a['type'])
                    if event_a[0] != 4:
                        continue
                    event = self.parse_event(event_a)
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                        text = event.text.lower()
                        user = event.user_id

                        check_time_start = time.time()
                        if text == 'endthisnow':
                            return
                        if user in unusers:

                            await TextHandler(SIGNS['red'], f'Новое сообщение от {user} / Черный список / : {text}',
                                              'error')  # todo

                            continue

                        elif user in users:
                            auth_user = USER_LIST[user]
                            if auth_user.block_template < 2:
                                name = auth_user.name
                                city = auth_user.city

                                await TextHandler(SIGNS['green'], f'Новое сообщение от {name} / {user} - {text}',
                                                  'info')  # todo

                                answer = await search_answer(text, city)
                                template = await auth_user.act(text)  # todo

                                # Сохранение состояния в файл
                                if template:
                                    # await self.thread_send_message(user, f"{answer} {template}")
                                    loop = asyncio.new_event_loop()

                                    Thread(target=self.start_send_message,
                                           args=(user, f"{answer} {template}", loop)).start()

                                else:
                                    await TextHandler(SIGNS['red'], f"{user} / {name} / Стадия 7 или больше / Игнор",
                                                      'error')
                                check_time_end = round(time.time() - check_time_start, 6)
                                await TextHandler(SIGNS['time'], f'Время формирования ответа {check_time_end} s',
                                                  'debug',
                                                  # todo сделать функцией
                                                  off_interface=True, prop=True)

                        else:  # Если нету в базе

                            # info = self.get_user_info(user)
                            info = await self.get_user_info(user)
                            # info = await self.async_get_user_info2(user)
                            # info = await self.async_get_user_info(user)

                            # print(info)
                            name = info['first_name']

                            await TextHandler(SIGNS['yellow'],
                                              f'Новое сообщение от {name} / {user} / Нету в базе - {text}',
                                              'warning')

                            closed = info["can_access_closed"]
                            # closed = 1
                            add_status = await self.check_status_friend(user)

                            await TextHandler(SIGNS['yellow'], f"Статус дружбы {add_status}", 'warning')

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
                                    await TextHandler(SIGNS['yellow'], f"Добавление в друзья", 'warning')
                                    await self.add_friend(user)

                                elif add_status == 1:
                                    await self.sen_message(user,
                                                           "было бы круто если бы ты принял заявку в друзья &#128522;")
                                    continue

                            if add_status == 2:
                                await TextHandler(SIGNS['yellow'], f"Добавление в друзья", 'warning')
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
                                await TextHandler(SIGNS['mark'],
                                                  f'{user} / {name} / Прошел все проверки / Добавлен в users',
                                                  'info')
                                # поиск города
                                city = await self.find_most_city(friend_list)

                                auth_user = await update_users(user, name, city=city)
                                template = await auth_user.act(text)

                                answer = await search_answer(text, city)
                                current_answer = f"{answer} {template}" if (answer or template) else \
                                    await search_answer('привет', friend_list)

                                await self.sen_message(user, current_answer)

                                check_time_end = round(time.time() - check_time_start, 6)
                                await TextHandler(SIGNS['time'], f'Время полной проверки {check_time_end} s', 'debug',
                                                  off_interface=True, prop=True)
                                continue

                            # verification_failed(user, name)
                            await TextHandler(SIGNS['red'], f'{user} {name} Проверку не прошел / Добавлен в unusers',
                                              'error')
                            await update_users(user, name, False)

            except Exception as e:
                # raise
                exp_log.exception(e)
                print('ПЕРЕПОДКЛЮЧЕНИЕ...')  # todo
                await TextHandler(SIGNS['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error')

    # def all_validators(self, age, count_friends, friends, male):
    @async_time_track
    async def all_validators(self, *args):
        validators = (await func(value) for func, value in zip(self.validators, args))
        async for valid in validators:
            if not valid:
                return False
        return True

    @staticmethod
    @async_time_track
    async def photo_validator(photo):
        await TextHandler(SIGNS['yellow'], f'Проверка на фото', 'warning')
        if photo:
            await TextHandler(SIGNS['yellow'], f'Проверку на фото прошел', 'warning')
            return True
        else:
            await TextHandler(SIGNS['red'], f'Фото отсутствует', 'error')
            return False

    @staticmethod
    @async_time_track
    async def age_validator(age):
        await TextHandler(SIGNS['yellow'], f'Проверка на возраст', 'warning')
        try:
            if age:
                # print(age)
                age = age[-1:-5:-1]
                age = age[-1::-1]
                # print(age)
                date = 2021 - int(age)
                if date >= 20:
                    await TextHandler(SIGNS['green'], 'Возраст соответствует')
                    return True
                else:
                    await TextHandler(SIGNS['red'], 'Не соответствует возраст', 'error')
                    return False
            else:
                return True  # todo
        except Exception as e:
            exp_log.exception(e)
            return True

    @staticmethod
    @async_time_track
    async def count_friends_validator(count):
        await TextHandler(SIGNS['yellow'], f'Проверка на количество друзей', 'warning')
        # count = session.method('status.get', {'user_id': user_id})
        if 24 <= count <= 1001:
            await TextHandler(SIGNS['green'], f'Число друзей соответствует')
            return True
        else:
            await TextHandler(SIGNS['red'], 'Не соответствует число друзей', 'error')
            return False

    @staticmethod
    @async_time_track
    async def mens_validator(info):
        male, female, friends = info
        await TextHandler(SIGNS['yellow'], f' девушек - {female}', 'warning', )
        await TextHandler(SIGNS['yellow'], f'Количество парней - {male}', 'warning', )
        await TextHandler(SIGNS['yellow'], f'Проверка на соотношение м / ж', 'warning', )
        res = male / friends * 100
        # print(round(res))
        if round(res) <= 35:
            await TextHandler(SIGNS['red'],
                              f'Количество мужчин меньше 35 процентов на общее количество друзей - Процент мужчин {res}%',
                              'error')

            return False
        else:
            await TextHandler(SIGNS['yellow'], f'Количество мужчин соответствует критериям. Процент мужчин - {res}%',
                              'warning')
            return True


@async_time_track
async def search_answer(text, city):  # todo
    """
    конвертирование разных по структуре но одинаковых
    по значению слов к общему по значению слову
    """
    answer_end = ''

    city_dict_yes = TALK_DICT_ANSWER_ALL['город']
    city_dict_no = TALK_DICT_ANSWER_ALL['негород']

    try:
        for a, b in TALK_DICT_ANSWER_ALL.items():
            if a == 'город' or a == 'негород':
                continue
            # print(a, b)
            if any(token in text for token in b["вход"]):
                answer = random.choice(b['выход'])
                answer_end += answer + ','
                # print(answer)
                # return answer
        answer_end = answer_end[0:-1]

        if any(city_text in text for city_text in city_dict_yes['вход']):
            answer = random.choice(city_dict_yes['выход'])
            res_answer = answer.format(city)
            # answer_end += res_answer + ','
            answer_end += res_answer

        elif any(city_text in text for city_text in city_dict_no['вход']):
            answer = random.choice(city_dict_no['выход'])
            # answer_end += answer + ','
            answer_end += answer

        return answer_end
    except Exception as e:
        print(e)
        return False


class RequestSex(Thread):

    def __init__(self, user_id, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.answer = False
        self.token = token

    def run(self):
        res = requests.get(
            url=f'https://api.vk.com/method/users.get?user_ids={self.user_id}&fields=bdate&fields=sex&access_token={self.token}&v=5.131')
        # print(res.json()['response'][0])
        if res.json()['response'][0]['sex'] == 2:
            # print(res)
            self.answer = True
            return True
        else:
            return False


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
    data = split_list(TOKENS)
    print(f'Выгружены данные токенов в количестве {len(TOKENS)}\n'
          f'Начинаю запуск бота в двухпроцессорном режиме')
    for i in TOKENS:
        print(i)
    # окго для контроля #todo
    worker = [Process(target=run_threads2, args=(i,)) for i in data]
    for i in worker:
        i.start()


def run_threads(data):
    # print(data)
    # print(sys.prefix)
    # print(multiprocessing.current_process())

    worker = []
    for i in data:
        loop = asyncio.new_event_loop()
        worker.append(Process(VkUserControl(i, loop)))

    for i in worker:
        i.start()

        # def image_to_byte_array(image: Image):


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


def upload_user_state(res):
    global USER_LIST
    USER_LIST = {}
    for key, value in res.items():
        USER_LIST[int(key)] = User(int(key), value['state'], value['name'], value['city'])


def create_checkmark(mode=False):
    # return colored('[+]', 'bright green')
    return colored('[✓]', 'bright green')


def text_colored(text):
    return colored(text, 'green', 'italic')


def create_arrow(count):
    return colored(f"{' ' * (count - 1)}►", "magenta")


# red_point = colored('R', 'red')
# green_point = colored('G', 'green')
# yellow_point = colored("Y", 'yellow')


# mark_sing = '[✓]'

mark = create_checkmark()

# cross = colored('[X]', 'red', 'bold')


# print(cross)

red_point = LOG_COLORS['error'][1]
green_point = LOG_COLORS['info'][1]
yellow_point = LOG_COLORS['warning'][1]

# sign #todo


verification_failed = lambda user, name: TextHandler(SIGNS['red'],
                                                     f'{user} {name} Проверку не прошел / Добавлен в unusers',
                                                     'error')

START_DATA = {
    'config': {
        'read_file': read_config,
        'text':
            [(SIGNS['green'], f'Конфигурационный файл  <config.json5> для токенов загружен:'),
             (SIGNS['mark'], f'Данные токенов загружены:'),
             (SIGNS['mark'], f'Данные для задержки загружены:'),
             ]
    },
}

start_data = {

}


async def upload_all_data_main():
    global TALK_DICT_ANSWER_ALL, TOKENS, TALK_TEMPLATE, USER_STATE, config
    try:
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            await async_eel.AddVersion(f"VkBot v{VERSION}")()
        # cprint("VkBotDir 1.6.3.1", 'bright yellow')
        await TextHandler(f"VkBot v{VERSION}", '', color='blue')

        config = read_config()
        TOKENS = config['tokens']
        answer = 'config.json5'

        await TextHandler(SIGNS['green'], f'Конфигурационный файл  {answer} для токенов загружен:')
        await TextHandler(SIGNS['mark'], f'Данные токенов загружены:')
        await TextHandler(SIGNS['magenta'], f'Загруженно токенов {len(TOKENS)}: ', color='magenta')
        for a, b in enumerate(TOKENS, 1):
            await TextHandler(SIGNS['magenta'], f"    {b}", color='magenta')

        await TextHandler(SIGNS['mark'], f'Данные для задержки загружены:')
        delay = f"[{config['delay_response_from']} - {config['delay_response_to']}] s"
        await TextHandler(SIGNS['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{config['delay_typing_from']} - {config['delay_typing_to']}] s"
        await TextHandler(SIGNS['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        TALK_DICT_ANSWER_ALL = read_json()
        answer2 = f"Данные для разговора загружены"
        await TextHandler(SIGNS['mark'], answer2)

        TALK_TEMPLATE = read_template()
        answer1 = 'template.json'
        await TextHandler(SIGNS['mark'], f'Файл {answer1} для шаблонов загружен')

        # Выгрузка стадий и юзеров
        await upload_sql_users()
        # USER_STATE = read_userstate()
        # upload_user_state(USER_STATE)
        # todo

        answer2 = 'userstate.json'
        await TextHandler(SIGNS['mark'], f'Файл {answer2} для этапов ИИ загружен')

        # upload_users()#todo

        answer3 = 'users.txt'
        await TextHandler(SIGNS['mark'], f'Файл {answer3} для белого списка загружен')
        answer4 = 'unusers.txt'
        await TextHandler(SIGNS['mark'], f'Файл {answer4} для черного списка загружен')

        await TextHandler(SIGNS['magenta'], 'Проверка прокси:', color='magenta')
        proxy = config['proxy']

        # if is_bad_proxy(proxy):
        #     await TextHandler(SIGNS['magenta'], f"    BAD PROXY {proxy}", log_type='error', full=True)
        # else:
        #     await TextHandler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING')
    except Exception as e:
        exp_log.exception(e)


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


async def main():
    await init_eel()
    await upload_all_data_main()
    # run_threads(TOKENS)  # todo
    #

    vk = VkUserControl(TOKENS[0])
    await vk.run_session()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(vk.run_session())

    # asyncio.run_coroutine_threadsafe(vk.run_session(), loop)
    # loop.run_forever()
    # asyncio.run(vk.run_session())


def main5():
    upload_all_data_main()

    # run_threads(TOKENS)
    run_multiproc4()


def main2():
    two_thread_loop()


def main3(loop1):
    # loop1 = asyncio.new_event_loop()
    upload_all_data_main()
    asyncio.set_event_loop(loop1)
    asyncio.get_event_loop()
    vk = VkUserControl(TOKENS[0], loop=loop1)
    # loop1.create_task(vk.run_session())
    # loop1.run_forever()
    loop1.run_until_complete(vk.run_session())


def main4(loop2):
    # loop2 = asyncio.new_event_loop()
    upload_all_data_main()
    asyncio.set_event_loop(loop2)
    asyncio.get_event_loop()
    vk = VkUserControl(TOKENS[0], loop=loop2)
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


if __name__ == '__main__':
    asyncio.run(main())
    # main()
    # multiprocessing.freeze_support()
    # Thread(target=scr).start()  # todo #ph
    # Thread(target=send_keyboard).start()  # todo #key
    # two_thread_loop()
    # exit()

    # thread_b = Thread(target=main3, args=(loop1,), daemon=True)

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(main())
    # many_loops()
    # main5()
    # main2()

# todo добавить мультипроцессорность
# исправить проблему с несклькими сообщениями когда отправляют сразу
# todo добавить прокси
# todo добавить для каждого пользователя класс с выгрузкой основных методов при первом запустке
# добавить в Unuser после окончания стадий
# todo добавить отображение в консоли блока если
# логирование
# todo тесты
# todo убрать ошибку со скрином
# определять по цвету текста в какой лог записать
# добавить sql базу данных
# todo запись общения в файл write_in_file

# база данных для user unuser userstate
# отключить интерефейс
# todo писать сообщения
# todo добавить многопроцессорность
# todo соединят и отпавлять как одно
# todo вынести весь текст в отдельный файл
# todo класс мета для декораторов
# todo доработать мультипроцессорность
# сделать поочередную проверку валидаторов
# проверчть друзей и отпавлять ттот же города
# добавить вариант ответа добавить в друзья или убрать полностью
# убирать людей без фото
# добавил проверку на добавление в друзья
# проверка с помощью ин
# добавит варинт выбра города
# добавить фукнцию для города впереди и сзади
# check
