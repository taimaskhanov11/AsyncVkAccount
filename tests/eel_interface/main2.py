import datetime

import eel

eel.init('www')
eel.start('index1.html', block = False)

while True:
    eel.addText(f'The time now is {datetime.datetime.now().replace(microsecond=0)}')
    eel.sleep(1)