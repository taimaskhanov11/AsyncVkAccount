import asyncio

import pytest
from mock.mock import AsyncMock

from core.database.models import DbAccount, DbUser
from core.message_handler import MessageHandler


def message_handler():
    handler = MessageHandler()
    async def send_message(*args, **kwargs): await asyncio.sleep(0.1)
    handler.send_message = send_message
    return handler
