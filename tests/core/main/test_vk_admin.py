import asyncio

import pytest
from mock.mock import AsyncMock, MagicMock, Mock
from tortoise import Tortoise

import vk_bot
from core.database import init_tortoise
from core.handlers.log_message import AsyncLogMessage
from main import init_logging_main
from settings import tg_id, tg_token, vk_tokens


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
def mock_log_message():
    async_log_collector = asyncio.Queue()
    log_message = AsyncLogMessage(async_log_collector)
    print('mock_log_message')
    return log_message


messages = [4, 1130616, 49, 408048349, 1640178505, 'asd']


async def iter():
    while True:
        # response = await self.wait()
        response = [[4, 1130616, 49, i, 1640178505, f'test_message_{i}'] for i in range(10)]
        # for event in response['updates']:
        for event in response:
            await asyncio.sleep(0.5)
            yield event


vk_bot.conversation_stages = {f'state{i}': [f'test{i}_1', f'test{i}_2'] for i in range(100)}
vk_bot.init_tortoise = AsyncMock()


def mock_find_most_city(x):
    return 'test_city'


# vk_bot.find_most_city = Mock(return_value='test_city')
vk_bot.find_most_city = mock_find_most_city


@pytest.fixture
def mock_accounts(mock_log_message):
    accounts = [vk_bot.AdminAccount(token, tg_token, tg_id, 3) for token in vk_tokens]
    new_accounts = []
    for num, acc in enumerate(accounts):
        acc.block_message_count = 100
        acc.delay_for_users = (0, 0)
        acc.delay_typing = (0, 0)
        acc.delay_for_acc = 0
        acc.longpoll = AsyncMock(iter=iter)
        # acc.longpoll.iter = iter

        async_log_collector = asyncio.Queue()
        acc.log = AsyncLogMessage(async_log_collector)

        # acc.check_and_get_self_info = AsyncMock()

        async def send_message(*args, **kwargs): await asyncio.sleep(0.1)

        acc.message_handler.send_message = send_message

        data = [
            {
                'id': num,
                'token': num,
                'first_name': f"account_{num}",
                'last_name': 'test_name',
                'photo_url': 'test_name',
                'photo_max_orig': 'NULL'
            }
        ]
        acc.api = MagicMock()
        acc.api.users = MagicMock(get=AsyncMock(return_value=data, name='users.get'))
        # acc.api.users.get =

        acc.validator = MagicMock()
        acc.validator.validate = MagicMock(return_value=True, name='validator.validate')
        acc.check_friend_status = AsyncMock(return_value=True, name='check_friend_status')
        acc.get_friend_info = AsyncMock()

        async def mock_get_user_info(user_id): return {'first_name': f'test_name{user_id}',
                                                       'last_name': 'test_last_name',
                                                       'can_access_closed': 'True',
                                                       }

        acc.get_user_info = mock_get_user_info

        acc.unloading_from_database = AsyncMock(name='unloading_from_database')
        acc.message_handler.uploaded_photo_from_dir = AsyncMock(name='uploaded_photo_from_dir')

    # print(accounts[0].block_message_count)
    return accounts


@pytest.mark.asyncio
@pytest.mark.usefixtures('init_db', 'delete_all')
class TestAdminAccount:

    async def test_user_creator_start(self, mock_log_message, mock_accounts):
        init_logging_main(mock_log_message)
        loop = asyncio.get_event_loop()
        [loop.create_task(acc.run_session()) for acc in mock_accounts]
        # await log_message.run_async_worker()
        # loop.create_task(log_message.run_async_worker())
        print('wait')
        await mock_log_message.run_async_worker()
        print('wait_done')

    # def test_speed_asyncio(self, mock_accounts, mock_log_message):
    #     init_logging_main(mock_log_message)
    #     # await self._user_creator_start(mock_log_message, mock_accounts)
    #     loop = asyncio.new_event_loop()
    #     loop.run_until_complete(self._user_creator_start(mock_log_message, mock_accounts))
