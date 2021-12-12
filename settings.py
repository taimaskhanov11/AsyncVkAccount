import json
import os
from pathlib import Path

import yaml
from aiovk import TokenSession

# from polog import config, file_writer


__all__ = [
    'settings',
    'bot_version',
    'ai_logic',
    'conversation_stages',
    'signs',
    'text_settings',
    'token_config',
    'message_config',
    'db_config',
    'bad_words',
    'log_colors',

    'vk_tokens',
    'tg_token',
    'tg_id',
    'views',

    # 'LOG_COLLECTOR',
    # 'log'
]

from core.log_settings import exp_log

BASE_DIR = Path(__file__).parent


# config.add_handlers(file_writer(str(Path(BASE_DIR, 'logs/new_log.log'))))


def read_json(path, encoding='utf-8-sig'):
    with open(Path(BASE_DIR, path), 'r', encoding=encoding) as ff:
        return json.load(ff)


def read_yaml(path):
    # print(path)
    with open(Path(BASE_DIR, path), 'r', encoding='utf-8-sig') as fh:
        return yaml.safe_load(fh)


# LOG_COLLECTOR = multiprocessing.Queue()
# log = LogHandler(None, LOG_COLLECTOR)


TokenSession.API_VERSION = '5.131'
# ai_logic = read_json('config/json/ai_logic.json')
ai_logic = read_yaml('config/ai_logic.yaml')
# conversation_stages = read_json('config/json/conversation_stages.json')
conversation_stages = read_yaml('config/conversation_stages.yaml')

# settings = read_json('config/json/settings.json')
settings = read_yaml('config/settings.yaml')
views = read_json('config/validators_text.json')  # текс для валидаторов
bad_words = read_yaml('config/bad_words.yaml')

bot_version = settings['version']
text_settings = settings['text_handler_controller']
token_config = settings['token_config']
message_config = settings['message_config']
db_config = settings['db_config']

try:
    tg_token = os.getenv('tg_token') or token_config['telegram_token']
    tg_id = int(os.getenv('tg_id') or token_config['telegram_id'])
    # tg_id = [int(os.getenv('tg_id'))] if os.getenv('tg_id') else token_config['telegram_id']
    vk_tokens = [os.getenv('tokens')] if os.getenv('tokens') else token_config['vk_tokens']
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
    "tg": '⟳',
    "number": '✆',
}

log_colors = {
    "info": ["green", "◯"],
    "warning": ["yellow", "⬤"],
    "error": ["red", "✖"],
    "debug": ["white", "இ"]
}
