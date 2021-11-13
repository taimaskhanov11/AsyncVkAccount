import logging.config
import os
# LOG_DIR = r'C:\Users\taima\PycharmProjects\vk_acaut\VkBotDir\logs'
# text = importlib.res('data', 'файл.txt')
# print(pkgutil.get_data('VkBotDir', 'logs/log_settings.py'))
# print(os.path.abspath('log_settings.py'))
# import os
# dirname = os.path.dirname(__file__)
# filename = os.path.join(dirname, 'relative/path/to/file/you/want')
# print(__file__)
from pathlib import Path

# import importlib

# import pkgutil
# import sys


LOG_DIR = Path(Path(__file__).parent, 'logs')
# print(LOG_DIR)
# LOG_DIR = os.path.dirname(__file__)
# print(LOG_DIR)
# print(LOG_DIR)
# print(os.path.basename(__file__))
# print(os.getcwd())


log_config = {
    "version": 1,
    "formatters": {
        "my_formatter": {
            "format": "%(levelname)s - %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "main_format": {
            "format": "%(levelname)s :%(asctime)s:%(name)s:%(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "print_format": {
            "format": "%(levelname)s [%(asctime)s] %(message)s ",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }

    },
    "handlers": {
        "file_handler_connection": {
            "class": "logging.FileHandler",
            "formatter": "my_formatter",
            "filename": f"{LOG_DIR}/VkBot_connection.log",
            "encoding": "utf8"
        },
        "file_handler_errors": {
            "class": "logging.FileHandler",
            "formatter": "my_formatter",
            "filename": f"{LOG_DIR}/VkBot_errors.log",
            "encoding": "utf8"
        },
        "file_handler_talk": {
            "class": "logging.FileHandler",
            "formatter": "print_format",
            "filename": f"{LOG_DIR}/VkBot_talk.log",
            "encoding": "utf-8"
        },

        "file_handler_main": {
            "class": "logging.FileHandler",
            "formatter": "main_format",
            "filename": f"{LOG_DIR}/main.log",
            "encoding": "utf-8"
        },
        "file_handler_vk_api": {
            "class": "logging.FileHandler",
            "formatter": "main_format",
            "filename": f"{LOG_DIR}/vk_api.log",
            "encoding": "utf-8"
        },
        "file_handler_property": {
            "class": "logging.FileHandler",
            "formatter": "print_format",
            "filename": f"{LOG_DIR}/property.log",
            "encoding": "utf-8"
        },

        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "main_format",
            # "encoding": "utf8",
            # "filename": "logs/main.log"
        }

    },
    "loggers": {
        "urllib3.connectionpool": {
            "handlers": ["file_handler_connection"],
            "level": "DEBUG",
        },

        "VkBot_errors": {
            "handlers": ["file_handler_errors", "stream_handler"],
            "level": "DEBUG",
        },
        "VkBot_talk": {
            "handlers": ["file_handler_talk"],
            "level": "DEBUG",
        },
        # "main": {
        #     "handlers": ["file_handler_main"],
        #     "level": "DEBUG",
        # }
        "vk_api": {
            "handlers": ["file_handler_vk_api"],
            "level": "DEBUG",
        },
        "property": {
            "handlers": ["file_handler_property"],
            "level": "DEBUG",
        },
        "root": {
            "handlers": ["file_handler_main"],
            "level": "DEBUG",
        }
    },
}

# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)  # or whatever
# handler = logging.FileHandler('logs/main.log', 'a+', 'utf-8')  # or whatever
# formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s %(name)s', "%Y-%m-%d %H:%M:%S")
# handler.setFormatter(formatter)
# root_logger.addHandler(handler)


# logging.basicConfig(level=logging.DEBUG, filename='logs/main.log', )

logging.config.dictConfig(log_config)
exp_log = logging.getLogger('VkBot_errors')
talk_log = logging.getLogger('VkBot_talk')
prop_log = logging.getLogger('property')
# logging.root = logging.getLogger('main')
# logging.root = logging.getLogger('__name__')

# log.setLevel(logging.DEBUG)
# fh = logging.FileHandler('logs/VkBot_info.log')
# formatter = logging.Formatter('%(levelname)s %(asctime)s   %(name)s  %(message)s')
# fh.setFormatter(formatter)
# log.addHandler(fh)
