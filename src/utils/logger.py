from logging import Logger
import logging

def color_filter(record):
    colors = {
        logging.DEBUG: "\033[90m",      # Gris
        logging.WARNING: "\033[93m",    # Jaune
        logging.ERROR: "\033[91m",      # Rouge
        logging.CRITICAL: "\033[1;91m"  # Rouge 
    }
    
    record.color = colors.get(record.levelno, "\033[0m")
    record.reset = "\033[0m"
    
    return True


def config_logger(name: str) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        handler = logging.StreamHandler()

        handler.addFilter(color_filter)
        
        format_msg = '%(color)s[%(levelname)s] (%(asctime)s): %(message)s'
        format_date = "%Y/%m/%d %H:%M:%S"
        
        format = logging.Formatter(fmt=format_msg, datefmt=format_date)
        handler.setFormatter(format)
        
        logger.addHandler(handler)
        
    return logger


def set_flask_logger(logger: Logger) -> None:
    wer_logger = logging.getLogger('werkzeug')
    wer_logger.handlers.clear()
    wer_logger.addHandler(logger.handlers[0])
    wer_logger.setLevel(logger.level)
    wer_logger.propagate = False
