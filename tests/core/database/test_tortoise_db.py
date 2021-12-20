import asyncio

import pytest
from tortoise import Tortoise

from core.database.tortoise_db import *


@pytest.mark.asyncio
async def test_init_and_close(db_data):
    await init_tortoise(*db_data)
    assert bool(Tortoise._connections) is True
    await Tortoise.close_connections()
    assert bool(Tortoise._connections) is False
    print('ENDtest_init_and_close')


@pytest.mark.asyncio
@pytest.mark.usefixtures('init_db', 'delete_all')
class TestDbAccount:

    async def test_creating(self, db_account: DbAccount):
        assert await DbAccount.exists(token='test_token')
        assert db_account.user_id == 1

    async def test_blocking(self, db_account: DbAccount):
        await DbAccount.blocking(db_account.user_id)
        await db_account.refresh_from_db()

        assert db_account.blocked is True

    async def test_delete(self, db_account: DbAccount):
        db_user = await DbUser.create(
            account=db_account, first_name='test', last_name='test', user_id=1
        )
        message = await Message.create(
            user=db_user, account=db_account, text='test', answer_question='test', answer_template='test'
        )
        # await db_account.delete()
        print(await DbAccount.all().delete())
        assert await db_account.exists() is False
        assert await db_user.exists() is False
        assert await message.exists() is False


@pytest.mark.asyncio
@pytest.mark.usefixtures('init_db', 'delete_all')
class TestDbUser:
    async def test_creating(self, db_user: DbUser):
        assert await DbUser.exists(first_name='a') is True
        assert db_user.user_id == 1

    async def test_blocking(self, db_user: DbUser):
        await DbUser.blocking(db_user.user_id)
        await db_user.refresh_from_db()

        assert db_user.blocked is True

    async def test_add_state(self, db_user: DbUser):
        state = await db_user.add_state(db_user.user_id)
        await db_user.refresh_from_db()
        assert state == 2
        assert db_user.state == 2

