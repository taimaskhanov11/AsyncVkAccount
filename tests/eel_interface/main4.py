import eel

eel.init("www")
eel.start("index4.html", block=False)

@eel.expose
def send(msg):
    print("Received Message: " + msg)
    return "ok"

while True:
    text = eel.readTextBox()()
    print("\rText box contents: {}".format(text),end='')
    eel.sleep(0.2)