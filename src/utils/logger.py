from logging import Logger
import logging


def config_logger(name: str) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Création d'un handler pour la console
    handler = logging.StreamHandler()
    format = logging.Formatter('[%(levelname)s] (%(asctime)s) # %(message)s')
    handler.setFormatter(format)
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger