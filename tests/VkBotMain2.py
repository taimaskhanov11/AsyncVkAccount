from VkBotDir.database.database import Users
from VkBotDir.settings import VERSION, LOG_COLORS, TEXT_HANDLER_CONTROLLER, SIGNS, TextHandler, time_track

if TEXT_HANDLER_CONTROLLER['accept_interface']:
    from interface.main import interface, eel, window_update

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
from vk_api.longpoll import VkLongPoll, VkEventType

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


@time_track
def upload_sql_users():
    # global USER_LIST
    for user in Users.select():
        _id = user.user_id
        if user.type:
            users.append(_id)
            USER_LIST[_id] = User(_id, user.state, user.name, user.city)
            # print(USER_LIST)
        else:
            unusers.append(_id)


@time_track  # legacy
def upload_users():
    with open('users.txt', 'r') as ff:
        for i in ff:
            users.append(int(i.strip()))
    with open('unusers.txt', 'r') as ff:
        for i in ff:
            unusers.append(int(i.strip()))


@time_track
def update_users(user_id, name, mode=True, city=None):
    if TEXT_HANDLER_CONTROLLER['accept_interface']:
        mode = 'users' if mode else 'unusers'
        window_update(user_id, name, number='', mode=mode)

    if mode:
        if mode == 'number':
            unusers.append(user_id)
            Users.change_value(user_id, 'type', False)
        else:
            Users.create_user(user_id, name, city, 1)
            USER_LIST[user_id] = User(user_id, 1, name, city)
            users.append(user_id)
            return USER_LIST[user_id]
            # with open('users.txt', 'a') as ff:
            #     ff.write(f'{user_id}\n')
    else:
        unusers.append(user_id)
        # with open('unusers.txt', 'a') as ff:
        #     ff.write(f'{user_id}\n')


class User:

    def __init__(self, user_id, state, name, city):
        self.user_id = user_id
        self.state = state
        self.name = name
        self.city = city

        self.len_template = len(TALK_TEMPLATE)
        self.half_template = self.len_template // 2
        self.block_template = 0

    @time_track
    def append_to_exel(self, user_id, text, name):
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

    @time_track
    def add_state(self):
        self.state += 1
        Users.add_state(self.user_id)

    @time_track
    def act(self, text):
        # print(TALK_TEMPLATE)

        if self.half_template <= self.state <= self.len_template + 1:
            # print(self.state)
            result = re.findall('\d{4,}', text)
            if result:
                self.append_to_exel(self.user_id, text, self.name)
                # print(f'{mark} {user_id} / {name} Номер получен добавление в unusers')
                window_update(self.user_id, self.name, text, mode='numbers')

                TextHandler(SIGNS['mark'], f'{self.user_id} / {self.name} Номер получен добавление в unusers')

                update_users(self.user_id, 'number')
                # todo добавление в unuser после номера
                return False
            if self.state == self.len_template + 1:
                # self.state += 1
                self.add_state()
                return False
            res = random.choice(TALK_TEMPLATE[f"state{self.state}"])
            # self.state += 1
            self.add_state()

            return res

        else:
            if self.state >= self.len_template + 2:
                return False
            else:
                res = random.choice(TALK_TEMPLATE[f"state{self.state}"])
                self.add_state()

                # self.state += 1
                return res


