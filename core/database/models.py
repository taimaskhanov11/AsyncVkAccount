import datetime
import random

from tortoise import fields, models

__all__ = [
    'DbCategory',
    'DbInput',
    'DbOutput',
    'DbNumber',
    'DbUser',
    'DbMessage',
    'DbAccount',
]


class DbAccount(models.Model):
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


class DbUser(models.Model):
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
        await DbMessage.filter(user=self).delete()
        await self.delete()

    @classmethod
    async def delete_all(cls):
        for user in await cls.all():
            await user.delete_instance()

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


class DbMessage(models.Model):
    user = fields.ForeignKeyField('models.DbUser', on_delete=fields.CASCADE, related_name='messages', index=True)
    account = fields.ForeignKeyField('models.DbAccount', on_delete=fields.CASCADE, related_name='messages', index=True)
    sent_at = fields.DatetimeField(auto_now_add=True)
    text = fields.TextField()
    answer_question = fields.TextField()
    answer_template = fields.TextField()

    class Meta:
        table = "app_vk_controller_message"


class SendMessage(models.Model):
    user = fields.ForeignKeyField('models.DbUser', related_name='sended_messages', on_delete=fields.CASCADE)
    account = fields.ForeignKeyField('models.DbAccount', related_name='sended_messages', on_delete=fields.CASCADE)
    sent_at = fields.DatetimeField()
    text = fields.TextField()

    @classmethod
    async def wait_message(cls, user):
        pass


class DbNumber(models.Model):
    account = fields.ForeignKeyField('models.DbAccount', on_delete=fields.CASCADE, related_name='numbers')
    user = fields.OneToOneField('models.DbUser', on_delete=fields.CASCADE, related_name='number')
    number = fields.TextField()
    date = fields.DatetimeField(default=datetime.datetime.now().replace(microsecond=0))
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_number"


class DbCategory(models.Model):
    title = fields.CharField(max_length=255, unique=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_category"


class DbInput(models.Model):
    category = fields.ForeignKeyField('models.DbCategory', on_delete=fields.CASCADE, related_name='input')
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
                    output = await DbOutput.filter(category=field.category)
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


class DbOutput(models.Model):
    category = fields.ForeignKeyField('models.DbCategory', on_delete=fields.CASCADE, related_name='output')
    text = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "app_vk_controller_output"
