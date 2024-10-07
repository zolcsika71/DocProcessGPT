# logging_config.py
import logging
import os
from colorlog import ColoredFormatter
from config import LOG_DIRECTORY, LOG_LEVEL
import uuid
import glob


def cleanup_old_logs(current_run_id):
    """
    Deletes old log files that are not associated with the current server run.
    Keeps only the log files related to the current run, identified by current_run_id.
    """
    for log_file in glob.glob(os.path.join(LOG_DIRECTORY, "app_*.log")):
        if current_run_id not in log_file:
            try:
                os.remove(log_file)
                print(
                    f"Deleted old log file: {log_file}"
                )  # Use print as logging might not be set up yet
            except OSError as e:
                print(f"Error deleting file {log_file}: {e}")


def setup_logging():
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    # Generate a unique identifier for this run
    current_run_id = str(uuid.uuid4())  # Using UUID for uniqueness
    log_filename = f"app_{current_run_id}.log"

    print(f"Log file will be: {log_filename}")

    # Remove old logs not connected to the current server run
    cleanup_old_logs(current_run_id)

    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)s [%(module)s]: %(message)s [in %(pathname)s:%(lineno)d]",
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
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    file_handler = logging.FileHandler(os.path.join(LOG_DIRECTORY, log_filename))
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(module)s]: %(message)s [in %(pathname)s:%(lineno)d]",
            "%m-%d %H:%M:%S",
        )
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    logger_setup = logging.getLogger(__name__)
    logger_setup.setLevel(getattr(logging, LOG_LEVEL))
    logger_setup.addHandler(console_handler)
    logger_setup.addHandler(file_handler)

    return logger_setup


# Initialize the logger
logger = setup_logging()
