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

from core.classes import BaseUser, ResponseTimeTrack
from core.classes.message_handler import MessageHandler
from core.context.log_message import LogMessage
from core.database import Account, Input, Message, Users, init_tortoise
from core.handlers.log_handler import log_handler
from core.handlers.text_handler import text_handler
from core.log_settings import exp_log, not_answer_log
from core.utils import find_most_city, search_answer
from core.validators import Validator
from settings import *
from settings import message_config

colorama_init()

__all__ = [
    'ResponseTimeTrack',
    'AdminAccount',
    'upload_all_data_main',
]


class AdminAccount:
    """Котролирует все процессы над аккаунтом"""

    def __init__(self, vk_token, tg_token, tg_user_id):
        """
        :param vk_token: Токен аккаунта вк для создания сессии
        :param tg_token: Токен телеграмма для отправки номеров
        :param tg_user_id: Идентификатор, куда отправляются номера
        """
        self.token = vk_token
        self.loop = asyncio.get_event_loop()
        # self.driver = HttpDriver(loop=loop) if loop else None
        self.session = TokenSession(self.token)
        self.vk = API(self.session)
        self.tg_bot = Bot(token=tg_token)
        self.tg_user_id = tg_user_id

        self.users_objects = {}
        self.verified_users = []
        self.unverified_users = []
        self.verifying_users = []

        self.validator = Validator()
        self.logger = LogMessage()  # todo

        self.longpoll = UserLongPoll(self.vk, mode=1, version=3)
        self.users_block = collections.defaultdict(int)
        self.DEFAULT_EVENT_CLASS = Event
        self.info = None
        self.db_account = None  # init in get_self_info
        self.signal_end = False
        self.start_status = True

        self.state_answer_count = len(conversation_stages) + 4

        self.block_message_count = message_config['block_message_count']
        self.delay_for_users = (message_config['delay_response_from'], message_config['delay_response_to'])
        self.delay_typing = (message_config['delay_typing_from'], message_config['delay_typing_to'])
        self.delay_for_acc = message_config['delay_between_messages_for_account']

        self.message_handler = MessageHandler(self)

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
        res = await self.vk.users.get(user_ids=user_id,
                                      fields='sex, bdate, has_photo, city, photo_max_orig')
        return res[0]

    async def get_friend_info(self, user_id: int) -> dict:
        return await self.vk.friends.search(user_id=user_id, fields="sex, city", count=1000)

    def user_info_view(self, info, count_friend, age, has_photo):
        text_handler(signs['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}", 'warning')
        text_handler(signs['yellow'], f"{count_friend} - Количество друзей", 'warning')
        text_handler(signs['yellow'], f'Возраст - {age}', 'warning')
        text_handler(signs['yellow'], f'Фото {has_photo}', 'warning')

    async def get_self_info(self):
        try:
            res = await self.vk.users.get(fields=['photo_max_orig'])
            self.info = res[0]
            db_account = await Account.get_or_create(
                user_id=self.info['id'], defaults={
                    'token': self.token,
                    'first_name': self.info['first_name'],
                    'last_name': self.info['last_name'],
                    'photo_url': self.info['photo_max_orig']
                },
            )
            self.db_account = db_account[0]
            text_handler(signs['version'], f'{self.info["first_name"]} {self.info["last_name"]}', color='yellow')
        except VkAuthError as e:
            await asyncio.gather(
                asyncio.to_thread(self.block_account_message),
                asyncio.to_thread(exp_log.error, e)
            )
            exit()

    def parse_event(self, raw_event: list) -> Event:
        return self.DEFAULT_EVENT_CLASS(raw_event)

    async def create_answer(self, text: str, auth_user: BaseUser, table_user: Users) -> None:
        """Формирование ответа пользователю"""
        template = await auth_user.act(text)  # todo
        if template:
            # answer = await Input.find_output(text, auth_user.city)
            answer = await search_answer(text, auth_user.city)
            if not answer:
                await asyncio.to_thread(
                    not_answer_log.warning, f'{auth_user.user_id} {auth_user.name} --> {text}'
                )

            current_answer = f'{answer} {template}'
            answer = answer or '<ответ не найден>'
            # Создание сообщения
            self.loop.create_task(self.message_handler.send_delaying_message(auth_user, current_answer))

        else:
            answer = 'Игнор/Проверка на номер'
            template = 'Игнор/Проверка на номер'
            await asyncio.to_thread(text_handler, signs['red'],
                                    f"{auth_user.user_id} / {auth_user.name}"
                                    f" / Стадия 7 или больше / Игнор / Проверка на номер ",
                                    'error')

        await self.message_handler.save_message(table_user, text, answer, template)

    def block_account_message(self):
        text_handler(signs['red'], 'Ошибка авторизации!!!', 'error')
        text_handler(signs['yellow'], 'Возможно вы ввели неправильный токен или аккаунт ЗАБЛОКИРОВАН!', 'error',
                     color='red')
        text_handler(signs['version'], f'Ваш токен {self.token}',
                     'error', color='red')

    async def update_users(self, user_id: int,
                           first_name: str,
                           last_name: str,
                           mode: bool = True, city: str = 'None',
                           photo_url: str = 'Нет фото') -> tuple[BaseUser, Users]:  # todo убрать
        """Создание объекта пользователя и сохранение в бд"""
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

    async def check_signals(self):
        while True:
            await asyncio.sleep(5)

            await self.db_account.refresh_from_db(fields=['start_status'])
            if self.start_status:
                if not self.db_account.start_status:
                    self.start_status = False
            else:
                if self.db_account.start_status:
                    self.start_status = True

    async def check_friend_status(self, user_id: int, name: str, can_access_closed: bool) -> bool:
        """Проверка статуса дружбы"""
        add_status = await self.vk.friends.areFriends(user_ids=user_id)
        add_status = add_status[0]['friend_status']

        await asyncio.to_thread(text_handler, signs['yellow'], f"Статус дружбы {add_status}", 'warning')

        if add_status == 2:
            await asyncio.gather(
                self.vk.friends.add(user_id=user_id),
                asyncio.to_thread(
                    text_handler, signs['yellow'], f"Добавление в друзья", 'warning'
                )
            )
            return True
        if not can_access_closed:
            self.users_block[user_id] += 1
            if self.users_block[user_id] > 1:
                return False

            match add_status:
                case 0:
                    asyncio.create_task(
                        self.message_handler.unverified_delaying_message(
                            user_id, name, random.choice(ai_logic['private']['выход'])
                        )
                    )
                case 1:
                    asyncio.create_task(
                        self.message_handler.unverified_delaying_message(
                            user_id, name, ai_logic['просьба принять заявку']['выход']
                        )
                    )

            return False
        return True

    def blacklist_message(self, auth_user: BaseUser, text: str) -> None:
        text_handler(signs['red'],
                     f'Новое сообщение от {auth_user.name}/Черный список/: {text}',
                     'error')

    async def create_response(self, text: str, user_id: int) -> None:
        """Идентификация и обработка пользователя"""
        auth_user = self.users_objects[user_id]
        db_user = await Users.get(user_id=auth_user.user_id)  # todo
        if auth_user.state > self.state_answer_count:
            self.unverified_users.append(auth_user.user_id)
            await asyncio.gather(
                Users.block_user(auth_user.user_id),
                asyncio.to_thread(self.blacklist_message, auth_user, text)
            )

        elif auth_user.block_template < self.block_message_count:
            await asyncio.gather(
                self.create_answer(text, auth_user, db_user),  # Создание ответа
                asyncio.to_thread(text_handler, signs['green'],
                                  f'Новое сообщение от {auth_user.name} / {user_id} - {text}',
                                  'info')  # todo
            )

        else:
            await asyncio.gather(
                asyncio.to_thread(text_handler, signs['yellow'],
                                  f'Новое сообщение от {auth_user.name} /{user_id}/SPAM  - {text}',
                                  'warning'),  # todo
                self.message_handler.save_message(db_user, text, 'блок', 'блок')
            )

    async def verify_user(self, user_id, text) -> bool | tuple[BaseUser, Users]:
        """Валидация и создание пользователя"""
        user_info = await self.get_user_info(user_id)
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        photo_url = user_info.get('photo_max_orig', 'без фото')
        pprint(user_info)
        await asyncio.to_thread(text_handler, signs['green'],
                                f'Новое сообщение от {first_name}/{user_id}/Нету в базе - {text}',
                                'warning')

        # todo if all(map(lambda x: x(), [func1, func2]))
        friend_status = await self.check_friend_status(user_id, first_name, user_info["can_access_closed"])
        if not friend_status:
            return False

        friend_list = await self.get_friend_info(user_id)
        valid = await asyncio.to_thread(
            self.validator.validate, friend_list, user_info
        )
        if valid:
            # поиск города
            city = find_most_city(friend_list)
            auth_user, table_user = await self.update_users(user_id, first_name, last_name, city=city,
                                                            photo_url=photo_url)

            await asyncio.to_thread(text_handler, signs['mark'],
                                    f'{user_id} / {first_name} / Прошел все проверки / Добавлен в verified_users',
                                    'info')

            return auth_user, table_user
        else:
            await asyncio.gather(
                self.update_users(user_id, first_name, last_name, mode=False, photo_url=photo_url),
                asyncio.to_thread(text_handler,
                                  signs['red'],
                                  f'{user_id}/{first_name}/Проверку не прошел/Добавлен в unverified_users',
                                  'error')
            )
            return False

    async def event_analysis(self, event: Event) -> None:
        """Разбор события"""
        text = event.text.lower()
        user_id = event.user_id

        while user_id in self.verifying_users:  # Ожидаем завершения проверки
            await asyncio.gather(
                asyncio.to_thread(
                    text_handler, signs['time'], f'Ожидаем завершения проверки {user_id} 1 sec', 'warning', 'cyan'
                ),
                asyncio.sleep(1)
            )

        res_time_track = ResponseTimeTrack(user_id)

        if user_id in self.unverified_users:
            auth_user = self.users_objects[user_id]
            table_user = await Users.get(user_id=auth_user.user_id)  # todo
            await asyncio.gather(
                self.message_handler.save_message(table_user, text, 'ЧС', 'ЧС'),  # todo
                asyncio.to_thread(self.blacklist_message, auth_user, text)
            )

        elif user_id in self.verified_users:
            await self.create_response(text, user_id)  # Создание ответа
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

    async def parse_message_event(self):
        async for event_a in self.longpoll.iter():
            if self.signal_end:
                print(f'{self.info["first_name"]} Остановка цикла событий!')
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

        text_handler(signs['queue'], f'Текущий цик событий {asyncio.get_event_loop()}', color='magenta')
        text_handler(signs['queue'], f'Текущий поток {multiprocessing.current_process()}, {threading.current_thread()}',
                     color='magenta')  # todo
        await self.get_self_info()

        # print(self.info)
        asyncio.create_task(self.message_handler.run_worker())  # Запуск обработчтк сообщений

        while True:
            try:
                await self.parse_message_event()

                while self.signal_end:
                    await asyncio.sleep(5)

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