class VkUserControl(Thread):

    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.token = token
        # self.session = vk_api.VkApi(token=token, api_version='5.131')
        self.session = vk_api.VkApi(token=token, api_version='5.131')
        self.vk = self.session.get_api()
        self.longpoll = VkLongPoll(self.session)
        self.users_block = {}
        self.info = self.vk.users.get(fields=['photo_max_orig'])[0]
        # print(self.info) # фото валидатор
        self.validators = (lambda x: x, self.age_validator, self.count_friends_validator, self.mens_validator,)

    def run(self):
        # print('Текущий поток', multiprocessing.current_process(), threading.current_thread())#todo

        self.run_session()

    @time_track
    def get_user_info(self, user_id):
        res = self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        # print(res)
        return res

    @time_track
    def sen_message(self, user, text):
        self.vk.messages.send(user_id=user,
                              message=text,
                              random_id=0)

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

    @time_track
    def get_friend(self, user_id):
        try:
            # return self.vk.friends.get(user_id=user_id)
            return self.vk.friends.search(user_id=user_id, fields=["sex", "city"], count=1000)
        except Exception as e:
            print(f'{e}')
            return False

    def write_in_file(self, user, text, answer):
        with open(f'chat_files/{user}.txt', 'a', encoding='utf8') as ff:
            ff.write(
                f'Сообщение от пользователя {user} : {text}\n     Ответ : {answer} |Время {datetime.datetime.now().replace(microsecond=0)}\n\n')

    def check_status_friend(self, user_id):
        try:
            return self.vk.friends.areFriends(user_ids=user_id)[0]['friend_status']
        except Exception as e:
            print(f'{e} Ошибка')
            return 'private'

    def add_friend(self, user_id):
        self.vk.friends.add(user_id=user_id)

    def check_and_add_friend(self, user_id):  # todo
        pass

    @staticmethod
    @time_track
    def write_userstate(user, name, city):  # legacy
        # now = time.time()
        state = USER_LIST[user].state
        USER_STATE[str(user)] = {'state': state,
                                 'name': name,
                                 'city': city}

        with open('userstate.json', 'w', encoding='utf8') as ff:
            json.dump(USER_STATE, ff, indent=4, ensure_ascii=False)
        # end = round(time.time() - now, 6)
        # TextHandler(SIGNS['time'], f'Время записи {end} s', 'debug',
        #             off_interface=True)

    @time_track
    def thread_send_message(self, user_id, text):
        USER_LIST[user_id].block_template += 1
        # рандомный сон
        delay_response_from, delay_response_to = config['delay_response_from'], config['delay_response_to']

        random_sleep_answer = random.randint(delay_response_from, delay_response_to)
        # print(random_sleep_answer)
        time.sleep(random_sleep_answer)
        # todo
        self.vk.messages.set_activity(user_id=user_id, type='typing')
        # рандомный сон
        delay_typing_from, delay_typing_to = config['delay_typing_from'], config['delay_typing_to']
        random_sleep_typing = random.randint(delay_typing_from, delay_typing_to)
        time.sleep(random_sleep_typing)
        self.session.method('messages.send', {'user_id': user_id,  # отправка ответа
                                              'message': text,
                                              'random_id': 0, })

        USER_LIST[user_id].block_template = 0

    @staticmethod
    @time_track
    def find_most_city(friend_list):
        friends_city = [i['city']['title'] for i in friend_list['items'] if
                        i.get('city')]
        c_friends_city = Counter(friends_city)
        city = max(c_friends_city.items(), key=lambda x: x[1])[0]
        return city

    @time_track
    def initialization_menu(self):
        eel.changeText(f'{self.info["first_name"]} {self.info["last_name"]}', 'text1')
        photo = self.info.get('photo_max_orig')
        if photo:
            res = requests.get(photo).content
            file = f'{self.info["id"]}.png'
            with open(f'interface/www/media/{file}', 'wb') as ff:
                ff.write(res)
            TextHandler(SIGNS['green'], 'Фото загружено')
            eel.giveAvatar(file)

    @staticmethod
    @time_track
    def user_info_view(info, friend_list, age, has_photo):
        TextHandler(SIGNS['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}",
                    'warning')
        TextHandler(SIGNS['yellow'], f"{friend_list['count']} - Количество друзей", 'warning')
        TextHandler(SIGNS['yellow'], f'Возраст - {age}', 'warning')
        TextHandler(SIGNS['yellow'], f'Фото {has_photo}', 'warning')

    @time_track
    def run_session(self):
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            self.initialization_menu()
        while True:
            try:
                for event in self.longpoll.listen():
                    # print(event.type)
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                        # print(event.type)
                        if event.from_user:  # Если написали в ЛС
                            text = event.text.lower()
                            user = event.user_id

                            check_time_start = time.time()
                            if text == 'endthisnow':
                                return
                            if user in unusers:

                                TextHandler(SIGNS['red'], f'Новое сообщение от {user} / Черный список / : {text}',
                                            'error')  # todo

                                continue

                            elif user in users:
                                auth_user = USER_LIST[user]
                                if auth_user.block_template < 2:
                                    name = auth_user.name
                                    city = auth_user.city

                                    TextHandler(SIGNS['green'], f'Новое сообщение от {name} / {user} - {text}',
                                                'info')  # todo

                                    answer = search_answer(text, city)
                                    template = auth_user.act(text)  # todo

                                    # Сохранение состояния в файл
                                    # self.write_userstate(user, name, city)

                                    if template:
                                        Thread(target=self.thread_send_message,
                                               args=(user, f"{answer} {template}")).start()

                                        # self.write_in_file(user, text, answer)
                                    else:
                                        TextHandler(SIGNS['red'], f"{user} / {name} / Стадия 7 или больше / Игнор",
                                                    'error')
                                    check_time_end = round(time.time() - check_time_start, 6)
                                    TextHandler(SIGNS['time'], f'Время ответа {check_time_end} s', 'debug', #todo сделать функцией
                                                off_interface=True, prop=True)

                            else:  # Если нету в базе

                                info = self.get_user_info(user)[0]
                                name = info['first_name']

                                TextHandler(SIGNS['yellow'],
                                            f'Новое сообщение от {name} / {user} / Нету в базе - {text}',
                                            'warning')

                                can_access_closed = info["can_access_closed"]
                                add_status = self.check_status_friend(user)

                                TextHandler(SIGNS['yellow'], f"Статус дружбы {add_status}", 'warning')

                                if not can_access_closed:
                                    if add_status == 0:

                                        if user not in self.users_block:
                                            self.users_block[user] = 0

                                        if self.users_block[user] > 1:
                                            continue

                                        self.vk.messages.send(user_id=user,
                                                              message=random.choice(
                                                                  TALK_DICT_ANSWER_ALL['private']['выход']),
                                                              random_id=0)

                                        self.users_block[user] += 1
                                        # self.write_in_file(user, text, "приветик добавь меня в друзья :)")
                                        # self.add_friend(user)
                                        continue
                                    elif add_status == 2:
                                        TextHandler(SIGNS['yellow'], f"Добавление в друзья", 'warning')

                                        self.add_friend(user)

                                    elif add_status == 1:
                                        self.vk.messages.send(user_id=event.user_id,
                                                              message="было бы круто если бы ты принял заявку в друзья &#128522;",
                                                              random_id=0)
                                        continue

                                friend_list = self.get_friend(user)
                                # print(friend_list)

                                m_f_count = [i['sex'] for i in friend_list['items']]

                                female = m_f_count.count(1)
                                male = m_f_count.count(2)
                                age = info.get('bdate')
                                has_photo = info['has_photo']

                                self.user_info_view(info, friend_list, age, has_photo)

                                count_friend = friend_list['count']
                                valid = self.all_validators(has_photo, age, count_friend, (male, female, count_friend))
                                # if self.age_validator(age) and self.count_friends_validator(count_friend) and has_photo:
                                if valid:
                                    # todo выбрать между много проц поточ и одним
                                    TextHandler(SIGNS['mark'],
                                                f'{user} / {name} / Прошел все проверки / Добавлен в users',
                                                'info')
                                    # поиск города
                                    city = self.find_most_city(friend_list)

                                    auth_user = update_users(user, name, city=city)
                                    template = auth_user.act(text)

                                    # self.write_userstate(user, name, USER_LIST[user].city)

                                    # print(f'Время записи {round(time.time() - now, 5)} s')  # todo
                                    answer = search_answer(text, city)
                                    current_answer = f"{answer} {template}" if (answer or template) else \
                                        search_answer('привет', friend_list)

                                    self.sen_message(user, current_answer)
                                    #
                                    # if answer or template:
                                    #     self.vk.messages.send(user_id=event.user_id,
                                    #                           message=f"{answer} {template}" if answer or template else,
                                    #                           random_id=0)  # todo работать тут 1
                                    # else:
                                    #     self.vk.messages.send(user_id=event.user_id,
                                    #                           message=search_answer('привет', friend_list),
                                    #                           random_id=0)
                                    check_time_end = round(time.time() - check_time_start, 6)
                                    TextHandler(SIGNS['time'], f'Время полной проверки {check_time_end} s', 'debug',
                                                off_interface=True, prop=True)
                                    continue

                                verification_failed(user, name)

                                update_users(user, name, False)



            except Exception as e:
                exp_log.exception(e)
                # print('ПЕРЕПОДКЛЮЧЕНИЕ...')  # todo
                TextHandler(SIGNS['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error')

    # def all_validators(self, age, count_friends, friends, male):
    @time_track
    def all_validators(self, *args):
        validators = (func(value) for func, value in zip(self.validators, args))
        for valid in validators:
            if not valid:
                return False
        return True
        # for func, value in zip(self.validators, args):
        #     print(value)
        #     print(func(value))

        # result = [self.age_validator(age), self.count_friends_validator(count_friends), self.mens_validator(friends, male)]
        # if all(result):
        #     return True
        # else:
        #     # 'Не прошел проверку на валидность'
        #     return False

    @staticmethod
    @time_track
    def photo_validator(photo):
        TextHandler(SIGNS['yellow'], f'Проверка на фото', 'warning')
        if photo:
            TextHandler(SIGNS['yellow'], f'Проверку на фото прошел', 'warning')
            return True
        else:
            TextHandler(SIGNS['red'], f'Фото отсутствует', 'error')
            return False

    @staticmethod
    @time_track
    def age_validator(age):
        TextHandler(SIGNS['yellow'], f'Проверка на возраст', 'warning')
        try:
            if age:
                # print(age)
                age = age[-1:-5:-1]
                age = age[-1::-1]
                # print(age)
                date = 2021 - int(age)
                if date >= 20:
                    TextHandler(SIGNS['green'], 'Возраст соответствует')
                    return True
                else:
                    TextHandler(SIGNS['red'], 'Не соответствует возраст', 'error')
                    return False
            else:
                return True  # todo
        except Exception as e:
            exp_log.exception(e)
            return True

    @staticmethod
    @time_track
    def count_friends_validator(count):
        TextHandler(SIGNS['yellow'], f'Проверка на количество друзей', 'warning')
        # count = session.method('status.get', {'user_id': user_id})
        if 24 <= count <= 1001:
            TextHandler(SIGNS['green'], f'Число друзей соответствует')
            return True
        else:
            TextHandler(SIGNS['red'], 'Не соответствует число друзей', 'error')
            return False

    @staticmethod
    @time_track
    def mens_validator(info):
        male, female, friends = info
        TextHandler(SIGNS['yellow'], f' девушек - {female}', 'warning', )
        TextHandler(SIGNS['yellow'], f'Количество парней - {male}', 'warning', )
        TextHandler(SIGNS['yellow'], f'Проверка на соотношение м / ж', 'warning', )
        res = male / friends * 100
        # print(round(res))
        if round(res) <= 35:
            TextHandler(SIGNS['red'],
                        f'Количество мужчин меньше 35 процентов на общее количество друзей - Процент мужчин {res}%',
                        'error')

            return False
        else:
            TextHandler(SIGNS['yellow'], f'Количество мужчин соответствует критериям. Процент мужчин - {res}%',
                        'warning')
            return True


@time_track
def search_answer(text, city):  # todo
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


def run_threads2(data):
    print(data)
    # print(sys.prefix)
    # print(multiprocessing.current_process())
    worker = [VkUserControl(i) for i in data]
    print(worker)
    for i in worker:
        i.start()


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
    worker = [VkUserControl(i) for i in data]

    # print(f'Потоки {worker}')#todo

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


def upload_all_data_main():
    global TALK_DICT_ANSWER_ALL, TOKENS, TALK_TEMPLATE, USER_STATE, config
    try:
        if TEXT_HANDLER_CONTROLLER['accept_interface']:
            eel.AddVersion(f"VkBot v{VERSION}")
        # cprint("VkBotDir 1.6.3.1", 'bright yellow')
        TextHandler(f"VkBot v{VERSION}", '', color='blue')

        config = read_config()
        TOKENS = config['tokens']
        answer = 'config.json5'

        TextHandler(SIGNS['green'], f'Конфигурационный файл  {answer} для токенов загружен:')
        TextHandler(SIGNS['mark'], f'Данные токенов загружены:')
        TextHandler(SIGNS['magenta'], f'Загруженно токенов {len(TOKENS)}: ', color='magenta')
        for a, b in enumerate(TOKENS, 1):
            TextHandler(SIGNS['magenta'], f"    {b}", color='magenta')

        TextHandler(SIGNS['mark'], f'Данные для задержки загружены:')
        delay = f"[{config['delay_response_from']} - {config['delay_response_to']}] s"
        TextHandler(SIGNS['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{config['delay_typing_from']} - {config['delay_typing_to']}] s"
        TextHandler(SIGNS['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        TALK_DICT_ANSWER_ALL = read_json()
        answer2 = f"Данные для разговора загружены"
        TextHandler(SIGNS['mark'], answer2)

        TALK_TEMPLATE = read_template()
        answer1 = 'template.json'
        TextHandler(SIGNS['mark'], f'Файл {answer1} для шаблонов загружен')

        # Выгрузка стадий и юзеров
        upload_sql_users()
        # USER_STATE = read_userstate()
        # upload_user_state(USER_STATE)
        # todo

        answer2 = 'userstate.json'
        TextHandler(SIGNS['mark'], f'Файл {answer2} для этапов ИИ загружен')

        # upload_users()#todo

        answer3 = 'users.txt'
        TextHandler(SIGNS['mark'], f'Файл {answer3} для белого списка загружен')
        answer4 = 'unusers.txt'
        TextHandler(SIGNS['mark'], f'Файл {answer4} для черного списка загружен')

        TextHandler(SIGNS['magenta'], 'Проверка прокси:', color='magenta')
        proxy = config['proxy']

        if is_bad_proxy(proxy):
            TextHandler(SIGNS['magenta'], f"    BAD PROXY {proxy}", log_type='error', full=True)
        else:
            TextHandler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING')
    except Exception as e:
        exp_log.exception(e)


def main():
    upload_all_data_main()
    # run_threads(TOKENS) #todo
    #
    vk = VkUserControl(TOKENS[0])
    vk.run_session()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    # Thread(target=scr).start()  # todo #ph
    # Thread(target=send_keyboard).start()  # todo #key
    main()

# todo добавить мультипроцессорность
# исправить проблему с несклькими сообщениями когда отправляют сразу
# todo добавить прокси
# todo добавить для каждого пользователя класс с выгрузкой основных методов при первом запустке
# todo добавить в Unuser после окончания стадий
# todo добавить отображение в консоли блока если
# todo логирование
# todo тесты
# todo убрать ошибку со скрином
# todo определять по цвету текста в какой лог записать
# todo добавить sql базу данных
# todo запись общения в файл write_in_file

# todo база данных для user unuser userstate
# todo отключить интерефейс
# todo писать сообщения
# todo добавить многопроцессорность
# todo соединят и отпавлять как одно
# todo вынести весь текст в отдельный файл
# todo класс мета для декораторов
# todo сделать поочередную проверку валидаторов

# проверчть друзей и отпавлять ттот же города
# добавить вариант ответа добавить в друзья или убрать полностью
# убирать людей без фото
# добавил проверку на добавление в друзья
# проверка с помощью ин
# добавит варинт выбра города
# добавить фукнцию для города впереди и сзади
# check
