import asyncio
import os
import random
from pathlib import Path

import requests
from vk_api.upload import FilesOpener

from core.classes import BaseUser
from core.database import Message, Users
from core.handlers import text_handler
from core.log_settings import exp_log
from settings import signs, ai_logic

BASE_DIR = Path(__file__).parent.parent.parent
IMAGE_DIR = Path(BASE_DIR, 'config/image')


# print(list(os.walk(IMAGE_DIR)))
# print(Path(IMAGE_DIR, '2.jpg'))


class MessageHandler(asyncio.Queue):
    """
    Контролирует все процессы с полученными сообщениями
    """

    def __init__(self, overlord):  # todo
        super().__init__()
        self.overlord = overlord
        self.log = self.overlord.log
        self.delay = self.overlord.delay_for_acc

        self.http = requests.Session()
        self.http.headers.pop('user-agent')

        self.photos = {}

    def waiting_message(self, name, text):
        text_handler(signs['message'],
                     f'Сообщение пользователю {name} c тексом: `{text[:40]}...` ⇑Отправлено',
                     'info', 'blue')

        text_handler(signs['queue'],
                     f'Ожидание очереди. Тайминг {self.overlord.delay_for_acc} s\n',
                     'info', 'cyan')

    async def run_worker(self):
        self.log('run_worker_start', self.overlord.first_name)

        while True:
            # Вытаскиваем сообщение из очереди.
            user_id, name, text, attachment = await self.get()
            attach_text = f'{text}>{attachment}'
            # Общее время между сообщениями, включает и время печатания

            self.log('waiting_message', name, attach_text, self.delay)
            await asyncio.gather(
                self.send_message(user_id, text, attachment),
                asyncio.sleep(self.overlord.delay_for_acc)
            )

            self.task_done()
            self.overlord.users_objects[user_id].block_template = 0  # снятие блока после обработки
            # Проверка сигнала завершения
            if self.empty():
                if not self.overlord.start_status:
                    self.log('run_worker_end', self.overlord.first_name)
                    break

    def search_answer(self, text: str, city: str):  # todo
        """
        Конвертирование разных по структуре но одинаковых
        по значению слов к общему по значению слову
        """
        answer_end = ''
        attachments = ''
        try:
            for a, b in ai_logic.items():
                if any(token in text for token in b["вход"]):
                    answer: str = random.choice(b['выход'])
                    if a == 'город':
                        # answer = answer.format(city)
                        answer = answer.format(city or ai_logic['негород']['выход'])
                    elif a == 'отправка фото':
                        if not attachments:
                            answer, attach = answer.split('>')
                            attachments = self.photos.get(attach)
                            # answer.format(city or ai_logic['негород']['выход'])
                    answer_end += answer + ','
            answer_end = answer_end[0:-1]
            return answer_end, attachments
        except Exception as e:
            exp_log.error(e)
            return False

    async def uploaded_photo_from_dir(self) -> dict:
        # dir_photos = [c for _, _, c in os.walk(IMAGE_DIR)]
        dir_photos = list(os.walk(IMAGE_DIR))[0][2]
        url_photos = await self.uploaded_photo(*dir_photos)
        photos_attachments = [f'photo{ph["owner_id"]}_{ph["id"]}' for ph in url_photos]
        res = dict(zip(dir_photos, photos_attachments))
        self.photos = res
        text_handler(signs['version'], f'{self.overlord.info["first_name"]} | Фото выгружены', color='black')
        return res

    async def uploaded_photo(self, *images):
        """Выгрузка своего фото на сервер"""

        photos = [str(Path(IMAGE_DIR, im)) for im in images]
        album = await self.overlord.api('photos.getMessagesUploadServer')
        url = album['upload_url']
        with FilesOpener(photos) as photo_files:
            response = self.http.post(url, files=photo_files)
        photos = await self.overlord.api('photos.saveMessagesPhoto', **response.json())
        return [{'id': im['id'], 'owner_id': im['owner_id'], 'access_key': im['access_key']} for im in photos]

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

    async def send_delaying_message(self, auth_user: BaseUser, text: str, attachment: str) -> None:
        """Создание отложенного сообщения"""
        auth_user.block_template += 1
        # рандомный сон
        random_sleep_answer = random.randint(*self.overlord.delay_for_users)
        await asyncio.sleep(random_sleep_answer)
        # todo доделать last_answer_time
        await self.put((auth_user.user_id, auth_user.name, text, attachment))

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
