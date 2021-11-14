import asyncio
import datetime
import inspect
import random
from pprint import pprint

import peewee as pw
from peewee_async import Manager, PostgresqlDatabase
from settings import async_time_track, time_track

postgre_db = PostgresqlDatabase('vk_controller', user='postgres', password='postgres',
                                             host='localhost', port=5432)


class TimeTrackMeta(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        pprint(attrs)

        for key, val in attrs.items():
            if inspect.isfunction(val):
                if key in ('__init__', 'act', 'parse_event', 'start_send_message', 'send_status_tg'):
                    continue
                # print(val)
                if asyncio.iscoroutinefunction(val):
                    print('async', val)
                    attrs[key] = async_time_track(val)
                else:
                    print('sync', val)
                    attrs[key] = time_track(val)
        return super().__new__(mcs, name, bases, attrs, **kwargs)


class BaseModel(pw.Model):
    class Meta:
        database = postgre_db


class Numbers(BaseModel):
    user_id = pw.IntegerField(unique=True)
    name = pw.CharField(default='')
    city = pw.CharField(default='')
    number = pw.CharField(default='')
    date = pw.DateTimeField(default=datetime.datetime.now().replace(microsecond=0))
    created_at = pw.DateTimeField(default=datetime.datetime.now())

    @classmethod
    @async_time_track
    async def get_user(cls, user_id):
        res = await async_db.get(cls, user_id=user_id)
        return res

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
    user_id = pw.IntegerField(unique=True)
    state = pw.IntegerField(default=1)
    name = pw.CharField(default='')
    city = pw.CharField(default='')
    blocked = pw.BooleanField(default=False)
    joined_at = pw.DateTimeField(default=datetime.datetime.now())
    updated_at = pw.DateTimeField(default=datetime.datetime.now())

    @classmethod
    @async_time_track
    async def get_user(cls, user_id):
        res = await async_db.get(cls, user_id=user_id)
        return res
        # return cls.get(user_id=user_id)

    @classmethod
    @async_time_track
    async def change_value(cls, user_id, title, value):
        user = await cls.get_user(user_id)
        setattr(user, title, value)
        await async_db.update(user)
        # user.save()

        # user = await cls.get_user(user_id)
        # setattr(user, title, value)
        # user.save()

    @classmethod
    @async_time_track
    async def get_value(cls, user_id, title):
        user = await cls.get_user(user_id)
        return getattr(user, title)

    @classmethod
    @async_time_track
    async def user_exists(cls, user_id):
        query = await async_db.execute(cls().select().where(cls.user_id == user_id))
        return query.exists()

        # query = cls().select().where(cls.user_id == user_id)
        # print(query)
        # return query.exists()

    @classmethod
    @async_time_track
    async def create_user(cls, user_id, name, city, state, blocked=False):
        user, created = await async_db.get_or_create(Users, user_id=user_id, state=state, name=name, city=city,
                                                     blocked=blocked)
        # user, created = await async_db.get_or_create(cls, user_id=user_id, state=state, name=name, city=city,
        #                                              blocked=blocked)
        return user
        # user, created = cls.get_or_create(user_id=user_id, state=state, name=name, city=city, type=status)

    @classmethod
    @async_time_track
    async def add_state(cls, user_id):
        user = await cls.get_user(user_id)
        user.state += 1
        await async_db.update(user)
        # user.save()


postgre_db.create_tables([Users, Numbers])
postgre_db.close()
async_db = Manager(postgre_db)
# pg_db.set_allow_sync(False)
async_db.database.allow_sync = False


async def test_func():
    # user, created = await async_db.create(Users, user_id=131232, name='Олег', city='Moscow')
    # user = await async_db.create(Users, user_id=131232, name='Олег', city='Moscow')
    user = await async_db.create_or_get(Users, user_id=131232, name='Олег', city='Moscow')
    # user = Users.create(user_id=13123, state=2, name='Олег', city='Moscow')
    print(user)
    # await Users.create_user(13123, 'Олег', 'Moscow', 0)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_func())
    # asyncio.run(test_func())
    pass

# todo добавить асинхронность
