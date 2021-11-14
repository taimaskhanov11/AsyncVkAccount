import json
import time
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# filename = r'C:\Users\taima\PycharmProjects\vk_account\main\tokens_data.txt'
import json5

BASE_DIR = Path(__file__).parent

def read_json(path, encoding='utf-8-sig'):
    # with open('config/answers.json', 'r', encoding='utf-8-sig') as ff:
    with open(Path(BASE_DIR, path), 'r', encoding=encoding) as ff:
        return json.load(ff)

def read_template():
    # print('Укажите json файл для шаблонов')
    # Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    # filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    with open(Path(BASE_DIR,path), 'r', encoding='utf-8-sig') as ff:
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
    time_track(read_userstate)()
    # upload_users()
