import asyncio
import random

from core.classes import BaseUser
from core.database import Message, Users
from core.handlers import text_handler
from settings import signs


class MessageHandler(asyncio.Queue):
    """
    Контролирует все процессы с полученными сообщениями
    """
    def __init__(self, overlord):  # todo
        super().__init__()
        self.overlord = overlord

    async def run_worker(self):
        await asyncio.to_thread(
            text_handler, signs['sun'], 'Обработчик сообщений запущен!', color='blue'
        )
        while True:
            # Вытаскиваем сообщение из очереди.
            user_id, name, text = await self.get()

            # Общее время между сообщениями, включает и время печатания
            await asyncio.gather(
                self.send_message(user_id, text),
                asyncio.to_thread(
                    text_handler, signs['message'],
                    f'Сообщение пользователю {name} c тексом: `{text}`\nОтправлено ⇑',
                    'info', 'blue'
                ),
                asyncio.to_thread(
                    text_handler, signs['queue'],
                    f'Ожидание очереди. Тайминг {self.overlord.delay_for_acc} s',
                    'info', 'cyan'
                ),
                asyncio.sleep(self.overlord.delay_for_acc)
            )

            self.task_done()
            self.overlord.users_objects[user_id].block_template = 0  # снятие блока после обработки
            # Проверка сигнала завершения
            if self.empty():
                if self.overlord.signal_end:
                    await asyncio.to_thread(text_handler, signs['yellow'], 'Завершение обработчика!')
                    break

    async def send_message(self, user_id: int, message: str) -> None:
        await self.overlord.vk.messages.setActivity(user_id=user_id, type='typing')
        await asyncio.sleep(random.randint(*self.overlord.delay_typing))

        await self.overlord.vk.messages.send(user_id=user_id,
                                             message=message,
                                             random_id=0)

    async def send_delaying_message(self, auth_user: BaseUser, text: str):
        """Создание отложенного сообщения"""
        auth_user.block_template += 1
        # рандомный сон
        random_sleep_answer = random.randint(*self.overlord.delay_for_users)
        await asyncio.sleep(random_sleep_answer)
        # todo доделать last_answer_time
        await self.put((auth_user.user_id, auth_user.name, text))

    async def save_message(self, table_user: Users, text: str,
                           answer_question: str, answer_template: str) -> None:
        """Сохрание сообщения в базе данных"""
        await Message.create(
            account=self.overlord.db_account,
            user=table_user,
            text=text,
            answer_question=answer_question,
            answer_template=answer_template,
        )
