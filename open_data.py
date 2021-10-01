import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import json

# filename = r'C:\Users\taima\PycharmProjects\vk_account\main\tokens_data.txt'
import json5


def read_file2():
    print('Укажите Data file')
    # Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    # filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    token = []
    bd_login = ''
    bd_password = ''
    admin = []

    with open('tests/tokens_data.txt', 'r', newline='') as ff:
        mode = False
        for i in ff:
            i = i.strip()
            if not i:
                continue

            elif mode == 'database':
                bd_login = i
                mode = 'database1'

            elif mode == 'database1':
                bd_password = i
                mode = "admin"

            elif i == 'admin':
                mode = 'admin'

            elif mode == 'admin':
                admin.append(i)

            elif i == 'database':
                mode = 'database'

            if not mode:
                token.append(i)

    return {'tokens': token,
            "bd_login": bd_login,
            "bd_password": bd_password,
            "admin": admin}


def read_file():
    # print('Укажите Data file')
    # Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    # filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    token = []
    bd_login = ''
    bd_password = ''
    admin = []

    with open('tests/tokens_data.txt', 'r', newline='') as ff:
        mode = False
        for i in ff:
            i = i.strip()
            if not i:
                continue
            token.append(i)
    return {'tokens': token}


def read_config():
    with open('config.json5', 'r', encoding='utf-8-sig') as ff:
        return json5.load(ff)


# print(read_file())


# coding:utf8


# with open('myjson.json', 'w', encoding='utf8') as ff:
#     json.dump(TALK_DICT_ANSWER_ALL, ff, indent=4, ensure_ascii=False)

def read_json():
    # print('Укажите json файл для общения')
    # Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    # filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    with open('answers.json', 'r', encoding='utf-8-sig') as ff:
        a = json.load(ff)
    return a


def read_template():
    # print('Укажите json файл для шаблонов')
    # Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    # filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    with open('templatea.json', 'r', encoding='utf-8-sig') as ff:
        a = json.load(ff)
    return a


def read_userstate():
    try:
        with open('userstate.json', 'r', encoding='utf-8-sig') as ff:
            a = json.load(ff)
    except Exception as e:
        print(e)
        a = {}
        with open('userstate.json', 'w', encoding='utf-8') as ff:
            json.dump(a, ff)
    return a


def read_delay_answer():
    with open('delay_answer.json', 'r', encoding='utf-8-sig') as ff:
        res = json.load(ff)
    return res


def read_proxy():
    with open('proxy.json', 'r', encoding='utf-8-sig') as ff:
        res = json.load(ff)
    return res


users = []
unusers = []


def time_track(func):
    def wrapper(*args, **kwargs):
        now = time.time()
        res = func(*args, **kwargs)
        print(f'Executed time {round(time.time() - now, 5)} s')
        return res

    return wrapper


@time_track
def upload_users():
    with open('users.txt', 'r') as ff:
        for i in ff:
            users.append(i.strip())
    with open('unusers.txt', 'r') as ff:
        for i in ff:
            unusers.append(i.strip())


def upgrade_users(user_id):
    with open('users.txt', 'a') as ff:
        ff.write(f'{user_id}\n')
    with open('unusers.txt', 'a') as ff:
        ff.write(f'{user_id}\n')


# a = '123412'
# upgrade_users(a)
if __name__ == '__main__':
    time_track(read_config)()
    time_track(read_userstate)()
    # upload_users()
