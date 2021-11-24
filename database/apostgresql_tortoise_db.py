import asyncio
import datetime
import inspect
import json
import random
import statistics
import time
from pathlib import Path

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model

from settings import async_time_track, log

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

@log
class Category(Model):
    title = fields.CharField(max_length=255, unique=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_category"

    @classmethod
    def create_from_dict(cls):
        pass

    @classmethod
    def view(cls, title):
        category = cls.get(title=title)
        return category.title, (
            tuple(input_.text for input_ in category.input), tuple(output.text for output in category.output)
        )

@log
class Input(Model):
    category = fields.ForeignKeyField('models.Category', related_name='input')
    text = fields.CharField(index=True, max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_input"

    @classmethod
    def create_from_dict(cls):
        pass

    @classmethod
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
            # print('answer in find_output', answer_end)
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


@log
class Output(Model):
    category = fields.ForeignKeyField('models.Category', related_name='output')
    text = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_output"

    @classmethod
    def create_from_dict(cls):
        pass

@log
class Numbers(Model):
    user_id = fields.IntField(unique=True, index=True)
    name = fields.CharField(default='', max_length=100)
    city = fields.CharField(default='', max_length=100)
    number = fields.CharField(default='', max_length=100)
    date = fields.DatetimeField(default=datetime.datetime.now().replace(microsecond=0))
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_numbers"

    def __str__(self):
        return self.name

    @classmethod
    async def change_value(cls, user_id, title, value):
        user = await cls.get(user_id=user_id)
        setattr(user, title, value)
        await user.save()


@log
class Users(Model):
    account = fields.ForeignKeyField('models.Account', related_name='users')
    user_id = fields.IntField(unique=True, index=True)
    state = fields.IntField(default=0)
    name = fields.CharField(default='default', max_length=100)
    city = fields.CharField(default='default', max_length=100)
    blocked = fields.BooleanField(default=False)
    joined_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now_add=True)  # todo

    class Meta:
        table = "app_vk_controller_user"

    def __str__(self):
        return self.name

    @classmethod
    async def add_state(cls, user_id):
        user = await cls.get(user_id=user_id)
        user.state += 1
        await user.save()
        return user.state

    @classmethod
    async def change_value(cls, user_id, title, value):
        user = await cls.get(user_id=user_id)
        setattr(user, title, value)
        await user.save()


class Message(Model):
    user = fields.ForeignKeyField('models.Users', related_name='messages', index=True)
    account = fields.ForeignKeyField('models.Account', related_name='messages', index=True)
    sent_at = fields.DatetimeField(auto_now_add=True)
    text = fields.TextField()
    answer_question = fields.TextField()
    answer_template = fields.TextField()

    class Meta:
        table = "app_vk_controller_message"


#
class Account(Model):
    token = fields.CharField(max_length=255)
    name = fields.CharField(max_length=255)
    user_id = fields.IntField(index=True, unique=True)
    blocked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    start_status = fields.BooleanField(default=True)

    class Meta:
        table = "app_vk_controller_account"

    @classmethod
    async def blocking(cls, user_id):
        account = await cls.get(user_id=user_id)
        account.blocked = True
        await account.save()


@async_time_track
async def init_tortoise():
    await Tortoise.init(  # todo
        # db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        db_url='postgres://postgres:postgres@localhost:5432/django_db',
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


async def test2():
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        modules={'models': ['__main__']}
    )
    # await Tortoise.generate_schemas()
    # await Output.create()
    # await main()
    # ou = await Output.get(id=1)
    # ou.text = 'привет привеееет'
    # await ou.save()
    # print(ou.text)


async def djagno_init():
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/django_db',
        modules={'models': ['__main__']}
    )
    await Tortoise.generate_schemas()


# asyncio.run(test())
if __name__ == '__main__':
    run_async(test2())
    run_async(djagno_init())
    # Account.default_connection()
    # Tortoise.
    # run_async(speed_test_create_delete())
    # run_async(heroku_init())
    pass
# loop = asyncio.new_event_loop()
# loop.run_until_complete(main())
# run_async(main())
