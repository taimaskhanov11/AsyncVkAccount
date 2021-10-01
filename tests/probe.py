import json5

import vk_api


token = 'c3e1f26d1e40e98be56a86e8776e7fc6b0f2824ab8e2f1a0b0a679339a624fa4b623200fc81b120858532'

data = {}
with open('../config.json5', 'r', encoding='utf-8') as config:
    config = json5.load(config)

    print(config)