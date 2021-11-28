import datetime
import os
import random
import time
from multiprocessing import Process
from threading import Thread

from peewee import *

from settings import async_time_track, time_track

pg_db = PostgresqlDatabase('vk_controller', user='postgres', password='postgres',
                           host='localhost', port=5432)


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


class BaseModel(Model):
    class Meta:
        database = pg_db


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
    type = BooleanField()

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
        user = await cls.get_user(user_id)
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


@time_track
def probe2():
    for i in range(100):
        Users.create_user(i, f'ALi{i}', f'alicity{i}', 1, random.choice([True, False]))


@time_track
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
    pg_db.create_tables([Users, Numbers])
    # Numbers.create_user(random.randint(1, 1000), '2', '3')

    # now = time.time()
    # probe2()
    # runner()
    # print('Общее время выполнения', time.time() - now)

# for i in range(10):
#     Users.create_user(i, 2, 'qasd', 'afasdf')
# print(Users.user_exists(1234))

# Users.create_user(1234, 2, 'qasd', 'afasdf')
# todo добавить асинхронность
