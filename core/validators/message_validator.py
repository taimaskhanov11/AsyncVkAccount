from core.classes import BaseUser
from core.handlers import text_handler
from settings import signs


class MessageValidator:

    def __init__(self, bad_words: list[str]):
        self.bad_words = bad_words

    def check_for_bad_words(self, text: str) -> bool:
        return any(map(lambda x: x in text, self.bad_words))
