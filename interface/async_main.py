# import gevent.monkey
# gevent.monkey.patch_all()
# import asyncio
# import os
import random
from pathlib import Path

import async_eel
from more_termcolor import colored


async def init_eel():
    # if __name__ in ['__main__']:
    #     # print('HELLO')
    #     async_eel.init(r'www')
    # else:
    #     # eel.init('VkBotDir/main/interface/www')
    #     # print(os.getcwd())
    #     async_eel.init(r'interface/www')
    path = Path(__file__).resolve().parent
    async_eel.init(f'{path}/www')

    port = random.randint(1, 8000)
    print(port)
    await async_eel.start('index.html', block=False, size=(1000, 600), host='localhost', port=port)  # todo


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


async def window_create(user_id, name, number=None, mode='numbers'):
    """
    Добавляет в таблицу в window_data данные и отображает в html
    """
    # print(user_id, name, number, mode)
    window_data[mode].append(f'<a href="https://vk.com/id{user_id}">{name}</a> - {number}<br>')
    # numbers.append(f'<a href="https://vk.com/id{user_id}">{name}</a> - {number}<br>')
    await async_eel.createDiv()()


async def window_update(user_id, name, number='', mode='numbers'):
    text = f'<a href="https://vk.com/id{user_id}">{name}</a> - {number}<br>'
    window_data[mode].append(text)
    if WINDOW_MODE == mode:
        await async_eel.updateDiv(text, 'elem0')()


@async_eel.expose
async def window_return(mode):
    # print(mode)
    global WINDOW_MODE
    WINDOW_MODE = mode
    return ''.join(window_data[mode])


@async_eel.expose()
async def color_change(color):
    if colors[color]:
        colors[color] = False
    else:
        colors[color] = True


count = 0


async def run(sign, text, color, full=False):
    if colors[color]:
        if full:
            await async_eel.addText(
                f'<span style="color: {color}">{sign}{text}</span>')()
        else:
            await async_eel.addText(
                f'<span style="color: {color}">{sign}</span> {text}')()


async def interface(sign, text, color, full=False):
    await run(sign, text, color, full)
