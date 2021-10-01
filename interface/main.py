import gevent.monkey
gevent.monkey.patch_all()

# from settings import TEXT_HANDLER_CONTROLLER
import os
import eel
from more_termcolor import colored


def init_eel():
    if __name__ in ['__main__']:
        print('HELLO')
        eel.init(r'www')
    else:
        # eel.init('VkBotDir/main/interface/www')
        print(os.getcwd())
        eel.init(r'interface/www')
    eel.start('index.html', block=False, size=(1000, 600), host='localhost', port=8000)  # todo


import datetime
import random
import time
from threading import Thread

# print(1)
# eel.init(r'www')
# eel.init(r'C:\Users\taima\PycharmProjects\vk_account\VkBotDir\main\interface\www')

# eel.init(r'VkBotDir.main.interface\www')

# eel.start('index.html', block=False, size=(1000, 600), host='localhost', port=8000)  # todo


# eel.init('www')

# eel.start('index.html', block=False, size=(1000, 600) ) #todo

# eel.init(r'C:\Users\taima\PycharmProjects\vk_account\VkBotDir\interface\www')
# eel.start('index.html', block=False, size=(1000, 600), host='localhost', port=8000)  # todo

sign_1 = colored("⬤", 'green', 'italic')

colors = {'red': 1, 'green': 1, 'yellow': 1, 'black': 1,
          'blue': 1, 'magenta': 1, "Lime": 1, 'white': 1,
          '#cef10c': 1, 'cyan': 1}

SESSION_DATA = {'user': [],
                'numbers': [],
                }
TURN = []

numbers = ['1']
now_users = ['2']
now_unusers = ['3']

window_data = {
    'numbers': numbers,
    'users': now_users,
    'unusers': now_unusers,

}

WINDOW_MODE = 'numbers'


def window_create(user_id, name, number=None, mode='numbers'):
    print(user_id, name, number, mode)
    window_data[mode].append(f'<a href="https://vk.com/id{user_id}">{name}</a> - {number}<br>')
    # numbers.append(f'<a href="https://vk.com/id{user_id}">{name}</a> - {number}<br>')
    eel.createDiv()


def window_update(user_id, name, number='', mode='numbers'):
    text = f'<a href="https://vk.com/id{user_id}">{name}</a> - {number}<br>'
    window_data[mode].append(text)
    if WINDOW_MODE == mode:
        eel.updateDiv(text, 'elem0')


# print(''.join(numbers))
@eel.expose
def window_return(mode):
    # print(mode)
    global WINDOW_MODE
    WINDOW_MODE = mode
    return ''.join(window_data[mode])


@eel.expose()
def color_change(color):
    if colors[color]:
        colors[color] = False
    else:
        colors[color] = True


count = 0


# @eel.expose()
def run(sign, text, color, full=False):
    if colors[color]:
        # eel.addText(f'⬤ Время сейчас {datetime.datetime.now().replace(microsecond=0)} {count}', i)
        # print(text)
        if full:
            eel.addText(
                f'<span style="color: {color}">{sign}{text}</span>')
        else:
            eel.addText(
                f'<span style="color: {color}">{sign}</span> {text}')
        # eel.sleep(1)


# def ali(text,color):
#    global count
#    for i in colors:
#        if colors[i]:
#            count += 1
#            # eel.addText(f'⬤ Время сейчас {datetime.datetime.now().replace(microsecond=0)} {count}', i)
#            eel.addText(
#                f'<span style="color: {i}">⬤</span> Время сейчас {datetime.datetime.now().replace(microsecond=0)} {count}',
#                i)
#            # eel.sleep(1)
#    # return i
def my_other_thread():
    while True:
        print("I'm a thread")
        eel.sleep(1.0)


def interface(sign, text, color, full=False):
    # while True:
    # run(f'⬤ The time now is {datetime.datetime.now().replace(microsecond=0)}', 'red')
    run(sign, text, color, full)
    # Thread(target=run, args=(text, color)).start()
    # eel.addText(f'⬤ The time now is {datetime.datetime.now().replace(microsecond=0)}')

    # eel.sleep(1) # todo

    # time.sleep(1)
    # eel.test()()  # todo


# eel.spawn(interface)

def runner():
    while True:
        # interface(f'⬤ The time now is {datetime.datetime.now().replace(microsecond=0)}', 'red')
        # print(__name__)
        eel.sleep(0.1)


# eel.spawn(runner)

# Thread(target=runner).start()

# print(1)
# runner()
def ali():
    print(1)


# if TEXT_HANDLER_CONTROLLER['accept_interface']:
init_eel()

if __name__ == '__main__':
    my_other_thread()
    # eel.spawn(runner)
    # time.sleep(20)

    # while True:
    #     ali()

    # interface(1, 'red')
    # eel.sleep(1)
    # interface(1,'red')
    # interface(f'⬤ The time now is {datetime.datetime.now().replace(microsecond=0)}', 'red')
    # eel.sleep(0.1)
    # eel.sleep(1)
    # eel.spawn(my_other_thread)
    # while True:
    #
    #     eel.spawn(runner)
    #     eel.sleep(1)
    # while True:
    #     # interface(f'⬤ The time now is {datetime.datetime.now().replace(microsecond=0)}', 'red')
    #     # print("I'm a main loop")
    # #     # eel.spawn(interface, args=(f'⬤ The time now is {datetime.datetime.now().replace(microsecond=0)}', 'red'))
    # #     # eel.sleep(10)
    #     eel.sleep(1)
    # run()
    # main()
