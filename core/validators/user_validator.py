import asyncio

from core.handlers import text_handler
from settings import signs


class UserValidator:

    def __init__(self):
        self.validators = (
            self.photo_validator,
            self.age_validator,
            self.count_friends_validator,
            self.mens_validator
        )

    async def all_validators1(self, *args):  # todo
        tasks = [asyncio.to_thread(func, arg) for func, arg in zip(self.validators, args)]
        res = await asyncio.gather(*tasks, return_exceptions=True)
        # print(res)
        if all(res):
            return True
        return False

    def validate(self, friend_list: dict, user_info: dict, ) -> bool:
        m_f_count = [i['sex'] for i in friend_list['items']]
        female, male, age = m_f_count.count(1), m_f_count.count(2), user_info.get('bdate')
        has_photo, count_friend = user_info['has_photo'], friend_list['count']

        self.info_view(user_info, count_friend, age, has_photo)
        return self.all_validators(has_photo, age, count_friend, (male, female, count_friend))

    def all_validators(self, has_photo: int, age: str, count_friend: int, mfc: tuple[int, int, int], ) -> bool:
        return all(
            (func(arg) for func, arg in zip(self.validators, (has_photo, age, count_friend, mfc)))
        )

    def info_view(self, info, count_friend, age, has_photo):
        text_handler(signs['yellow'], f"{info['first_name']}, {info['last_name']}, {info['id']}", 'warning')
        text_handler(signs['yellow'], f"{count_friend} - Количество друзей", 'warning')
        text_handler(signs['yellow'], f'Возраст - {age}', 'warning')
        text_handler(signs['yellow'], f'Фото {has_photo}', 'warning')

    def photo_validator(self, photo: int) -> bool:
        return bool(photo)

    def age_validator(self, age: str) -> bool:
        try:
            if age:
                age = age[-1:-5:-1]
                age = age[-1::-1]
                date = 2021 - int(age)
                if date >= 20:
                    return True
                return False
            else:
                return True  # todo
        except Exception as e:
            # exp_log.exception(e)
            text_handler(signs['red'], f'Неккоректный возраст {age}', 'error')
            return True

    def count_friends_validator(self, count: int) -> bool:
        if 24 <= count <= 1001:
            return True
        return False

    def mens_validator(self, info: tuple[int, int, int]) -> bool:
        """
        Проверка соотношения м/ж
        if m<=35%:
            :return: False
            :rtype: bool
        else:
            :return: True
            :rtype: bool
        """
        male, female, friends = info
        res = male / friends * 100
        if round(res) <= 35:
            return False
        else:
            return True

# Validator = validator_handler(UserValidator)
