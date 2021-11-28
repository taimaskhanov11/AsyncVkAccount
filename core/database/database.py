import asyncio
import datetime
import os
import random
import statistics
import time
from multiprocessing import Process
from threading import Thread

from peewee import *

from settings import async_time_track, time_track

db_dir = os.path.join(os.path.dirname(__file__), 'users.db')

db = SqliteDatabase(db_dir)


def time_track1(func):
    def surrogate(*args, **kwargs):
        started_at = time.time()

        result = func(*args, **kwargs)

        ended_at = time.time()
        # elapsed = round(ended_at - started_at, 5)
        elapsed = ended_at - started_at
        print(f'Execution time: {elapsed} s')
        return elapsed

    return surrogate


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


class BaseModel(Model):
    class Meta:
        database = db


class Numbers(BaseModel):
    user_id = IntegerField(unique=True)
    name = CharField(default='')
    city = CharField(default='')
    number = CharField(default='')
    date = DateTimeField(default=datetime.datetime.now().replace(microsecond=0))

    @classmethod
    @async_time_track
    async def get_user(cls, user_id):
        return cls.get(user_id=user_id)

    @classmethod
    @async_time_track
    async def change_value(cls, user_id, title, value):
        user = await cls.get_user(user_id)
        setattr(user, title, value)
        user.save()

    @classmethod
    @async_time_track
    async def create_user(cls, user_id, name, city, number):
        user, created = cls.get_or_create(user_id=user_id, name=name, city=city, number=number)


class Users(BaseModel):
    user_id = IntegerField(unique=True)
    state = IntegerField(default=1)
    name = CharField(default='')
    city = CharField(default='')
    blocked = BooleanField(default=False)
    joined_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    # @classmethod
    # @async_time_track
    # async def get(cls, **kwargs):
    #     return super(Users, cls).get( **kwargs)


    @classmethod
    @async_time_track
    async def get_user(cls, user_id):
        return cls.get(user_id=user_id)

    # @classmethod
    # @async_time_track
    # async def create(cls, **kwargs):
    #     return super(Users, cls).create(**kwargs)

    @classmethod
    @async_time_track
    async def change_value(cls, user_id, title, value):
        user = await cls.get_user(user_id)
        setattr(user, title, value)
        user.save()

    @classmethod
    @async_time_track
    async def get_value(cls, user_id, title):
        user = await cls.get_user(user_id)
        return getattr(user, title)

    @classmethod
    @async_time_track
    async def get_ref_count(cls, user_id):
        user = await cls.get_user(user_id)
        return user.ref

    @classmethod
    @async_time_track
    async def user_exists(cls, user_id):
        query = cls().select().where(cls.user_id == user_id)
        print(query)
        return query.exists()

    @classmethod
    @async_time_track
    async def create_user(cls, user_id, name, city, state, status=True):
        user, created = cls.get_or_create(user_id=user_id, state=state, name=name, city=city, type=status)

    @classmethod
    @async_time_track
    async def add_state(cls, user_id):
        user = cls.get(user_id=user_id)
        user.state += 1
        user.save()


def create_users_dict():
    pass


def run():
    count = 1
    print(count)
    while True:
        Users.add_state(1234)
        count += 1
        print(count)


# print()

# grandmaster = Users(name="22", user_id=123, type = True)
# grandmaster.save()
def check():
    for i in Users.select():
        # print(i.value)
        print(i.user_id)
        print(i.state)
        print(i.name)
        print(i.city)
        print(i.type)


def probe(x):
    print(x, "запущен")
    Users.add_state(x)


@time_track1
def probe2():
    for i in range(1000):
        Users.create(user_id=i, type=True)
    for i in range(1000):
        user = Users.get(user_id=i)
        user.delete_instance()


@time_track1
def runner():
    # now = time.time()

    # workers = [Process(target=probe, args=(i,)) for i in range(100)]
    workers = [Thread(target=probe, args=(i,)) for i in range(100)]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    # print('Общее время выполнения', time.time() - now)


if __name__ == '__main__':
    db.create_tables([Users, Numbers])
    # Numbers.create_user(random.randint(1, 1000), '2', '3')
    user = Users.get(user_id=1)

    now = time.time()
    # asyncio.run(probe2())
    all_time = []
    for i in range(10):
        res = probe2()
        all_time.append(res)
    # print()
    # runner()
    print('Общее время выполнения', time.time() - now)
    print('Среднее время выполнения', statistics.mean(all_time))

# for i in range(10):
#     Users.create_user(i, 2, 'qasd', 'afasdf')
# print(Users.user_exists(1234))

# Users.create_user(1234, 2, 'qasd', 'afasdf')
# todo добавить асинхронность
