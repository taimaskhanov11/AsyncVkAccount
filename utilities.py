import random
from collections import Counter

from settings import TALK_DICT_ANSWER_ALL, async_time_track


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

    city_dict_yes = TALK_DICT_ANSWER_ALL['город']
    city_dict_no = TALK_DICT_ANSWER_ALL['негород']

    try:
        for a, b in TALK_DICT_ANSWER_ALL.items():

            # todo update

            if a == 'город' or a == 'негород':
                continue
            # print(a, b)
            if any(token in text for token in b["вход"]):
                answer = random.choice(b['выход'])
                answer_end += answer + ','
                # print(answer)
                # return answer
        answer_end = answer_end[0:-1]

        if any(city_text in text for city_text in city_dict_yes['вход']):
            answer = random.choice(city_dict_yes['выход'])
            res_answer = answer.format(city)
            # answer_end += res_answer + ','
            answer_end += res_answer

        elif any(city_text in text for city_text in city_dict_no['вход']):
            answer = random.choice(city_dict_no['выход'])
            # answer_end += answer + ','
            answer_end += answer

        return answer_end
    except Exception as e:
        print(e)
        return False


