from pathlib import Path

from loguru import logger
from tortoise import Tortoise, run_async

from core.database.models import DbUser, DbInput, DbOutput, DbCategory
from settings import db_config, ai_logic

BASE_DIR = Path(__file__)

__all__ = [
    'init_tortoise',
]


async def init_tortoise(username, password, host, port, db_name):
    # async def init_tortoise(config):
    await Tortoise.init(  # todo
        # db_url='postgres://postgres:postgres@localhost:5432/vk_controller',
        # db_url='postgres://postgres:postgres@localhost:5432/django_db',
        # db_url=f'postgres://{username}:{password}@db:{port}/{db_name}',
        db_url=f'postgres://{username}:{password}@{host}:{port}/{db_name}',
        modules={'models': ['core.database.models']}
    )
    await Tortoise.generate_schemas()


async def runner(username, password, host, port, db_name):
    data = {
        'connections': {
            # Dict format for connection
            'default': {
                'engine': 'tortoise.backends.asyncpg',
                'credentials': {
                    'host': host,
                    'port': port,
                    'user': username,
                    'password': password,
                    'database': db_name,
                },
            }, 'default2': {
                'engine': 'tortoise.backends.asyncpg',
                'credentials': {
                    'host': host,
                    'port': port,
                    'user': username,
                    'password': password,
                    'database': db_name,
                },
            },

        },
        'apps': {
            'models': {
                'models': ['core.database.models'],
                # If no default_connection specified, defaults to 'default'
                'default_connection': 'default',
            }, 'models2': {
                'models': ['core.database.models'],
                # If no default_connection specified, defaults to 'default'
                'default_connection': 'default2',
            },
        },
    }
    await Tortoise.init(data)
    print(Tortoise._connections)
    default = Tortoise.get_connection('default2')
    print(DbUser.describe())


@logger.catch
async def get_send_messages():
    await init_tortoise(*db_config.values())
    for category, data in ai_logic.items():
        category = await DbCategory.get_or_create(title=category)
        category = category[0]
        for inp in data['вход']:
            await DbInput.get_or_create(text=inp, category=category)
        for outp in data['выход']:
            await DbOutput.get_or_create(text=outp, category=category)


if __name__ == '__main__':
    # run_async(init_tortoise(*db_config.values()))
    # run_async(runner(*db_config.values()))
    run_async(get_send_messages())
