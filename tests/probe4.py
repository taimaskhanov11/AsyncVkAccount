import time

from more_termcolor import colored


def progressBar(current, total, barLength = 20):
    percent = float(current) * 100 / total
    arrow = '-' * int(percent/100 * barLength - 1) + '>'
    spaces = ' ' * (barLength - len(arrow))
    print('\rProgress [%s/%s]: [%s%s] %d %%' % (current,total,arrow, spaces, percent), end='',flush=True)


def status_bar_line (once, timer):
    for i in range(once):
        print(f'\r{colored(f"{i}  %","bright blue" )}', end='', flush=True)
        time.sleep(timer)
# status_bar_line(100, .02, )
print(round(3.))