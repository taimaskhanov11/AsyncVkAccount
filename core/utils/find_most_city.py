from collections import Counter


def find_most_city(friend_list: dict) -> str:
    friends_city = [i['city']['title'] for i in friend_list['items'] if
                    i.get('city')]
    c_friends_city = Counter(friends_city)
    city = max(c_friends_city.items(), key=lambda x: x[1])[0]
    return city
