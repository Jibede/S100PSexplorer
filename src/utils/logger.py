from logging import Logger
import logging


def config_logger(name: str) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Création d'un handler pour la console
    handler = logging.StreamHandler()
    
    format_msg = '[%(levelname)s] (%(asctime)s): %(message)s'
    format_date = "%Y/%m/%d %H:%M:%S"
    format = logging.Formatter(fmt=format_msg, datefmt=format_date)
    
    handler.setFormatter(format)
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger