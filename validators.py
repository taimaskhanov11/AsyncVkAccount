from handlers import log_handler

__all__ = [
    'photo_validator',
    'age_validator',
    'mens_validator',
    'count_friends_validator'
]

import sys


def photo_validator(photo) -> bool:
    if photo:
        return True
    return False


def age_validator(age: str | int) -> bool:
    if age:
        age = age[-1:-5:-1]
        age = age[-1::-1]
        date = 2021 - int(age)
        if date >= 20:
            return True
        return False
    else:
        return True  # todo


def count_friends_validator(count: int) -> bool:
    if 24 <= count <= 1001:
        return True
    return False


def mens_validator(info: tuple) -> tuple[bool, int]:
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
        return False, res
    else:
        return True, res


current_module = sys.modules[__name__]
for v_name in __all__:
    v = getattr(current_module, v_name)
    setattr(current_module, v_name, log_handler(v))

