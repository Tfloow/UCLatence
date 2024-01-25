import logging

LOG_FORMAT = '%(asctime)s - [%(levelname)s]\t- %(funcName)s:%(lineno)d - %(threadName)s - %(message)s'
logging.root.setLevel(logging.DEBUG)


logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
)

logger = logging.getLogger("UCLouvain-Down")

file_handler = logging.FileHandler('my_log.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


if __name__ == "__main__":
    # Log some messages at different levels
    logger.debug('This is a DEBUG message')
    logger.info('This is an INFO message')
    logger.warning('This is a WARNING message')
    logger.error('This is an ERROR message')
    logger.critical('This is a CRITICAL message')