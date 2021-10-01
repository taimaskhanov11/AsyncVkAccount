import datetime
import io
import logging
import multiprocessing
import random
import threading

from multiprocessing import Process
from threading import Thread
import requests
import vk_api
import time
import pyautogui

from vk_api.longpoll import VkLongPoll, VkEventType

from open_data import read_json, read_file, read_template

logging.basicConfig(level=logging.INFO)

users = []
unusers = []
import telebot

TOKEN = '1623818411:AAE4iAu4JqlqUgoMI85deLc1KV94rG-CVJY'
# TOKEN = '1711808404:AAFSZICWTmMrutOBKO8a3C1DatpxzSCccE8'
# TOKEN = '1829887939:AAHDWw57KSvQi8zZthDOzGzIWuqSKX6WIcs'
BOT = telebot.TeleBot(TOKEN)
SendMessage = BOT.send_message

add_for_friend = ["приветик добавь меня в друзья :))", "добавь в друзья"]  # todo


def upload_users():
    with open('../users.txt', 'r') as ff:
        for i in ff:
            users.append(int(i.strip()))
    with open('../unusers.txt', 'r') as ff:
        for i in ff:
            unusers.append(int(i.strip()))


upload_users()


def upgrade_users(user_id, mode=True):
    if mode:
        with open('../users.txt', 'a') as ff:
            ff.write(f'{user_id}\n')
    else:
        with open('../unusers.txt', 'a') as ff:
            ff.write(f'{user_id}\n')


