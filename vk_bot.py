import asyncio
import collections
import multiprocessing
import random
import threading

from aiogram import Bot
from aiovk import API, TokenSession
from aiovk.exceptions import VkAuthError
from aiovk.longpoll import UserLongPoll
from colorama import init as colorama_init
from vk_api.longpoll import Event, VkEventType

from core.classes import BaseUser, TimeTrack
from core.classes.session_user import SessionUser
from core.database.models import DbAccount, DbUser
from core.database.tortoise_db import init_tortoise
from core.handlers.log_message import LogMessage
from core.message_handler import MessageHandler
from core.utils.find_most_city import find_most_city
from core.validators import MessageValidator, UserValidator
from settings import *

colorama_init()

__all__ = [
    'TimeTrack',
    'AdminAccount',
]


class AdminAccount:
    """Котролирует все процессы над аккаунтом"""

    def __init__(
            self,
            vk_token: str,
            tg_token: str,
            tg_user_id: int,
            log_message: LogMessage
    ) -> None:
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
        self.longpoll = UserLongPoll(self.api, mode=1, version=3)

        self.tg_bot = Bot(token=tg_token)
        self.tg_user_id = tg_user_id

        self.block_message_count = message_config['block_message_count']
        self.delay_for_users = (message_config['delay_response_from'], message_config['delay_response_to'])
        self.delay_typing = (message_config['delay_typing_from'], message_config['delay_typing_to'])
        self.delay_for_acc = message_config['delay_between_messages_for_account']
        self.state_answer_count = len(conversation_stages) + 4
        self.friend_status_0 = ai_logic['private']['выход']
        self.friend_status_1 = ai_logic['просьба принять заявку']['выход']

        self.users_objects = {}
        self.authenticated_users = []
        self.banned_users = []
        self.under_consideration_user = []

        self.validator = UserValidator(self)
        self.message_validator = MessageValidator(bad_words)

        self.log = log_message  # todo
        self.message_handler = MessageHandler(self)

        self.users_block = collections.defaultdict(int)
        self.DEFAULT_EVENT_CLASS = Event

        self.info = None
        self.first_name = None
        self.user_id = None

        self.db_account = None  # init in get_self_info
        self.signal_end = False
        self.start_status = True

    def __str__(self):
        return self.first_name

    async def unloading_from_database(self):  # todo
        """Выгружает пользователей из базы в переменную"""
        users_all = await DbUser.all()
        for db_user in users_all:
            _id = db_user.user_id
            self.users_objects[_id] = BaseUser(_id, db_user, self, db_user.state, db_user.first_name, db_user.city)
            if db_user.blocked:
                self.banned_users.append(_id)
            else:
                self.authenticated_users.append(_id)

    async def send_number_tg(self, text: str) -> None:
        """Отправка полученного номера в телеграмм по id"""
        await self.tg_bot.send_message(self.tg_user_id, text)

    async def get_user_info(self, user_id: int) -> dict:
        # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
        res = await self.api.users.get(user_ids=user_id,
                                       fields='sex, bdate, has_photo, city, photo_max_orig')
        return res[0]

    async def get_friend_info(self, user_id: int) -> dict:
        return await self.api.friends.search(user_id=user_id, fields="sex, city", count=1000)

    async def check_and_get_self_info(self):
        try:
            res = await self.api.users.get(fields=['photo_max_orig'])
            self.info = res[0]
            db_account = await DbAccount.get_or_create(
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
            self.log('self_info', f'{self.info["first_name"]} {self.info["last_name"]}')
            return True

        except VkAuthError as e:
            self.log('token_error', f'Ошибка токена {self.token} | {e}')
            return False

    def parse_event(self, raw_event: list) -> Event:
        return self.DEFAULT_EVENT_CLASS(raw_event)

    def template_valid(self, auth_user, text, template):
        # answer = await Input.find_output(text, auth_user.city) #todo поиск через Таблицу
        # answer, attachment = await search_answer(text, auth_user.city)
        answer, attachment = self.message_handler.search_answer(text, auth_user.city)
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

    async def create_answer(self, text: str,
                            auth_user: BaseUser,
                            table_user: DbUser) -> None:
        """Формирование ответа пользователю"""
        template = await auth_user.act(text)  # todo

        if template:
            answer, current_answer, attachment = self.template_valid(auth_user, text, template)
            # Создание сообщения
            self.loop.create_task(self.message_handler.send_delaying_message(auth_user, current_answer, attachment))
        else:
            answer, attachment, template = self.template_invalid(auth_user.user_id, auth_user.name)
        await self.message_handler.save_message(table_user, text, f'{answer}>{attachment}', template)

    async def update_users(self, user_id: int,
                           first_name: str,
                           last_name: str,
                           mode: bool = True, city: str = 'None',
                           photo_url: str = 'Нет фото') -> tuple[BaseUser, DbUser]:  # todo убрать

        """Создание объекта пользователя и сохранение в бд"""

        db_user = await DbUser.create(
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
        self.authenticated_users.append(user_id) if mode else self.banned_users.append(user_id)
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

    async def add_to_blacklist(self, user_id: int):
        self.banned_users.append(user_id)
        await DbUser.blocking(user_id)

    async def create_response(self, su) -> None:
        """Идентификация и обработка пользователя"""

        auth_user: BaseUser = self.users_objects[su.user_id]
        db_user: DbUser = await DbUser.get(user_id=auth_user.user_id)  # todo

        # Проверка на запрещенные слова
        if self.message_validator.check_for_bad_words(su.text):
            await self.add_to_blacklist(su.user_id)
            self.log('bad_word', auth_user.name, su.user_id)

        # Проверка на стадию разговора, если больше - в черный список
        elif auth_user.state > self.state_answer_count:
            await self.add_to_blacklist(su.user_id)
            self.log('blacklist_message', auth_user.name, su.text)

        # Проверка на частоту сообщений если меньше self.block_message_count - отвечает
        elif auth_user.block_template < self.block_message_count:
            self.log('auth_user_message', auth_user.name, su.user_id, su.text)
            await self.create_answer(su.text, auth_user, db_user)  # Создание ответа

        else:
            # Проверка на частоту сообщений если больше self.block_message_count - игнорит
            await self.message_handler.save_message(db_user, su.text, 'блок', 'блок')
            self.log('spam_message', auth_user.name, su.user_id, su.text)

    async def user_is_valid(self, city, user_id, first_name, last_name, photo_url):
        auth_user, table_user = await self.update_users(user_id, first_name, last_name, city=city,
                                                        photo_url=photo_url)
        self.log('verification_successful', user_id, first_name)
        return auth_user, table_user

    async def user_is_invalid(self, user_id, first_name, last_name, photo_url):
        await self.update_users(user_id, first_name, last_name, mode=False, photo_url=photo_url)
        self.log('verification_failed', user_id, first_name)
        return False

    async def verify_user(self, user_id: int, text: str) -> bool | tuple[BaseUser, DbUser]:
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
            city = find_most_city(friend_list)  # todo
            return await self.user_is_valid(city, user_id, first_name, last_name, photo_url)
        else:
            return await self.user_is_invalid(user_id, first_name, last_name, photo_url)

    async def wait_for_authentication(self, su, delay: int) -> None:
        self.log('wait_for_verification', su.user_id, delay)
        await asyncio.sleep(delay)  # todo

    async def for_unverified_users(self, session_user):
        auth_user = self.users_objects[session_user.user_id]
        table_user = await DbUser.get(user_id=auth_user.user_id)  # todo
        await self.message_handler.save_message(table_user, session_user.text, 'ЧС', 'ЧС'),  # todo
        self.log('blacklist_message', auth_user.name, session_user.text)

    async def identification(self, su) -> None:

        self.under_consideration_user.append(su.user_id)
        # await asyncio.sleep(2)
        verified = await self.verify_user(su.user_id, su.text)

        if verified:
            await self.create_answer(su.text, *verified)
        self.under_consideration_user.remove(su.user_id)

    async def event_analysis(self, event: Event) -> None:
        """Разбор события"""
        su = SessionUser(
            event.user_id, event.text.lower(), self
        )

        # text = event.text.lower()
        # user_id = event.user_id

        # user = self.users_objects.get(su.user_id) #todo
        #
        # match user:
        #     case BannedUser:
        #         pass
        #     case AuthUser:
        #         pass
        res_time_track = TimeTrack(su, self.log)  # todo

        # Ожидаем завершения проверки
        if su in self.under_consideration_user:
            await self.wait_for_authentication(su, 2)

        if su in self.banned_users:
            await self.for_unverified_users(su)

        elif su in self.authenticated_users:
            # Создание ответа
            await self.create_response(su)
            res_time_track.stop()

        else:
            # Если нету в базе
            await self.identification(su)

        res_time_track.stop(check=True)

    async def parse_message_event(self):
        self.log('parse_message_event', self.first_name)
        async for event_a in self.longpoll.iter():
            if not self.start_status:
                # Остановка парсинга при отключении статуса
                self.log('stopping_loop', self.first_name)
                break

            if event_a[0] != 4:
                continue

            event = self.DEFAULT_EVENT_CLASS(event_a)
            # print(event)
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                # Создания задачи Анализ события
                self.loop.create_task(self.event_analysis(event))

    async def run_session(self):
        """Запуст и выгрузка основных данных"""

        # Инициализация базы данных
        await init_tortoise(*db_config.values())  # todo 26.01.2022 14:09 taima: вынести в общий

        if not await self.check_and_get_self_info():
            return False

        # Выгрузка пользователей
        await self.unloading_from_database()

        self.log('process_info',
                 self.first_name,
                 str(self.loop),
                 str(multiprocessing.current_process()),
                 str(threading.current_thread()))

        # Выгрузка фото
        await self.message_handler.uploaded_photo_from_dir()
        self.log('photos_uploaded', self.first_name)

        # Запуск проверки сигнала запуска
        self.loop.create_task(self.signal_checking())

        while True:
            try:
                # Запуск обработчика сообщений
                self.loop.create_task(self.message_handler.run_worker())

                # Запуск обработчика сообщений через db
                self.loop.create_task(self.message_handler.run_db_worker())

                # Парс события
                await self.parse_message_event()

                while not self.start_status:
                    await asyncio.sleep(5)

            except VkAuthError as e:
                self.log('acc_block_error', e, self.token)
                await DbAccount.blocking(self.user_id)
                return

            except Exception as e:
                self.log('auth_error', e)
            # finally:
            #     await self.session.close()
            finally:
                await self.session.close()

                # Создание новой сессии
                self.session = TokenSession(self.token)
                self.api = API(self.session)
                self.longpoll = UserLongPoll(self.api, mode=1, version=3)

# log_handler.init_choice_logging(__name__,
#                                 *__all__)
