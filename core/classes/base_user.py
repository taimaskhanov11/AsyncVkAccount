import asyncio
import datetime
import random
import re

import pandas as pd

from core.database import Numbers, Users
from core.handlers import text_handler
from settings import conversation_stages, signs


class BaseUser:
    def __init__(self, user_id, overlord, state, name, city):
        self.overlord = overlord
        self.user_id = user_id
        self.state = state
        self.name = name
        self.city = city

        self.len_template = len(conversation_stages)
        self.half_template = self.len_template // 2
        self.block_template = 0
        self.last_answer_time = 0

    def append_to_exel(self, user_id, text, name):  # todo убрать
        time = datetime.datetime.now().replace(microsecond=0)
        excel_data_df = pd.read_excel("username.xlsx")
        data = pd.DataFrame(
            {
                "UserID": [user_id],
                "Name": [name],
                "Url": [f"https://vk.com/id{user_id}"],
                "Number": [text],
                "Date": [time],
            }
        )
        res = excel_data_df.append(data)
        res.to_excel("username.xlsx", index=False)
        # print(res)
        return data

    async def add_state(self):
        self.state += 1
        await Users.add_state(self.user_id)

    async def number_success(self, text):
        await asyncio.gather(
            # todo добавлять в таблицу
            # Numbers.create(user_id=self.user_id, name=self.name, city=self.city, number=text),
            Users.change_value(self.user_id, "blocked", True),
            # asyncio.to_thread(self.append_to_exel, self.user_id, text, self.name),
            asyncio.to_thread(
                text_handler,
                signs["mark"],
                f"{self.user_id} / {self.name} Номер получен добавление в unverified_users",
            ),
            asyncio.to_thread(
                text_handler,
                signs["tg"],
                f"Отправка данных пользователя {self.name} в telegram",
                "warning",
                color="blue",
            ),
            self.overlord.send_status_tg(
                f'бот {self.overlord.info["first_name"]} {self.overlord.info["last_name"]}\n'
                f"Полученные данные:\n"
                f"name      {self.name}\n"
                f"id        {self.user_id}\n"
                f"url       https://vk.com/id{self.user_id}\n"
                f"number    {text}"
            ),
        )
        self.overlord.unverified_users.append(self.user_id)  # todo

    async def act(self, text: str):
        await self.add_state()
        if self.state >= self.half_template:
            result = re.findall("\d{4,}", text)
            if result:
                await self.number_success(text)
                return False

            # print(self.len_template)
            if self.state >= self.len_template + 1:
                return False
            res = random.choice(conversation_stages[f"state{self.state}"])
            return res

        else:
            res = random.choice(conversation_stages[f"state{self.state}"])
            return res
