import json
import random

from open_data import read_json, read_template

with open('../answers.json', 'r', encoding='utf-8-sig') as ff:
    c = json.load(ff)

TEMPLATES = read_template()
# with open('templatea.json', 'r', encoding='utf-8-sig') as ff:
#     TEMPLATES = json.load(ff)
#     # print(a)

def search_answer(text):  # todo
    """
    конвертирование разных по структуре но одинаковых
    по значению слов к общему по значению слову
    """
    answer_end = ''
    try:
        for a, b in c.items():
            # print(a, b)
            if any(token in text for token in b["вход"]):
                answer = random.choice(b['выход'])
                answer_end += answer + ','
                # print(answer)
                # return answer
        answer_end = answer_end[0:-1]
        return answer_end
    except:
        return False


class User:

    def __init__(self, user_id):
        self.user_id = user_id
        self.state = 1

    def act(self):
        res = random.choice(TEMPLATES[f"state{self.state}"])
        self.state += 1
        return res

user = User(123)

print(f"{search_answer('как погода')} {user.act()}")
print(TEMPLATES)
print(user.act())
