import json
import statistics
from pprint import pprint
from sys import getsizeof

from VkBotDir.database.db import Users, time_track

USER_LIST = {}
USER_STATE = {}


class User:
    def __init__(self, user, name, city, state):
        self.user = user
        self.name = name
        self.city = city
        self.state = state


for i in range(10000):
    USER_LIST[i] = User(i, 'Olege', 'bubryanovs', 1)
    # Users.create_user(i, 1, 'qasd', 'afasdf')
# for i in range(1000):
#     # USER_LIST[i] = User(1234, 'Olege', 'bubryanovs', 1)
#     Users.create_user(i, 1, 'qasd', 'afasdf')


def write_userstate(user):
    state = USER_LIST[user].state
    name = USER_LIST[user].name
    city = USER_LIST[user].city
    USER_STATE[str(user)] = {'state': state,
                             'name': name,
                             'city': city}

    with open('userstate.json', 'w', encoding='utf8') as ff:
        json.dump(USER_STATE, ff, indent=4, ensure_ascii=False)


@time_track
def json_run(user_id):
    write_userstate(user_id)


@time_track
def sql_run(user_id):
    Users.add_state(user_id)

@time_track
def txt_run(user_id):
    with open('users.txt', 'a') as ff:
        ff.write(f'{user_id}\n')


def test_1():
    json_data = []
    for i in range(100):
        # USER_LIST[i].state+=1
        json_data.append(json_run(i))

    sql_data = []
    for i in range(100):
        # USER_LIST[i].state+=1
        sql_data.append(sql_run(i))

    print('json average time', statistics.mean(json_data))
    print('sql average time', statistics.mean(sql_data))
    pprint(len(json_data))
    pprint(len(sql_data))
    print(getsizeof(USER_LIST))
    print(getsizeof(USER_STATE))

def test2():
    txt_data = []
    for i in range(100000):
        txt_data.append(txt_run(i))
    print('txt average time', statistics.mean(txt_data))


if __name__ == '__main__':
    test2()