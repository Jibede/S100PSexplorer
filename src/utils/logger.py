from logging import Logger
import logging


def config_logger(name: str) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    handler = logging.StreamHandler()
    
    format_msg = '[%(levelname)s] (%(asctime)s): %(message)s'
    format_date = "%Y/%m/%d %H:%M:%S"
    format = logging.Formatter(fmt=format_msg, datefmt=format_date)
    
    handler.setFormatter(format)
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

def set_flask_logger(logger: Logger) -> None:
    wer_logger = logging.getLogger('werkzeug')
    wer_logger.handlers.clear()
    wer_logger.addHandler(logger.handlers[0])
    wer_logger.setLevel(logger.level)
    wer_logger.propagate = False
