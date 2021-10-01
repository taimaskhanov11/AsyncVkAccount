class Mastermind:
    def __init__(self):
        self.resetState()

    def registerResponse(self, guess, response):
        if response == "2222":
            # Win
            return

        eliminated = self.computeEliminatedList(guess, response)
        self.possibleSolutions -= eliminated

    def nextGuess(self):
        possibleResponses = set()
        for i in range(0, 3):
            for j in range(0, 3):
                for k in range(0, 3):
                    for l in range(0, 3):
                        code = "{}{}{}{}".format(i, j, k, l)
                        possibleResponses |= {code}

        bestGuess = ""
        bestEliminations = -1

        for guess in self.possibleSolutions:
            minEliminations = 9999
            for response in possibleResponses:
                eliminations = len(self.computeEliminatedList(guess, response))
                if eliminations < minEliminations:
                    minEliminations = eliminations

            if minEliminations > bestEliminations:
                bestEliminations = minEliminations
                bestGuess = guess

        return guess

    def computeEliminatedList(self, guess, response):
        count_2 = response.count("2")
        count_1 = response.count("1")

        eliminated = set()
        for code in self.possibleSolutions:
            sim_response = self.computeResponse(guess, code)

            sim_count_2 = sim_response.count("2")
            sim_count_1 = sim_response.count("1")
            if sim_count_1 != count_1 or sim_count_2 != count_2:
                eliminated |= {code}

        return eliminated

    def computeResponse(self, guess, code):
        code_finite = list(code)
        response = ["?"] * 4
        for i in range(0, 4):
            if guess[i] == code[i]:
                response[i] = "2"
                code_finite[i] = " "

        for i in range(0, 4):
            if guess[i] != code[i]:
                if guess[i] in code_finite:
                    response[i] = "1"
                    code_finite[code_finite.index(guess[i])] = " "
                else:
                    response[i] = "0"

        return response

    def resetState(self):
        self.possibleSolutions = set()
        for i in range(1, 7):
            for j in range(1, 7):
                for k in range(1, 7):
                    for l in range(1, 7):
                        code = "{}{}{}{}".format(i, j, k, l)
                        self.possibleSolutions |= {code}
