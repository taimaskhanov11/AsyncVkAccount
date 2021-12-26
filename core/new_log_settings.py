import asyncio
import sys
from pathlib import Path
from pprint import pprint

import yaml
from loguru import logger

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = Path(BASE_DIR, 'new_logs')

__all__ = [
    'logger',

]

"""
elapsed	The time elapsed since the start of the program	See datetime.timedelta
exception	The formatted exception if any, None otherwise	type, value, traceback
extra 	The dict of attributes bound by the user (see bind())	None
file      The file where the logging call was made	name (default), path
function	The function from which the logging call was made	None
level  	The severity used to log the message	name (default), no, icon
line  	The line number in the source code	None
message	The logged message (not yet formatted)	None
module	The module where the logging call was made	None
name  	The __name__ where the logging call was made	None
process	The process in which the logging call was made	name, id (default)
thread	The thread in which the logging call was made	name, id (default)
time  	The aware local time when the logging call was made	See datetime.datetime

Color   (abbr)	Styles (abbr)
Black   (k)	Bold (b)
Blue    (e)	Dim (d)
Cyan    (c)	Normal (n)
Green   (g)	Italic (i)
Magenta (m)	Underline (u)
Red     (r)	Strike (s)
White   (w)	Reverse (v)
Yellow  (y)	Blink (l)
Hide  (h)


Level name	Severity value	Logger method
TRACE	    5	            logger.trace()
DEBUG	    10	            logger.debug()
INFO	    20	            logger.info()
SUCCESS	25	            logger.success()
WARNING	30	            logger.warning()
ERROR	    40	            logger.error()
CRITICAL	50	            logger.critical()

log_formatters = '2021-12-26 16:45:14.888 | TRACE    | __main__:main:238 - TRACE'
formatter = '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.name}:{level.no} | {name}:{module}:{function}:{line} | - {message} | {elapsed}'

"""


# logging.


# loop = asyncio.new_event_loop()


class MyFilter:

    def __init__(self, level):
        self.level = level

    def __call__(self, record):
        levelno = logger.level(self.level).no
        return record["level"].no == levelno


