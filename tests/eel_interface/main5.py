import eel
import Mastermind

game = Mastermind.Mastermind()

lastGuess = "1122"
@eel.expose
def response(code):
    global lastGuess
    game.registerResponse(lastGuess, code)
    guess = game.nextGuess()
    lastGuess = guess
    eel.provideNextGuess(guess)


eel.init("www")
eel.start("index5.html")