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



