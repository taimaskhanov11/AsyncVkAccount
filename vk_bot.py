import asyncio
import collections
import multiprocessing
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import telebot
from aiovk import API, TokenSession
from aiovk.exceptions import VkAuthError
from aiovk.longpoll import UserLongPoll
from colorama import init as colorama_init
from tqdm import trange
from vk_api.longpoll import Event, VkEventType

from core.classes import BaseUser, ResponseTimeTrack
from core.context.log_message import LogMessage
from core.database import Account, Input, Message, Users, init_tortoise
from core.handlers.log_handler import log_handler
from core.handlers.text_handler import text_handler
from core.log_settings import exp_log, not_answer_log
from core.utils import find_most_city
from core.validators import (age_validator, count_friends_validator,
                             mens_validator, photo_validator)
from settings import *

colorama_init()

__all__ = [
    'ResponseTimeTrack',
    'VkUserControl',
    'upload_all_data_main',
]


class VkUserControl:
    validators = (photo_validator, age_validator, count_friends_validator, mens_validator)

    def __init__(self, vk_token):
        self.token = vk_token
        self.loop = asyncio.get_event_loop()
        # self.driver = HttpDriver(loop=loop) if loop else None
        self.session = TokenSession(self.token)
        self.tg_bot = telebot.TeleBot(settings['telegram_token'])
        self.vk = API(self.session)

        self.users_objects = {}
        self.verified_users = []
        self.unverified_users = []

        self.verifying_users = []

        self.logger = LogMessage()  # todo

        self.longpoll = UserLongPoll(self.vk, mode=1, version=3)
        self.users_block = collections.defaultdict(int)
        self.DEFAULT_EVENT_CLASS = Event
        self.info = None
        self.table_account = None  # init in get_self_info
        self.executor = ThreadPoolExecutor()
        self.signal_end = False
        self.start_status = True

        self.state_answer_count = len(conversation_stages) + 4
        self.block_message_count = settings['block_message_count']
        self.delay_for_users = (settings['delay_response_from'], settings['delay_response_to'])
        self.delay_typing = (settings['delay_typing_from'], settings['delay_typing_to'])
        self.delay_for_acc = settings['delay_between_messages_for_account']

        self.message_queue = asyncio.Queue()

    async def unloading_from_database(self):  # todo
        users_all = await Users.all()
        for user in users_all:
            _id = user.user_id
            self.users_objects[_id] = BaseUser(_id, user.state, user.name, user.city)
            if user.blocked:
                self.unverified_users.append(_id)
            else:
                self.verified_users.append(_id)

    def send_status_tg(self, text: str) -> None:
        print('отправка')
        self.tg_bot.send_message(settings['user_id'], text)

    async def get_user_info(self, user_id: int) -> dict:
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.vk.users.get(user_ids=user_id,
                                      fields='sex, bdate, has_photo, city')
        return res[0]

    async def send_message(self, user_id: int, text: str) -> None:
        await self.vk.messages.setActivity(user_id=user_id, type='typing')
        await asyncio.sleep(random.randint(*self.delay_typing))

        await self.vk.messages.send(user_id=user_id,
                                    message=text,
                                    random_id=0)

    async def get_friend(self, user_id):
        return await self.vk.friends.search(user_id=user_id, fields="sex, city", count=1000)

    def check_and_add_friend(self, user_id):  # todo
        pass

    def user_info_view(self, info, count_friend, age, has_photo):
        text_handler(signs['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}", 'warning')
        text_handler(signs['yellow'], f"{count_friend} - Количество друзей", 'warning')
        text_handler(signs['yellow'], f'Возраст - {age}', 'warning')
        text_handler(signs['yellow'], f'Фото {has_photo}', 'warning')

    async def get_self_info(self):
        res = await self.vk.users.get(fields=['photo_max_orig'])
        self.info = res[0]
        table_account = await Account.get_or_create(
            user_id=self.info['id'], defaults={
                'token': self.token,
                'name': self.info['first_name']
            },
        )
        self.table_account = table_account[0]

    def parse_event(self, raw_event) -> Event:
        return self.DEFAULT_EVENT_CLASS(raw_event)

    async def send_delaying_message(self, auth_user: BaseUser, text: str):
        auth_user.block_template += 1
        # рандомный сон
        random_sleep_answer = random.randint(*self.delay_for_users)
        await asyncio.sleep(random_sleep_answer)
        # todo доделать last_answer_time
        await self.message_queue.put((auth_user.user_id, auth_user.name, text))

    async def create_answer(self, text: str, auth_user: BaseUser, table_user: Users):

        template = await auth_user.act(text, self)  # todo
        if template:
            answer = await Input.find_output(text, auth_user.city)
            if not answer:
                await asyncio.to_thread(
                    not_answer_log.warning, f'{auth_user.user_id} {auth_user.name} --> {text}'
                )

            current_answer = f'{answer} {template}'
            answer = answer or '<ответ не найден>'

            asyncio.create_task(self.send_delaying_message(auth_user, current_answer))

        else:
            answer = 'Игнор/Проверка на номер'
            template = 'Игнор/Проверка на номер'
            await asyncio.to_thread(text_handler(signs['red'],
                                                 f"{auth_user.user_id} / {auth_user.name} / Стадия 7 или больше / Игнор / Проверка на номер ",
                                                 'error'))

        await self.save_message(table_user, text, answer, template)

    def block_account_message(self):
        text_handler(signs['red'], 'Ошибка авторизации!!!', 'error')
        text_handler(signs['yellow'], 'Возможно вы ввели неправильный токен или аккаунт ЗАБЛОКИРОВАН!', 'error',
                     color='red')
        text_handler(signs['version'], f'Ваш токен {self.token}',
                     'error', color='red')

    async def update_users(self, user_id, name, mode=True, city=None):  # todo убрать
        table_user = await Users.create(account=self.table_account, user_id=user_id, name=name, city=city)
        self.users_objects[user_id] = BaseUser(user_id, 0, name, city)
        self.verified_users.append(user_id) if mode else self.unverified_users.append(user_id)
        return self.users_objects[user_id], table_user

    # todo проверка состояния
    def create_signals_thread(self, func, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(*args))

    async def check_signals(self):
        while True:
            await asyncio.sleep(5)

            await self.table_account.refresh_from_db(fields=['start_status'])
            if self.start_status:
                if not self.table_account.start_status:
                    self.start_status = False
            else:
                if self.table_account.start_status:
                    self.start_status = True

    async def check_friend_status(self, user_id: int, can_access_closed: bool) -> bool:
        add_status = await self.vk.friends.areFriends(user_ids=user_id)
        add_status = add_status[0]['friend_status']

        await asyncio.to_thread(text_handler, signs['yellow'], f"Статус дружбы {add_status}", 'warning')

        if add_status == 2:
            await asyncio.gather(
                asyncio.to_thread(
                    text_handler, signs['yellow'], f"Добавление в друзья", 'warning'
                ),
                self.vk.friends.add(user_id=user_id)
            )
            return True
        if not can_access_closed:
            match add_status:
                case 0:
                    await self.send_message(user_id, random.choice(
                        ai_logic['private']['выход']))
                case 1:
                    await self.send_message(user_id, "было бы круто если бы ты принял заявку в друзья &#128522;")
            return False
        return True

    async def check_user_validity(self, user_id, info, name) -> bool | tuple[BaseUser, Users]:
        friend_list = await self.get_friend(user_id)
        m_f_count = [i['sex'] for i in friend_list['items']]
        female, male, age = m_f_count.count(1), m_f_count.count(2), info.get('bdate')
        has_photo, count_friend = info['has_photo'], friend_list['count']
        await asyncio.to_thread(self.user_info_view, info, count_friend, age, has_photo)

        valid = await self.all_validators(has_photo, age, count_friend, (male, female, count_friend), )
        if valid:
            # поиск города
            city = find_most_city(friend_list)
            auth_user, table_user = await self.update_users(user_id, name, city=city)

            await asyncio.to_thread(text_handler, signs['mark'],
                                    f'{user_id} / {name} / Прошел все проверки / Добавлен в users',
                                    'info')

            return auth_user, table_user
        else:
            await asyncio.gather(
                self.update_users(user_id, name, False),
                asyncio.to_thread(text_handler,
                                  signs['red'],
                                  f'{user_id} {name} Проверку не прошел / Добавлен в unusers',
                                  'error')
            )
            return False

    async def save_message(self, table_user: Users, text: str, answer_question: str, answer_template: str) -> None:
        await Message.create(
            account=self.table_account,
            user=table_user,
            text=text,
            answer_question=answer_question,
            answer_template=answer_template,
        )

    def blacklist_message(self, auth_user: BaseUser, text: str) -> None:
        text_handler(signs['red'],
                     f'Новое сообщение от {auth_user.name}/Черный список/: {text}',
                     'error')

    async def create_response(self, text: str, user_id: int) -> None:
        auth_user = self.users_objects[user_id]
        table_user = await Users.get(user_id=auth_user.user_id)  # todo
        if auth_user.state > self.state_answer_count:
            self.unverified_users.append(auth_user.user_id)
            await asyncio.gather(
                Users.block_user(auth_user.user_id),
                asyncio.to_thread(self.blacklist_message, auth_user, text)
            )

        elif auth_user.block_template < self.block_message_count:
            await asyncio.gather(
                self.create_answer(text, auth_user, table_user),
                asyncio.to_thread(text_handler(signs['green'],
                                               f'Новое сообщение от {auth_user.name} / {user_id} - {text}',
                                               'info'))  # todo
            )

        else:
            await asyncio.gather(
                asyncio.to_thread(text_handler, signs['yellow'],
                                  f'Новое сообщение от {auth_user.name} /{user_id}/SPAM  - {text}',
                                  'warning'),  # todo
                self.save_message(table_user, text, 'блок', 'блок')
            )

    async def verify_user(self, user_id, text) -> bool | tuple[BaseUser, Users]:
        info = await self.get_user_info(user_id)
        name = info['first_name']

        await asyncio.to_thread(text_handler, signs['green'],
                                f'Новое сообщение от {name}/{user_id}/Нету в базе - {text}',
                                'warning')

        can_access_closed = info["can_access_closed"]

        # todo if all(map(lambda x: x(), [func1, func2]))
        friend_status = await self.check_friend_status(user_id, can_access_closed)
        if not friend_status:
            return False

        validate = await self.check_user_validity(user_id, info, name)
        if not validate:
            return False

        return validate

    async def run(self, event: Event) -> None:
        text = event.text.lower()
        user_id = event.user_id

        while user_id in self.verifying_users:  # Ожидаем завершения проверки
            print('Ждем')
            await asyncio.sleep(1)

        res_time_track = ResponseTimeTrack(user_id)

        if user_id in self.unverified_users:
            auth_user = self.users_objects[user_id]
            table_user = await Users.get(user_id=auth_user.user_id)  # todo
            await asyncio.gather(
                self.save_message(table_user, text, 'ЧС', 'ЧС'),  # todo
                asyncio.to_thread(self.blacklist_message, auth_user, text)
            )

        elif user_id in self.verified_users:
            await self.create_response(text, user_id)
            res_time_track.stop()

        else:
            # Если нету в базе
            self.verifying_users.append(user_id)
            # await asyncio.sleep(2)
            verified = await self.verify_user(user_id, text)
            if verified:
                await self.create_answer(text, *verified)
            self.verifying_users.remove(user_id)

        res_time_track.stop(check=True)

    async def worker(self):
        await asyncio.to_thread(
            text_handler, signs['sun'], 'Обработчик сообщений запущен!', color='blue'
        )
        while True:
            # Вытаскиваем 'рабочий элемент' из очереди.
            user_id, name, text = await self.message_queue.get()

            # Общее время между сообщениями включает и время печатания
            await asyncio.gather(
                self.send_message(user_id, text),
                asyncio.to_thread(
                    text_handler, signs['message'],
                    f'Сообщение пользователю {name} c тексом: `{text}`\nОтправлено ⇑',
                    'info', 'blue'
                ),
                asyncio.to_thread(
                    text_handler, signs['queue'],
                    f'Ожидание очереди. Тайминг {self.delay_for_acc} s',
                    'info', 'cyan'
                ),
                asyncio.sleep(self.delay_for_acc)
            )

            self.message_queue.task_done()
            self.users_objects[user_id].block_template = 0  # снятие блока после обработки

            # Проверка сигнала завершения
            if self.message_queue.empty():
                if self.signal_end:
                    await asyncio.to_thread(text_handler, signs['yellow'], 'Завершение обработчика!')
                    break

    async def run_session(self):

        # Инициализация базы данных
        await init_tortoise()
        # Выгрузка пользователей
        await self.unloading_from_database()

        print('Текущий цик событий', asyncio.get_event_loop())
        print('Текущий поток', multiprocessing.current_process(), threading.current_thread())  # todo

        try:
            await self.get_self_info()
        except VkAuthError as e:
            print(e)
            await asyncio.gather(
                asyncio.to_thread(self.block_account_message),
                asyncio.to_thread(exp_log.error, e)
            )
            exit()

        # func = lambda x, *args: Thread(target=self.create_signals_thread, args=(x, *args,)).start()
        # func(self.check_signals, self.info['id'])
        # self.message_loop.run()

        asyncio.create_task(self.worker())

        print(self.info['first_name'], self.info['last_name'])
        while True:
            try:
                async for event_a in self.longpoll.iter():
                    # print(event_a)
                    if event_a[0] != 4:
                        continue

                    event = self.parse_event(event_a)
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                        self.loop.create_task(self.run(event))
                        if self.signal_end:
                            # self.message_queue.empty()
                            print('Закрытие цикла событий')
                            asyncio.get_event_loop().close()
                            # break

            except VkAuthError as e:
                exp_log.error(e)
                await asyncio.gather(asyncio.to_thread(self.block_account_message),
                                     Account.blocking(self.info['id']), return_exceptions=True)
                return

            except Exception as e:
                await asyncio.gather(
                    asyncio.to_thread(text_handler, signs['red'], 'ПЕРЕПОДКЛЮЧЕНИЕ...', 'error'),
                    asyncio.to_thread(exp_log.warning, e)
                )

    async def all_validators(self, *args):
        tasks = [asyncio.to_thread(func, arg) for func, arg in zip(self.validators, args)]
        res = await asyncio.gather(*tasks, return_exceptions=True)
        # print(res)
        if all(res):
            return True
        return False


# @log_handler
async def upload_all_data_main(statusbar=False):
    """Инициализация данных профиля и сохранений в базе"""
    try:

        text_handler(f"VkBot v{bot_version}", '', color='blue')

        text_handler(signs['magenta'], f'Загруженно токенов {len(tokens)}: ', color='magenta')
        for a, b in enumerate(tokens, 1):
            text_handler(signs['magenta'], f"    {b}", color='magenta')

        delay = f"[{settings['delay_response_from']} - {settings['delay_response_to']}] s"
        text_handler(signs['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{settings['delay_typing_from']} - {settings['delay_typing_to']}] s"
        text_handler(signs['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        # Выгрузка стадий и юзеров
        # await unloading_from_database()

        # todo
        text_handler(signs['magenta'], 'Проверка прокси:', color='magenta')
        for proxy in settings['proxy']:
            text_handler(signs['magenta'], '    PROXY {proxy} IS WORKING'.format(proxy=proxy))
        time.sleep(1)

        if statusbar:
            for i in trange(300, colour='green', smoothing=0.1, unit_scale=True):
                time.sleep(0.001)
        # if is_bad_proxy(proxy):
        #     await TextHandler(SIGNS['magenta'], f"    BAD PROXY {proxy}", log_type='error', full=True)
        # else:
        #     await TextHandler(SIGNS['magenta'], '    PROXY {proxy} IS WORKING')
    except Exception as e:
        exp_log.exception(e)


log_handler.init_choice_logging(__name__,
                                *__all__)
