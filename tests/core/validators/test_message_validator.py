import unittest

from core.validators import MessageValidator


class TestMessageValidator(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls) -> None:
    #     pass
    #
    # def setUp(self) -> None:
    #     pass

    def test_check_for_bad_words_in(self):
        bad_words = ['шлюха', 'пизда', 'хуй']
        message_validator = MessageValidator(bad_words)
        text = 'привет как дела че делаешь ты шлюха'
        check = message_validator.check_for_bad_words(text)
        self.assertEqual(check, True)

    def test_check_for_bad_words_not_in(self):
        bad_words = ['шлюха', 'пизда', 'хуй']
        message_validator = MessageValidator(bad_words)
        text = "привет как дела че делаешь ты чертила ебанная"
        check = message_validator.check_for_bad_words(text)
        self.assertEqual(check, False)


if __name__ == '__main__':
    unittest.main()
