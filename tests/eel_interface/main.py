import eel

@eel.expose
def hello():
    print('Hello world!')

@eel.expose
def addText():
    return 'assd'


eel.init('www')
eel.start('index1.html')
