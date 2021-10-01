import json
from pprint import pprint

template = {
    "state1": ['я так рада что ты меня нашел я как раз дома сижу','хорошо что ты написал', 'приятно что ты написал'],
    "state2": ['вариант ответа 1 state2', 'вариант ответа 2 state2'],
    "state3": ['вариант ответа 1 state3', 'вариант ответа 2 state3'],
    "state4": ['вариант ответа 1 state4', 'вариант ответа 2 state4'],
    "state5": ['вариант ответа 1 state5', 'вариант ответа 2 state5'],
    "state6": ['вариант ответа 1 state6', 'вариант ответа 2 state6']
}

# with open('template.json', 'w', encoding='utf8') as ff:
#     json.dump(template, ff, indent=4, ensure_ascii=False)


#     pprint(a)
# with open('templatea.json', 'w', encoding='utf8') as ff:
#     json.dump(template, ff, indent=4, ensure_ascii=False)

with open('../templatea.json', 'r', encoding='utf-8-sig') as ff:
    a = json.load(ff)
    print(a)
