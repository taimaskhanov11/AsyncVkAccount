import asyncio
import datetime
import inspect
import json
import random
import statistics
import time

from pathlib import Path

from aiocache import cached, Cache

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


class Category(Model):
    title = fields.CharField(max_length=255, unique=True, index=True)

    @classmethod
    def create_from_dict(cls):
        pass

    @classmethod
    def view(cls, title):
        category = cls.get(title=title)
        return category.title, (
            tuple(input_.text for input_ in category.input), tuple(output.text for output in category.output)
        )


class Input(Model):
    category = fields.ForeignKeyField('models.Category', related_name='input')
    text = fields.CharField(index=True, max_length=255)

    @classmethod
    def create_from_dict(cls):
        pass

    @classmethod
    @async_time_track
    # @cached(ttl=60, cache=Cache.MEMORY) #todo
    async def find_output(cls, text, city):
        # res = await cls.filter(text__in = text)
        # print(text.split())
        answer_data = await cls.all().select_related('category')
        answer_end = ''
        try:
            for field in answer_data:
                if field.text in text:
                    output = await Output.filter(category=field.category)
                    answer = random.choice(output).text
                    if field.category.title == 'город':
                        answer.format(city)
                    answer_end += answer + ','
            answer_end = answer_end[0:-1]
            print('answer in find_output', answer_end)
            return answer_end
        except Exception as e:
            print(e)
            return False

    # @classmethod
    # # @time_track
    # @async_time_track  # todo
    # # @cachetools.cached(cache=cachetools.TTLCache(maxsize=20, ttl=60))
    # async def find_answer(cls, text, city):
    #     res = await cls.find_output(text)
    #     return res

        # if field.category.title == 'город': #todo
        #     answer.format(city or TALK_DICT_ANSWER_ALL['негород']['выход'])
        #


class Output(Model):
    category = fields.ForeignKeyField('models.Category', related_name='output')
    text = fields.TextField()

    @classmethod
    def create_from_dict(cls):
        pass


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

@async_time_track
async def init_tortoise():
    await Tortoise.init( #todo
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['database.apostgresql_tortoise_db']}
    )
    # await Tortoise.init( #todo
    #     db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
    #     modules={'models': ['database.apostgresql_tortoise_db']}
    # )
    # await Tortoise.init(
    #     db_url='postgres://bcuoknoutrikhk:94fd296ff056160bf19a70efd4f9b855d4b8a0b50ad1902156735414563252de@localhost:5432/d9gvn77ajkr6cp',
    #     modules={'models': ['database.apostgresql_tortoise_db']}
    # )

    # await Tortoise.generate_schemas()


async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    # also specify the app name of "models"
    # which contain models from "app.models"
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['__main__']}
    )
    print('init()')
    # await main()
    conn = Tortoise.get_connection('default')
    # res = await conn.execute_query('SELECT * FROM input WHERE ')
    res = await conn.execute_query("SELECT * FROM input WHERE text = %s", ["a"])
    print(res)
    print('a')
    await Input.find_output('прив', 'a')
    # Generate the schema
    # await Tortoise.generate_schemas()


async def speed_test_create_delete():
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['__main__']}
    )

    # answer_data = await Input.all().select_related('category')
    # res = await Input.find_output('привет')
    # res2 = await Input.find_output('привет')
    res = Input.find_answer('привет', 'GER')
    print(res)

    # answer_data = await Input.all().select_related('category')
    # print(answer_data)
    # print(answer_data[0].category.title)
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
    with open(Path(BASE_DIR.parent.parent, 'config/answers.json'), 'r', encoding='utf-8-sig') as ff:
        data = json.load(ff)
    # print(data)
    for category_title, answers in data.items():
        category = await Category.get_or_create(title=category_title)
        category = category[0]
        print(category)
        # exit()
        # print(category)
        # category = Category.create(title=category_title)
        for input_text in answers['вход']:
            await Input.get_or_create(category=category, text=input_text)
            # Input.get_or_create(category=category, category_title=category, text=input_text)
            # Input.create(category=category, text=input_text)
        for output_text in answers['выход']:
            await Output.get_or_create(category=category, text=output_text)


async def heroku_init():
    await Tortoise.init(
        db_url='postgres://bcuoknoutrikhk:94fd296ff056160bf19a70efd4f9b855d4b8a0b50ad1902156735414563252de@ec2-63-34-223-144.eu-west-1.compute.amazonaws.com:5432/d9gvn77ajkr6cp',
        modules={'models': ['__main__']}
    )
    await Tortoise.generate_schemas()




# asyncio.run(test())
if __name__ == '__main__':
    # run_async(init())
    # run_async(speed_test_create_delete())
    run_async(heroku_init())
    pass
# loop = asyncio.new_event_loop()
# loop.run_until_complete(main())
# run_async(main())
