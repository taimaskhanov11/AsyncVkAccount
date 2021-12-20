import asyncio

import pytest
from mock.mock import MagicMock
from tortoise import Tortoise

from core.classes import BaseUser
from core.database import DbAccount, DbUser, init_tortoise


@pytest.fixture(scope='module')
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def init_db():
    print('!@#!@#!@#!@#!@#START_DB')
    try:
        await init_tortoise('postgres', 'postgres', 'localhost', '5432', 'testdb')
        yield
    finally:
        # await DbUser.delete_all()
        print('!@#!@#!@#!@#!@#END_DB')
        await Tortoise.close_connections()


@pytest.fixture
async def user():
    return BaseUser(
        **{
            "user_id": 1,
            "state": 1,
            "db_user": MagicMock(),
            "name": "a",
            "overlord": MagicMock(),
            "city": "test_city",
        }
    )

