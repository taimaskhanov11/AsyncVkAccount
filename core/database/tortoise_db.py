import datetime
import json
import random
from pathlib import Path

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model

from settings import db_config

BASE_DIR = Path(__file__)

__all__ = [
    'Category',
    'Input',
    'Output',
    'Number',
    'DbUser',
    'Message',
    'DbAccount',
    'init_tortoise',
]


class DbAccount(Model):
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


class DbUser(Model):
    account = fields.ForeignKeyField('models.DbAccount', on_delete=fields.CASCADE, related_name='users')
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

    async def delete_instance(self):
        await Message.filter(user=self).delete()
        await self.delete()

    @classmethod
    async def delete_all(cls):
        for user in await cls.all():
            await user.delete()

    @classmethod
    async def blocking(cls, user_id):
        table_user = await cls.get(user_id=user_id)
        table_user.blocked = True
        await table_user.save()

    @classmethod
    async def add_state(cls, user_id):
        user = await cls.get(user_id=user_id)
        user.state += 1
        await user.save()
        return user.state


class Message(Model):
    user = fields.ForeignKeyField('models.DbUser', on_delete=fields.CASCADE, related_name='messages', index=True)
    account = fields.ForeignKeyField('models.DbAccount', on_delete=fields.CASCADE, related_name='messages', index=True)
    sent_at = fields.DatetimeField(auto_now_add=True)
    text = fields.TextField()
    answer_question = fields.TextField()
    answer_template = fields.TextField()

    class Meta:
        table = "app_vk_controller_message"


class SendMessage(Model):
    user = fields.ForeignKeyField('models.DbUser', related_name='sended_messages', on_delete=fields.CASCADE)
    account = fields.ForeignKeyField('models.DbAccount', related_name='sended_messages', on_delete=fields.CASCADE)
    sent_at = fields.DatetimeField()
    text = fields.TextField()

    @classmethod
    async def wait_message(cls, user):
        pass


class Number(Model):
    account = fields.ForeignKeyField('models.DbAccount', on_delete=fields.CASCADE, related_name='numbers')
    user = fields.OneToOneField('models.DbUser', on_delete=fields.CASCADE, related_name='number')
    number = fields.TextField()
    date = fields.DatetimeField(default=datetime.datetime.now().replace(microsecond=0))
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_number"

    # def __str__(self):
    #     return self.user.first_name

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


async def init_tortoise(username, password, host, port, db_name):
    # async def init_tortoise(config):
    await Tortoise.init(  # todo
        # db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        # db_url='postgres://postgres:postgres@localhost:5432/django_db',
        # db_url=f'postgres://{username}:{password}@db:{port}/{db_name}',
        db_url=f'postgres://{username}:{password}@{host}:{port}/{db_name}',
        modules={'models': ['core.database.tortoise_db']}
    )
    await Tortoise.generate_schemas()


if __name__ == '__main__':
    run_async(init_tortoise(*db_config.values()))
