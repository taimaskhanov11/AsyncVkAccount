import time

from core.handlers import text_handler
from settings import signs


class ResponseTimeTrack:
    def __init__(self, user_id: int):
        self.start_time = time.monotonic()
        self.user_id = user_id

    def stop(self, check: bool = False) -> None:
        end_time = time.monotonic()
        check_time_end = round(end_time - self.start_time, 6)
        text = f'{self.user_id}/Время полной проверки {check_time_end}s' if check else f'Время формирования ответа {check_time_end} s'
        text_handler(signs['time'], text, 'debug', color='blue',
                     off_interface=True, prop=True)
