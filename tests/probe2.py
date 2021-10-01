import asyncio
import json
import time

# from VkBotDir.main.user_class import User

# rek = {'delay': 10}
# 
# with open('delay_answer.json', 'w', encoding='utf8') as ff:
#     json.dump(rek, ff)
# 
# with open('delay_answer.json', 'r', encoding='utf-8-sig') as ff:
#     res = json.load(ff)
# print(rek)
# print(res)

import re
from collections import Counter

number = 'вот мой номер 2332'
# result = re.findall(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', number)
# result = re.findall(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$', number)
result = re.findall('\d{4,}', number)


# if result:  # True, False
#     print('yes')

async def main():
    print(1)
    await asyncio.sleep(10)
    print(2)


async def main2():
    print(1)
    await asyncio.sleep(10)
    print(2)
    return 3


async def end():
    x = await asyncio.gather(main(), main2())
    print(x)


a = {'count': 449, 'items': [
    {'first_name': 'Pasha', 'id': 210885, 'last_name': 'Nuts', 'can_access_closed': True, 'is_closed': False, 'sex': 2,
     'can_invite_to_chats': False},
    {'first_name': 'Антон', 'id': 393646, 'last_name': 'Рудой', 'can_access_closed': True, 'is_closed': False, 'sex': 2,
     'can_invite_to_chats': False},
    {'first_name': 'Craig', 'id': 989149, 'last_name': 'Ashton', 'can_access_closed': True, 'is_closed': False,
     'sex': 2, 'can_invite_to_chats': False}]}

b = ['a', 2, 2, 3, 4, 'a', 5]
k = {(123,): 3}


class Ali:

    ret = 2


    def arec(self):
        self.ret = 3

if __name__ == '__main__':

    ali = Ali()
    print(ali.ret)
    ali.__getattribute__('arec')()
    print(ali.ret)




    # b  = [i['sex'] for i in a['items']]
    #
    # print(b)
