import asyncio

import pytest
from tortoise import Tortoise

from core.database import init_tortoise


@pytest.fixture(scope="session")
def db_data():
    print('db_data')
    return 'postgres', 'postgres', 'localhost', '5432', 'testdb'


@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def init_db(db_data):
    print('!@#!@#!@#!@#!@#START_DB')
    try:
        await init_tortoise(*db_data)
        yield
    finally:
        # await DbUser.delete_all()
        print('!@#!@#!@#!@#!@#END_DB')
        await Tortoise.close_connections()


