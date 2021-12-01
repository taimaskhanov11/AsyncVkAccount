from core.handlers import text_handler
from settings import signs


class LogMessage:
    log_messages = {
        'adding_friend': [signs['yellow'], "Добавление в друзья", 'warning'],
        'friend_status': [signs['yellow'], "Статус дружбы {}", 'warning'],  # add_status
        'user_check_info': [signs['yellow'], "{}, {}, {}\n"  # info, count_friend, age, has_photo
                                             "{} - Количество друзей"
                                             "Возраст - {}"
                                             "Фото {}", 'warning'],
        'block_account_message': [signs['red'], 'Ошибка авторизации!!!\n'  # token
                                                'Возможно вы ввели неправильный токен или аккаунт ЗАБЛОКИРОВАН!\n'
                                                'Ваш токен {}', 'error']
    }

    def __call__(self, *args, **kwargs):
        print(args)

    def add(self, log_message, *args):
        sign, text, log_type = self.log_messages.get(log_message)
        text_handler(sign, text.format(*args), log_type)
