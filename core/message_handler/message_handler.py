import asyncio
import random

from core.database import Message, DbUser
from core.log_settings import exp_log
from core.message_handler.message_sender import MessageSender
from core.message_handler.photo_uploader import PhotoUploader
from settings import ai_logic


class MessageHandler(MessageSender, PhotoUploader):
    """
    Контролирует все процессы с получением и отправкой сообщений

    """

    def __init__(self, overlord):  # todo
        super().__init__(overlord)
        PhotoUploader.__init__(self)

    def search_answer(self, text: str, city: str):  # todo
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

    async def save_message(self, table_user: DbUser, text: str,
                           answer_question: str, answer_template: str) -> None:
        """Сохрание сообщения в базе данных"""
        await Message.create(
            account=self.overlord.db_account,
            user=table_user,
            text=text,
            answer_question=answer_question,
            answer_template=answer_template,
        )
