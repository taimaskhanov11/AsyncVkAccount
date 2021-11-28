from pathlib import Path

import json

# from polog import config, file_writer


__all__ = [
    'settings',
    'text_settings',
    'bot_version',
    'ai_logic',
    'conversation_stages',
    'signs',

    'tokens',
    'views',
]

BASE_DIR = Path(__file__).parent


# config.add_handlers(file_writer(str(Path(BASE_DIR, 'logs/new_log.log'))))


def read_json(path, encoding='utf-8-sig'):
    with open(Path(BASE_DIR, path), 'r', encoding=encoding) as ff:
        return json.load(ff)


ai_logic = read_json('config/ai_logic.json')
conversation_stages = read_json('config/conversation_stages.json')
settings = read_json('config/settings.json')
views = read_json('config/validators_text.json')

bot_version = settings['version']
text_settings = settings['text_handler_controller']
tokens = settings['tokens']

signs = {
    "red": "✖",
    "green": "◯",
    "yellow": "⬤",
    "mark": "[✓]",
    "magenta": "►",
    "time": "⌛",
    "version": "∆",
    "queue": '•‣',
    "message": '✉'
}

log_colors = {
    "info": ["green", "◯"],
    "warning": ["yellow", "⬤"],
    "error": ["red", "✖"],
    "debug": ["white", "இ"]
}
