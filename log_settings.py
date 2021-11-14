import logging.config

from pathlib import Path

LOG_DIR = Path(Path(__file__).parent, 'logs')

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

logging.config.dictConfig(log_config)
exp_log = logging.getLogger('VkBot_errors')
talk_log = logging.getLogger('VkBot_talk')
prop_log = logging.getLogger('property')