def log_configurate(log_settings):
    formatter_main = '{time:YYYY-MM-DD HH:mm:ss.SSS} |  {level.name}:{level.no} | {name}:{function}:{line} | - {message} | {elapsed}'
    formatter = '{level.name}:{level.no} | {message}'
    # print(log_settings)
    handlers = [dict(sink=sys.stderr, filter=MyFilter(LEVELNAME), level=LEVELNAME, enqueue=True, diagnose=True)
                for LEVELNAME, boolean in log_settings.items() if boolean
                ]

    # levels = [
    #     # 'NEW_MESSAGE',
    #     # 'SPAN_MESSAGE',
    #     # 'TRACE',
    #     'DEBUG',
    #     # 'INFO',
    #     'SUCCESS',
    #     'WARNING',
    #     # 'ERROR',
    #     'CRITICAL',
    #     'XANSWER',
    #     'TALK'
    # ]

    # handlers = [
    #     dict(
    #         # sink=sys.stderr,
    #         sink=f"{LOG_DIR}/{level_name.lower()}.log",
    #         format=formatter,
    #         filter=MyFilter(level_name),
    #         level=level_name,
    #         enqueue=True,
    #         colorize=True,
    #         # encoding='utf-8',
    #         diagnose=True)
    #     for level_name in levels]

    logger.configure(
        handlers=[
            # *handlers,

            dict(sink=f"{LOG_DIR}/xanswer.log", filter=MyFilter('XANSWER'), level='XANSWER', enqueue=True,
                 encoding='utf-8', diagnose=True),
            dict(sink=f"{LOG_DIR}/talk.log", filter=MyFilter('TALK'), encoding='utf-8', level='TALK', enqueue=True,
                 diagnose=True),
            dict(sink=f"{LOG_DIR}/debug.log", filter=MyFilter('DEBUG'), level='DEBUG', enqueue=True, encoding='utf-8',
                 diagnose=True),
            dict(sink=f"{LOG_DIR}/info.log", filter=MyFilter('INFO'), level='INFO', enqueue=True, encoding='utf-8',
                 diagnose=True),
            dict(sink=f"{LOG_DIR}/success.log", filter=MyFilter('SUCCESS'), level='SUCCESS', enqueue=True,
                 encoding='utf-8', diagnose=True),
            dict(sink=f"{LOG_DIR}/warning.log", filter=MyFilter('WARNING'), level='WARNING', enqueue=True,
                 encoding='utf-8', diagnose=True),
            dict(sink=f"{LOG_DIR}/error.log", filter=MyFilter('ERROR'), level='ERROR', enqueue=True, encoding='utf-8',
                 diagnose=True),
            dict(sink=f"{LOG_DIR}/critical.log", filter=MyFilter('CRITICAL'), level='CRITICAL', enqueue=True,
                 encoding='utf-8', diagnose=True),
            dict(sink=f'{LOG_DIR}/trace.log', level='TRACE', format=formatter_main, enqueue=True, encoding='utf-8',
                 diagnose=True),
            # dict(sys.stdout, level='TRACE', enqueue=True, diagnose=True),

            # dict(sink=sys.stderr, format=formatter, filter=MyFilter('NEW_MESSAGE'), level='NEW_MESSAGE', enqueue=True,
            #      encoding='utf-8', diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('SPAN_MESSAGE'), level='SPAN_MESSAGE', enqueue=True, encoding='utf-8',
            #      diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('TRACE'), level='TRACE', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, level='INFO',format=formatter, enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, level='TRACE', enqueue=True, diagnose=True),

            *handlers,
            # dict(sink=sys.stderr, filter=MyFilter('DEBUG'), level='DEBUG', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('INFO'), level='INFO', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('TALK'), level='TALK', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('XANSWER'), level='XANSWER', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('SUCCESS'), level='SUCCESS', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('WARNING'), level='WARNING', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('ERROR'), level='ERROR', enqueue=True, diagnose=True),
            # dict(sink=sys.stderr, filter=MyFilter('CRITICAL'), level='CRITICAL', enqueue=True, diagnose=True),

        ],

        levels=[
            # dict(name="NEW_MESSAGE", no=5, icon="¤", color="<magenta>"),
            # dict(name="SPAN_MESSAGE", no=5, icon="¤", color=""),

            dict(name="TALK", no=21, icon="¤", color="<green>"),
            dict(name="XANSWER", no=22, icon="¤", color="<magenta>"),
            # dict(name="TRACE", no=5, icon="¤", color="<magenta>"),
            # dict(name="NEW3", no=19, icon="¤", color="<yellow><bold>"),
            # dict(name="NEW4", no=19, icon="¤", color="<yellow><bold>"),
        ],

        # extra={"common_to_all": "default"},
        # patcher=lambda record: record["extra"].update(some_value=42),
        # activation=[("my_module.secret", False), ("another_library.module", True)],
    )


# my_filter = MyFilter("WARNING")
# logger.add(sys.stderr, filter=my_filter, level=0)
#
# logger.warning("OK")
# logger.debug("NOK")
#
# my_filter.level = "DEBUG"
# logger.debug("OK")


async def main():
    logger.trace('TRACE')
    logger.debug('DEBUG')
    logger.info('INFO')
    logger.success('SUCCESS')
    logger.warning('WARNING')
    logger.error('ERROR')
    logger.critical('CRITICAL')
    logger.log('XANSWER', 'XANSWER')
    logger.log('TALK', 'TALK')

    # logger.log('SPAN_MESSAGE', 'SPAN_MESSAGE')
    # logger.log('NEW_MESSAGE', 'NEW_MESSAGE')


def read_yaml(path):
    # print(path)
    with open(Path(BASE_DIR, path), 'r', encoding='utf-8-sig') as fh:
        return yaml.safe_load(fh)


if __name__ == '__main__':
    settings = read_yaml('config/settings.yaml')

    # main()
    log_configurate(settings['log_settings'])
    asyncio.run(main())

# logging.config.dictConfig(log_config)
# exp_log = logging.getLogger('errors')
# talk_log = logging.getLogger('talk')
# prop_log = logging.getLogger('property')
# not_answer_log = logging.getLogger('not_found_answer')
