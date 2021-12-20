import asyncio
import random
import re

from core.database import Number, DbUser
from settings import conversation_stages


# class TransparentUser:
#
#     def __init__(self):
#         pass
#

class BaseUser:
    def __init__(self, user_id: int, db_user: DbUser, overlord, state: int, name: str, city: str):
        self.overlord = overlord
        self.log = self.overlord.log
        self.db_user = db_user
        self.user_id = user_id
        self.state = state
        self.name = name
        self.city = city

        self.len_template = len(conversation_stages)
        self.conversation_stages = conversation_stages
        self.half_template = self.len_template // 2
        self.block_template = 0
        self.last_answer_time = 0

    # def __str__(self):
    #     return self.name

    async def add_state(self) -> None:
        self.state += 1
        await DbUser.add_state(self.user_id)

    async def send_number(self, text: str) -> None:
        await self.overlord.send_number_tg(
            f'бот {self.overlord.first_name} {self.overlord.info["last_name"]}\n'
            f"Полученные данные:\n"
            f"name      {self.name}\n"
            f"id        {self.user_id}\n"
            f"url       https://vk.com/id{self.user_id}\n"
            f"number    {text}"
        ),

    async def number_success(self, text):
        self.log('number_success', self.user_id, self.name, text)
        await asyncio.gather(
            Number.create(account=self.overlord.db_account,
                          user=self.db_user, number=text),
            DbUser.blocking(self.user_id),
            self.send_number(text)
        )
        self.overlord.unverified_users.append(self.user_id)  # todo

    async def act(self, text: str):
        await self.add_state()
        if self.state >= self.half_template:
            result = re.findall(r"\d{4,}", text)
            if result:
                await self.number_success(text)
                return False

            if self.state >= self.len_template + 1:
                return False
            res = random.choice(self.conversation_stages[f"state{self.state}"])
            return res

        else:
            res = random.choice(self.conversation_stages[f"state{self.state}"])
            return res