class VkUserControl(Thread):

    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.token = token
        self.session = vk_api.VkApi(token=token)
        self.vk = self.session.get_api()

    def run(self):
        print(multiprocessing.current_process(), threading.current_thread())
        self.run_session()

    def get_user_info(self, user_id):
        res = self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo'])
        print(res)
        return res

    def sen_message(self, user, text):
        self.vk.messages.send(user_id=user,
                              message=text,
                              random_id=0)

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
        # print(res)
        # print(res)
        # print(len(res))#todo
        # print(res.count(True))
        return (len(res), res.count(True))

    def get_friend(self, user_id):
        try:
            return self.vk.friends.get(user_id=user_id)
        except Exception as e:
            print(f'{e}')
            return False

    def write_in_file(self, user, text, answer):
        with open(f'{user}.txt', 'a', encoding='utf8') as ff:
            ff.write(f'Сообщение от пользователя {user} : {text}\nОтвет : {answer}\n {datetime.datetime.now()}')

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

    def run_session(self):
        longpoll = VkLongPoll(self.session)
        print(users, "- ЮЗЕРЫ")
        print(unusers, "- АНЮЗЕРЫ")
        for event in longpoll.listen():
            print(event.type)
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                # print(event.type)
                if event.from_user:  # Если написали в ЛС
                    # time.sleep(1)  #todo Задержка перед ответом
                    text = event.text.lower()
                    user = event.user_id
                    if text == 'endthisnow':
                        return
                    if user in unusers:
                        self.session.method('messages.send', {'user_id': event.user_id,  # отправка ответа
                                                              'message': 'Не соответсвие1',
                                                              'random_id': 0, })
                        self.write_in_file(user, text, 'Не соответсвие1')
                        continue

                    print(f'Новое сообщение от {user}: {text}')

                    if user not in users:  # Если нету в базе
                        print('Нету в базе')
                        info = self.get_user_info(user)[0]
                        friend_list = self.get_friend(user)
                        can_access_closed = info["can_access_closed"]
                        add_status = self.check_status_friend(user)
                        print(123123, add_status)
                        if not can_access_closed:
                            if add_status == 0:
                                self.vk.messages.send(user_id=event.user_id,
                                                      message="приветик добавь меня в друзья :))",
                                                      random_id=0)
                                self.write_in_file(user, text, "приветик добавь меня в друзья :)")
                                # self.add_friend(user)
                                continue
                            elif add_status == 2:
                                self.add_friend(user)

                            elif add_status == 1:
                                self.vk.messages.send(user_id=event.user_id,
                                                      message="было бы круто если бы ты принял заявку в друзья &#128522;",
                                                      random_id=0)
                                self.write_in_file(user, text, "приветик добавь меня в друзья :)")
                                continue

                        # elif not can_access_closed:#todo
                        #     self.vk.messages.send(user_id=event.user_id, message="Добавь меня в друзья :)",
                        #                           random_id=0)
                        #     self.write_in_file(user, text, "Добавь меня в друзья :)")
                        #     continue
                        print(info['first_name'], info['last_name'], info['id'])
                        print(f"{friend_list['count']} - Количество друзей")
                        age = info.get('bdate')
                        print('Возраст -', age)
                        count_friend = friend_list['count']
                        has_photo = info['has_photo']
                        print('Фото', has_photo)
                        if self.age_validator(age) and self.count_friends_validator(count_friend) and has_photo:
                            print('Проверка на возраст')
                            print('Проверка на фото')
                            # if self.age_validator(age) :
                            # todo выбрать между много проц поточ и одним
                            print("Проверка на количество друзей")
                            count_mens = self.thread_url_pars_friend(friend_list['items'])  # с помощью url запросов
                            # print(count_mens)
                            assert count_friend == count_mens[0], 'Ошибка'
                            # valid = all_validators(age, count_friend, count_friend, count_mens[1]) #todo валидатор
                            if self.mens_validator(count_friend, count_mens[1]):
                                print('Проверка на соотношение м\ж')
                                users.append(user)
                                upgrade_users(user)
                                print(f'{user} {info["first_name"]} прошел все проверки')
                                answer = search_answer(text)
                                if answer:
                                    self.vk.messages.send(user_id=event.user_id, message=search_answer(text),
                                                          random_id=0)  # todo работать тут 1
                                    self.write_in_file(user, text, answer)

                                else:
                                    self.vk.messages.send(user_id=event.user_id, message=search_answer('привет'),
                                                          random_id=0)
                                    self.write_in_file(user, text, 'привет')

                            else:
                                print(f'{user} Проверку не прошел')
                                unusers.append(user)
                                upgrade_users(user, mode=False)
                                self.vk.messages.send(user_id=event.user_id, message="не соответсвие, соотношения м\ж",
                                                      random_id=0)
                                self.write_in_file(user, text, "не соответсвие, соотношения м\ж")

                        else:
                            print(f'{user} {info["first_name"]} Проверку не прошел')
                            unusers.append(user)
                            upgrade_users(user, False)
                            self.vk.messages.send(user_id=event.user_id,
                                                  message="не соответсвие2, Возраст или число друзей",
                                                  random_id=0)
                            self.write_in_file(user, text, "не соответсвие2, Возраст или число друзей")
                    else:
                        # print(f'{user} Проверку прошел')
                        answer = search_answer(text)  # todo работать тут 2
                        if answer:
                            self.vk.messages.send(user_id=event.user_id, message=search_answer(text), random_id=0)
                            self.write_in_file(user, text, answer)
                        else:
                            # pass
                            self.vk.messages.send(user_id=event.user_id, message='дайка подумаю', random_id=0)

    def all_validators(self, age, count_friends, x, y):
        result = [self.age_validator(age), self.count_friends_validator(count_friends), self.mens_validator(x, y)]
        if all(result):
            return True
        else:
            'Не прошел проверку на валидность'
            return False

    @staticmethod
    def age_validator(age):
        try:
            if age:
                # print(age)
                age = age[-1:-5:-1]
                age = age[-1::-1]
                # print(age)
                date = 2021 - int(age)
                if date >= 20:
                    return True
                else:
                    print('Не соответсвует возраст')
                    return False
            else:
                return True  # todo
        except:
            return True

    @staticmethod
    def count_friends_validator(count):
        # count = session.method('status.get', {'user_id': user_id})
        if 24 <= count <= 1001:
            return True
        else:
            print('Не соответсвует число друзей')
            return False

    @staticmethod
    def mens_validator(x, y):
        res = y / x * 100
        # print(round(res))
        if round(res) <= 35:
            print('Количество мужчин меньше 35 процентов на общее количество друзей')
            return False
        else:
            return True


def search_answer(text): #todo
    """
    конвертирование разных по структуре но одинаковых
    по значению слов к общему по значению слову
    """
    try:
        for a, b in TALK_DICT_ANSWER_ALL.items():
            # print(a, b)
            if text in b["вход"]:
                answer = random.choice(b['выход'])
                # print(answer)
                return answer
    except:
        return False
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


def run_threads3(data):
    print(data)
    # print(sys.prefix)
    # print(multiprocessing.current_process())
    worker = [VkUserControl(i) for i in data]
    print(worker)
    for i in worker:
        i.start()


# def image_to_byte_array(image: Image):


def scr():
    count = 0
    while True:
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        count += 1
        BOT.send_document(269019356, img_byte_arr)
        time.sleep(1)


def main_end2():
    multiprocessing.freeze_support()
    data = read_file()

    global TALK_DICT_ANSWER_ALL, TOKENS, TALK_TEMPLATE
    TALK_DICT_ANSWER_ALL = read_json()
    TALK_TEMPLATE = read_template()
    TOKENS = data['tokens']
    print(data)
    print(TALK_DICT_ANSWER_ALL)

    run_threads3(TOKENS)


if __name__ == '__main__':
    # Thread(target=scr).start() #todo
    main_end2()

# todo добавить мультипроцессорность
# todo убирать людей без фото
# todo добавил проверку на добавление в друзья
# todo проверка с помощью ин
