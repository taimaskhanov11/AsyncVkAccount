import json
import random
from collections import Counter
from pathlib import Path

from settings import async_time_track,TALK_DICT_ANSWER_ALL

BASE_DIR = Path(__file__).parent




@async_time_track
async def find_most_city(friend_list):
    friends_city = [i['city']['title'] for i in friend_list['items'] if
                    i.get('city')]
    c_friends_city = Counter(friends_city)
    city = max(c_friends_city.items(), key=lambda x: x[1])[0]
    return city


@async_time_track
async def search_answer(text, city):  # todo
    """
    Конвертирование разных по структуре но одинаковых
    по значению слов к общему по значению слову
    """
    answer_end = ''
    try:
        for a, b in TALK_DICT_ANSWER_ALL.items():
            if any(token in text for token in b["вход"]):
                answer = random.choice(b['выход'])
                if b == 'город':
                    answer.format(city or TALK_DICT_ANSWER_ALL['негород']['выход'] )
                answer_end += answer + ','
        answer_end = answer_end[0:-1]
        return answer_end
    except Exception as e:
        print(e)
        return False
