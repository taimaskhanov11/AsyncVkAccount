import asyncio
import collections
import multiprocessing
import random
import threading
import time
from pprint import pprint

from aiogram import Bot
from aiovk import API, TokenSession
from aiovk.exceptions import VkAuthError
from aiovk.longpoll import UserLongPoll

from colorama import init as colorama_init
from tqdm import trange
from vk_api.longpoll import Event, VkEventType

from core.classes import BaseUser, TimeTrack
from core.classes.message_dispatcher import MessageHandler
from core.handlers.log_message import LogMessage
from core.database import Account, Input, Message, Users, init_tortoise
from core.handlers.log_router import log_handler
from core.handlers.text_handler import text_handler
from core.log_settings import exp_log
from core.utils import find_most_city
from core.validators import UserValidator, MessageValidator
from settings import *

colorama_init()

__all__ = [
    'TimeTrack',
    'AdminAccount',
    'upload_all_data_main',
]


class AdminAccount:
    """Котролирует все процессы над аккаунтом"""

    def __init__(self, vk_token: str, tg_token: str, tg_user_id: int, log_collector_queue):
        """
        :param vk_token: Токен аккаунта вк для создания сессии
        :param tg_token: Токен телеграмма для отправки номеров
        :param tg_user_id: Идентификатор, куда отправляются номера
        """
        self.token = vk_token
        self.loop = asyncio.get_event_loop()
        # self.driver = HttpDriver(loop=loop) if loop else None
        self.session = TokenSession(self.token)
        self.api = API(self.session)
        self.tg_bot = Bot(token=tg_token)
        self.tg_user_id = tg_user_id

        self.block_message_count = message_config['block_message_count']
        self.delay_for_users = (message_config['delay_response_from'], message_config['delay_response_to'])
        self.delay_typing = (message_config['delay_typing_from'], message_config['delay_typing_to'])
        self.delay_for_acc = message_config['delay_between_messages_for_account']

        self.users_objects = {}
        self.verified_users = []
        self.unverified_users = []
        self.verifying_users = []

        self.validator = UserValidator()
        self.message_validator = MessageValidator(bad_words)
        # self.logger = LogMessage()  # todo
        self.log = LogMessage(self, log_collector_queue)  # todo
        self.message_handler = MessageHandler(self)

        self.longpoll = UserLongPoll(self.api, mode=1, version=3)
        self.users_block = collections.defaultdict(int)
        self.DEFAULT_EVENT_CLASS = Event
        self.info = None
        self.first_name = None
        self.user_id = None

        self.db_account = None  # init in get_self_info
        self.signal_end = False
        self.start_status = True

        self.friend_status_0 = ai_logic['private']['выход']
        self.friend_status_1 = ai_logic['просьба принять заявку']['выход']

        self.state_answer_count = len(conversation_stages) + 4



    # def __str__(self):
    #     return self.info['first_name']

    async def unloading_from_database(self):  # todo
        """Выгружает пользователей из базы в переменную"""
        users_all = await Users.all()
        for db_user in users_all:
            _id = db_user.user_id
            self.users_objects[_id] = BaseUser(_id, db_user, self, db_user.state, db_user.first_name, db_user.city)
            if db_user.blocked:
                self.unverified_users.append(_id)
            else:
                self.verified_users.append(_id)

    async def send_status_tg(self, text: str) -> None:
        """Отправка полученного номера в телеграмм по id"""
        await self.tg_bot.send_message(self.tg_user_id, text)

    async def get_user_info(self, user_id: int) -> dict:
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.api.users.get(user_ids=user_id,
                                       fields='sex, bdate, has_photo, city, photo_max_orig')
        return res[0]

    async def get_friend_info(self, user_id: int) -> dict:
        return await self.api.friends.search(user_id=user_id, fields="sex, city", count=1000)

    async def get_self_info(self):
        try:
            res = await self.api.users.get(fields=['photo_max_orig'])
            self.info = res[0]
            db_account = await Account.get_or_create(
                user_id=self.info['id'], defaults={
                    'token': self.token,
                    'first_name': self.info['first_name'],
                    'last_name': self.info['last_name'],
                    'photo_url': self.info['photo_max_orig']
                },
            )
            self.first_name = self.info['first_name']
            self.user_id = self.info['id']
            self.db_account = db_account[0]
            self.start_status = self.db_account.start_status
            text_handler(signs['version'], f'{self.info["first_name"]} {self.info["last_name"]}', color='yellow')
        except VkAuthError as e:
            self.block_account_message()
            exp_log.critical(f'Ошибка токена {self.token} | {e}')
            raise

    def parse_event(self, raw_event: list) -> Event:
        return self.DEFAULT_EVENT_CLASS(raw_event)

    def template_valid(self, auth_user, text, template):
        # answer = await Input.find_output(text, auth_user.city)
        # answer, attachment = await search_answer(text, auth_user.city)
        answer, attachment = self.message_handler.search_answer(text, auth_user.city)
        # print(attachment)
        if not answer:
            self.log('no_answer_found', auth_user.user_id, auth_user.name, text)

        current_answer = f'{answer} {template}'
        answer = answer or '<ответ не найден>'
        return answer, current_answer, attachment

    def template_invalid(self, user_id, name):
        answer = 'Игнор/Проверка на номер'
        attachment = ''
        template = 'Игнор/Проверка на номер'
        self.log('template_invalid', user_id, name)
        return answer, attachment, template

    async def create_answer(self, text: str, auth_user: BaseUser, table_user: Users) -> None:
        """Формирование ответа пользователю"""
        # print(text)
        template = await auth_user.act(text)  # todo

        if template:
            answer, current_answer, attachment = self.template_valid(auth_user, text, template)
            # Создание сообщения
            self.loop.create_task(self.message_handler.send_delaying_message(auth_user, current_answer, attachment))
        else:
            answer, attachment, template = self.template_invalid(auth_user.user_id, auth_user.name)
        await self.message_handler.save_message(table_user, text, f'{answer}>{attachment}', template)

    def block_account_message(self):
        text_handler(signs['version'], f'Ошибка токена {self.token}', 'error',
                     color='red')

    async def update_users(self, user_id: int,
                           first_name: str,
                           last_name: str,
                           mode: bool = True, city: str = 'None',
                           photo_url: str = 'Нет фото') -> tuple[BaseUser, Users]:  # todo убрать
        """Создание объекта пользователя и сохранение в бд"""
        # pprint([user_id, first_name, last_name, mode, city, photo_url])
        db_user = await Users.create(
            account=self.db_account,
            user_id=user_id,
            photo_url=photo_url,
            first_name=first_name,
            last_name=last_name,
            city=city,
            blocked=not mode
        )

        user_object = BaseUser(user_id, db_user, self, 0, first_name, city)

        self.users_objects[user_id] = user_object
        self.verified_users.append(user_id) if mode else self.unverified_users.append(user_id)
        return user_object, db_user

    async def signal_checking(self):
        self.log('signal_checking', self.first_name)
        while True:
            await asyncio.sleep(5)
            await self.db_account.refresh_from_db(fields=['start_status'])
            if self.start_status:
                if not self.db_account.start_status:
                    self.start_status = False
            else:
                if self.db_account.start_status:
                    self.start_status = True

    def access_closed(self, user_id, status, name):
        self.users_block[user_id] += 1
        if self.users_block[user_id] > 1:
            return False
        if status == 0:
            asyncio.create_task(self.message_handler.unverified_delaying(
                user_id, name, random.choice(self.friend_status_0))
            )
        elif status == 1:
            asyncio.create_task(self.message_handler.unverified_delaying(
                user_id, name, random.choice(self.friend_status_1))
            )

    async def check_friend_status(self, user_id: int, name: str, can_access_closed: bool) -> bool:
        """Проверка статуса дружбы"""
        status = await self.api.friends.areFriends(user_ids=user_id)
        status = status[0]['friend_status']
        self.log('friend_status', status)

        if status == 2:
            await self.api.friends.add(user_id=user_id)
            self.log('adding_friend', name)
            return True

        if not can_access_closed:
            self.access_closed(user_id, status, name)
            return False

        return True

    def blacklist_message(self, auth_user: BaseUser, text: str) -> None:
        text_handler(signs['red'],
                     f'Новое сообщение от {auth_user.name}/Черный список/: {text}',
                     'error')

    async def add_to_blacklist(self, user_id: int):
        self.unverified_users.append(user_id)
        await Users.block_user(user_id)

    async def create_response(self, user_id: int, text: str) -> None:
        """Идентификация и обработка пользователя"""

        auth_user: BaseUser = self.users_objects[user_id]
        db_user: Users = await Users.get(user_id=auth_user.user_id)  # todo

        # Проверка на запрещенные слова
        if self.message_validator.check_for_bad_words(text):
            await self.add_to_blacklist(user_id)
            self.log('bad_word', auth_user.name, user_id)

        # Проверка на стадию разговора, если больше в черный список
        elif auth_user.state > self.state_answer_count:
            await self.add_to_blacklist(user_id)
            self.log('blacklist_message', auth_user.name, text)

        # Проверка на частоту сообщений если меньше self.block_message_count, отвечаем
        elif auth_user.block_template < self.block_message_count:
            await self.create_answer(text, auth_user, db_user)  # Создание ответа
            self.log('auth_user_message', auth_user.name, user_id, text)

        else:
            # Проверка на частоту сообщений если больше self.block_message_count, игнорим
            await self.message_handler.save_message(db_user, text, 'блок', 'блок')
            self.log('spam_message', auth_user.name, user_id, text)

    async def user_is_valid(self, friend_list, user_id, first_name, last_name, photo_url):
        city = find_most_city(friend_list)
        auth_user, table_user = await self.update_users(user_id, first_name, last_name, city=city,
                                                        photo_url=photo_url)
        self.log('verification_successful', user_id, first_name)
        return auth_user, table_user

    async def user_is_invalid(self, user_id, first_name, last_name, photo_url):
        await self.update_users(user_id, first_name, last_name, mode=False, photo_url=photo_url)
        self.log('verification_failed', user_id, first_name)
        return False

    async def verify_user(self, user_id, text) -> bool | tuple[BaseUser, Users]:
        """Валидация и создание пользователя"""
        user_info = await self.get_user_info(user_id)
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        photo_url = user_info.get('photo_max_orig', 'без фото')
        # pprint(user_info)
        self.log('new_user_message', first_name, user_id, text)

        # todo if all(map(lambda x: x(), [func1, func2]))
        friend_status = await self.check_friend_status(user_id, first_name, user_info["can_access_closed"])
        if not friend_status:
            return False

        friend_list = await self.get_friend_info(user_id)
        valid = await asyncio.to_thread(
            self.validator.validate, friend_list, user_info
        )

        if valid:
            return await self.user_is_valid(friend_list, user_id, first_name, last_name, photo_url)
        else:
            return await self.user_is_invalid(user_id, first_name, last_name, photo_url)

    async def wait_for_verification(self, user_id: int, delay: int) -> None:
        self.log('wait_for_verification', user_id, delay)
        await asyncio.sleep(delay)  # todo

    async def for_unverified_users(self, user_id: int, text: str):
        auth_user = self.users_objects[user_id]
        table_user = await Users.get(user_id=auth_user.user_id)  # todo
        await self.message_handler.save_message(table_user, text, 'ЧС', 'ЧС'),  # todo
        self.log('blacklist_message', auth_user.name, text)

    async def identification(self, user_id: int, text: str) -> None:
        # Если нету в базе
        self.verifying_users.append(user_id)
        # await asyncio.sleep(2)
        verified = await self.verify_user(user_id, text)

        if verified:
            await self.create_answer(text, *verified)
        self.verifying_users.remove(user_id)

    async def event_analysis(self, event: Event) -> None:
        """Разбор события"""

        text = event.text.lower()
        user_id = event.user_id

        if user_id in self.verifying_users:  # Ожидаем завершения проверки
            await self.wait_for_verification(user_id, 2)

        res_time_track = TimeTrack(user_id, self.log)

        if user_id in self.unverified_users:
            await self.for_unverified_users(user_id, text)

        elif user_id in self.verified_users:
            await self.create_response(user_id, text)  # Создание ответа
            res_time_track.stop()

        else:
            await self.identification(user_id, text)

        res_time_track.stop(check=True)

    async def parse_message_event(self):
        async for event_a in self.longpoll.iter():
            if not self.start_status:
                self.log('stopping_loop', self.first_name)
                break

            if event_a[0] != 4:
                continue

            event = self.DEFAULT_EVENT_CLASS(event_a)
            # print(event)
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                self.loop.create_task(self.event_analysis(event))  # Создания задачи Анализ события

    async def run_session(self):
        """Запуст и выгрузка основных данных"""

        # Инициализация базы данных
        await init_tortoise(*db_config.values())

        # Выгрузка пользователей
        await self.unloading_from_database()

        try:
            await self.get_self_info()
        except:
            return
            # print(self.info)

        self.log('process_info',
                 str(self.loop),
                 str(multiprocessing.current_process()),
                 str(threading.current_thread()))

        # Выгрузка фото
        await self.message_handler.uploaded_photo_from_dir()

        # Запуск проверки сигнала запуска
        self.loop.create_task(self.signal_checking())
        # self.log.queue.put(self.first_name)

        while True:

            try:
                self.loop.create_task(self.message_handler.run_worker())  # Запуск обработчика сообщений
                await self.parse_message_event()  # парс события

                while not self.start_status:
                    # print(self.start_status)
                    await asyncio.sleep(5)

            except VkAuthError as e:
                self.log('acc_block_error', e, self.token)
                await Account.blocking(self.user_id)
                return

            except Exception as e:
                self.log('auth_error', e)
            # finally:
            #     await self.session.close()


# @log_handler
def upload_all_data_main(statusbar=False):
    """Инициализация данных профиля и сохранений в базе"""
    try:

        text_handler(f"VkBot v{bot_version}", '', color='blue')
        text_handler(signs['magenta'], f'Загруженно токенов {len(vk_tokens)}: ', color='magenta')
        for a, b in enumerate(vk_tokens, 1):
            text_handler(signs['magenta'], f"    {b}", color='magenta')

        delay = f"[{message_config['delay_response_from']} - {message_config['delay_response_to']}] s"
        text_handler(signs['magenta'], f"    Задержка перед ответом : {delay}", color='cyan')
        delay = f"[{message_config['delay_typing_from']} - {message_config['delay_typing_to']}] s"
        text_handler(signs['magenta'], f"    Длительность отображения печати : {delay}", color='cyan')

        # Выгрузка стадий и юзеров

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
