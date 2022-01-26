import time


class TimeTrack:
    def __init__(self, user, log):
        self.start_time = time.monotonic()
        self.user = user
        self.log = log

    def stop(self, check: bool = False) -> None:
        end_time = time.monotonic()
        check_time_end = round(end_time - self.start_time, 6)
        text = f'{self.user.user_id}/Время полной проверки {check_time_end}s' if check else f'Время формирования ответа {check_time_end} s'
        self.log('time_track_stop', text)
