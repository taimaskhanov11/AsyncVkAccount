import asyncio
import datetime
import inspect
import random
import statistics
import time
from pathlib import Path
from pprint import pprint

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model

from settings import async_time_track, time_track
BASE_DIR = Path(__file__)

def async_time_track1(func):
    async def surrogate(*args, **kwargs):
        started_at = time.time()

        result = await func(*args, **kwargs)

        ended_at = time.time()
        # elapsed = round(ended_at - started_at, 5)
        elapsed = ended_at - started_at
        print(f'Execution time: {elapsed} s')
        return elapsed

    return surrogate


class Numbers(Model):
    user_id = fields.IntField(unique=True, index=True)
    name = fields.CharField(default='', max_length=100)
    city = fields.CharField(default='', max_length=100)
    number = fields.CharField(default='', max_length=100)
    date = fields.DatetimeField(default=datetime.datetime.now().replace(microsecond=0))
    created_at = fields.DatetimeField(default=datetime.datetime.now())

    def __str__(self):
        return self.name

    @classmethod
    @async_time_track
    async def change_value(cls, user_id, title, value):
        user = await cls.get(user_id=user_id)
        setattr(user, title, value)
        await user.save()


class Users(Model):
    user_id = fields.IntField(unique=True)
    state = fields.IntField(default=1)
    name = fields.CharField(default='default', max_length=100)
    city = fields.CharField(default='default', max_length=100)
    blocked = fields.BooleanField(default=False)
    joined_at = fields.DatetimeField(default=datetime.datetime.now())
    updated_at = fields.DatetimeField(default=datetime.datetime.now())

    def __str__(self):
        return self.name

    @classmethod
    @async_time_track
    async def add_state(cls, user_id):
        user = await cls.get(user_id=user_id)
        user.state += 1
        await user.save()
        return user.state

    @classmethod
    @async_time_track
    async def change_value(cls, user_id, title, value):
        user = await cls.get(user_id=user_id)
        setattr(user, title, value)
        await user.save()

async def init_tortoise():

    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['database.apostgresql_tortoise_db']}
    )



async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    # also specify the app name of "models"
    # which contain models from "app.models"
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['__main__']}
    )
    print('init()')
    await main()
    # Generate the schema
    # await Tortoise.generate_schemas()


async def speed_test_create_delete():
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['__main__']}
    )
    await probe2()
    # for i in range(1000):
    #     await Users.create(user_id=i, blocked=True)
    # for i in range(1000):
    #     user = Users.get(user_id=i)
    #     user.delete_instance()


@async_time_track1
async def probe2():
    for i in range(1000):
        # await Users.create(user_id=i, type=True)
        user = await Users.create(user_id=i, type=True)
        print(user)
    for i in range(1000):
        user = Users.get(user_id=i)
        # user.state += 1

        await user.delete()


async def test():
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['__main__']}
    )
    now = time.time()
    all_time = []
    for i in range(10):
        res = await probe2()
        all_time.append(res)

    print('Общее время выполнения', time.time() - now)
    print('Среднее время выполнения', statistics.mean(all_time))


async def main():
    pass
    # event = await Users.create(user_id=123123)
    # event = await Users.create(user_id=123123)
    # Users.get()
    # event = await Users(user_id=1231233)
    # event = await Users.add_state(user_id=1231233)
    # print(event)
    # user = await Users.get(user_id=1231233)
    # user.state += 1
    # await user.save()


# run_async is a helper function to run simple async Tortoise scripts.

# asyncio.run(test())
if __name__ == '__main__':

    run_async(init())

# loop = asyncio.new_event_loop()
# loop.run_until_complete(main())
# run_async(main())
