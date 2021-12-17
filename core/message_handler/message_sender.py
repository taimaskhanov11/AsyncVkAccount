import asyncio
import random

from core.classes import BaseUser
from core.database.apostgresql_tortoise_db import SendMessage


class MessageSender(asyncio.Queue):
    """
    Контролирует все процессы с отправкой сообщений
    """

    def __init__(self, overlord):  # todo
        super().__init__()
        self.overlord = overlord
        self.log = self.overlord.log
        self.delay = self.overlord.delay_for_acc

    async def run_worker(self):
        self.log('run_worker_start', self.overlord.first_name)
        while True:

            # Вытаскиваем сообщение из очереди.
            user_id, name, text, attachment = await self.get()
            attach_text = f'{text}>{attachment}'

            self.log('waiting_message', name, attach_text, self.delay)
            # Общее время между сообщениями, включает и время печатания
            await asyncio.gather(
                self.send_message(user_id, text, attachment),
                asyncio.sleep(self.delay)
            )
            self.task_done()

            # снятие блока после обработки
            self.overlord.users_objects[user_id].block_template = 0

            # Проверка сигнала завершения
            if self.empty():
                if not self.overlord.start_status:
                    self.log('run_worker_end', self.overlord.first_name)
                    break

    async def run_db_worker(self):
        self.log('message_db_worker_start', self.overlord.first_name)
        while True:

            await asyncio.sleep(3)
            # Вытаскиваем сообщение из очереди.
            messages = await SendMessage.all().select_related('user')

            # Отправка сообщения
            for message in messages:
                await self.send_message(message.user.user_id, message.text),
                self.log('db_message_send', message.user.first_name, message.text, self.delay)

            # Проверка сигнала завершения
            if self.empty():
                if not self.overlord.start_status:
                    self.log('message_db_end', self.overlord.first_name)
                    break



    async def send_delaying_message(self, auth_user: BaseUser, text: str, attachment: str) -> None:
        """Создание отложенного сообщения"""
        auth_user.block_template += 1
        # рандомный сон
        random_sleep_answer = random.randint(*self.overlord.delay_for_users)
        await asyncio.sleep(random_sleep_answer)
        # todo доделать last_answer_time
        await self.put((auth_user.user_id, auth_user.name, text, attachment))

    async def send_message(self, user_id: int, message: str, attachment: str = None) -> None:
        await self.overlord.api.messages.setActivity(user_id=user_id, type='typing')
        await asyncio.sleep(random.randint(*self.overlord.delay_typing))
        await self.overlord.api.messages.send(user_id=user_id,
                                              message=message,
                                              attachment=attachment,
                                              random_id=0)

    async def unverified_delaying(self, user_id, name, text):  # todo name
        random_sleep_answer = random.randint(*self.overlord.delay_for_users)
        await asyncio.sleep(random_sleep_answer)
        await self.send_message(user_id, text)
        self.log('message_send_success', name, text)
