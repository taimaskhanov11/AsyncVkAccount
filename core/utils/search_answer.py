import random

from settings import ai_logic


async def search_answer(text, city):  # todo
    """
    Конвертирование разных по структуре но одинаковых
    по значению слов к общему по значению слову
    """
    answer_end = ''
    try:
        for a, b in ai_logic.items():
            if any(token in text for token in b["вход"]):
                answer = random.choice(b['выход'])
                if b == 'город':
                    answer.format(city or ai_logic['негород']['выход'])
                answer_end += answer + ','
        answer_end = answer_end[0:-1]
        return answer_end
    except Exception as e:
        print(e)
        return False
