import os
from pathlib import Path

import json
import os

# from polog import config, file_writer
from aiovk import TokenSession

__all__ = [
    'settings',
    'text_settings',
    'bot_version',
    'ai_logic',
    'conversation_stages',
    'signs',

    'vk_tokens',
    # 'tg_token',
    # 'tg_id',
    'views',
]

from core.log_settings import exp_log

BASE_DIR = Path(__file__).parent


# config.add_handlers(file_writer(str(Path(BASE_DIR, 'logs/new_log.log'))))


def read_json(path, encoding='utf-8-sig'):
    with open(Path(BASE_DIR, path), 'r', encoding=encoding) as ff:
        return json.load(ff)


TokenSession.API_VERSION = '5.131'
ai_logic = read_json('config/ai_logic.json')
conversation_stages = read_json('config/conversation_stages.json')
settings = read_json('config/settings.json')
views = read_json('config/validators_text.json')

bot_version = settings['version']
text_settings = settings['text_handler_controller']

try:
    tg_token = os.getenv('tg_token') or settings['telegram_token']
    tg_id = int(os.getenv('tg_id') or settings['telegram_id'])
    vk_tokens = [os.getenv('TOKENS')] or settings['tokens']
except Exception as e:
    exp_log.exception(e)
    print('Неправильный ввод ВК или ТГ токена')

signs = {
    "red": "✖",
    "green": "◯",
    "yellow": "⬤",
    "mark": "[✓]",
    "magenta": "►",
    "time": "⌛",
    "version": "∆",
    "queue": '•‣',
    "message": '✉',
    "sun": '☀',
    "tg": '⟳'
}

log_colors = {
    "info": ["green", "◯"],
    "warning": ["yellow", "⬤"],
    "error": ["red", "✖"],
    "debug": ["white", "இ"]
}
