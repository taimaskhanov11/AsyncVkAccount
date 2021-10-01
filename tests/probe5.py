import statistics
import time


def time_track(func):
    def wrapper(*args, **kwargs):
        now = time.time()
        res = func(*args, **kwargs)
        end = time.time() - now
        print(end, 's')
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return end

    return wrapper


def run():
    for i in range(100):
        print(i ** 1000)


@time_track
def run2():
    for i in range(100):
        print(i ** 1000)


def func1():
    check_time = []
    for i in range(20):
        now = time.time()
        run()
        end = time.time() - now
        check_time.append(end)
        print(end, 's')
    return statistics.mean(check_time)


def func2():
    check_time = []
    for i in range(20):
        check_time.append(run2())

    return statistics.mean(check_time)


if __name__ == '__main__':
    res = func1()
    res2 = func2()
    print(res, res2)
