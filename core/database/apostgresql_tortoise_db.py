import datetime
import json
import random
from pathlib import Path

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model

from core.handlers.log_handler import log_handler

BASE_DIR = Path(__file__)

__all__ = [
    'Tortoise',
    'Category',
    'Input',
    'Output',
    'Numbers',
    'Users',
    'Message',
    'Account',
    'init_tortoise',
]


class Account(Model):
    token = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    user_id = fields.IntField(index=True, unique=True)
    photo_url = fields.TextField(null=True)
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


class Users(Model):
    account = fields.ForeignKeyField('models.Account', on_delete=fields.CASCADE, related_name='users')
    user_id = fields.IntField(unique=True, index=True)
    photo_url = fields.TextField(null=True)
    state = fields.IntField(default=1)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    city = fields.CharField(default='default', max_length=100)
    blocked = fields.BooleanField(default=False)
    joined_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now_add=True)  # todo

    class Meta:
        table = "app_vk_controller_user"

    def __str__(self):
        return self.first_name

    @classmethod
    async def block_user(cls, user_id):
        table_user = await cls.get(user_id=user_id)
        table_user.blocked = True
        await table_user.save()

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


class Numbers(Model):
    account = fields.ForeignKeyField('models.Account', on_delete=fields.CASCADE, related_name='numbers')
    user = fields.OneToOneField('models.Users', on_delete=fields.CASCADE, related_name='number')
    date = fields.DatetimeField(default=datetime.datetime.now().replace(microsecond=0))
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_numbers"

    def __str__(self):
        return self.user.name

    @classmethod
    async def change_value(cls, user_id, title, value):
        user = await cls.get(user_id=user_id)
        setattr(user, title, value)
        await user.save()


class Category(Model):
    title = fields.CharField(max_length=255, unique=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_category"

    @classmethod
    def create_from_dict(cls):
        pass

    @classmethod
    async def view(cls, title):
        category = await cls.get(title=title)
        return category.title, (
            tuple(input_.text for input_ in category.input), tuple(output.text for output in category.output)
        )


class Input(Model):
    category = fields.ForeignKeyField('models.Category', on_delete=fields.CASCADE, related_name='input')
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


class Output(Model):
    category = fields.ForeignKeyField('models.Category', on_delete=fields.CASCADE, related_name='output')
    text = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_output"

    @classmethod
    def create_from_dict(cls):
        pass


class Message(Model):
    user = fields.ForeignKeyField('models.Users', on_delete=fields.CASCADE, related_name='messages', index=True)
    account = fields.ForeignKeyField('models.Account', on_delete=fields.CASCADE, related_name='messages', index=True)
    sent_at = fields.DatetimeField(auto_now_add=True)
    text = fields.TextField()
    answer_question = fields.TextField()
    answer_template = fields.TextField()

    class Meta:
        table = "app_vk_controller_message"


#


async def init_tortoise(username, password, host, port, db_name):
# async def init_tortoise(config):
    await Tortoise.init(  # todo
        # db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        # db_url='postgres://postgres:postgres@localhost:5432/django_db',
        db_url=f'postgres://{username}:{password}@{host}:{port}/{db_name}',
        modules={'models': ['core.database.apostgresql_tortoise_db']}
    )
    await Tortoise.generate_schemas()


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


async def djagno_init():
    await Tortoise.init(
        db_url='postgres://postgres:postgres@localhost:5432/django_db',
        modules={'models': ['__main__']}
    )
    await Tortoise.generate_schemas()


log_handler.init_choice_logging(__name__,
                                *__all__)

if __name__ == '__main__':
    run_async(djagno_init())
