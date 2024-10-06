# logging_config.py
import os
import logging
from logging import Formatter
from logging.config import dictConfig
from colorlog import ColoredFormatter


def setup_logging(log_directory="logs"):
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
        datefmt="%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(os.path.join(log_directory, "app.log"))
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
            "%m-%d %H:%M:%S",
        )
    )
    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler])
