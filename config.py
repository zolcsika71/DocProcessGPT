# config.py
import os


# Function to get environment variables with a default value
def get_env_variable(var_name, default_value=None):
    return os.getenv(var_name, default_value)


FILE_TO_PROCESS_FOLDER = get_env_variable(
    "FILE_TO_PROCESS_FOLDER", "data/file_processing/raw"
)
PROCESSED_FILE_FOLDER = get_env_variable(
    "PROCESSED_FILE_FOLDER", "data/file_processing/processed"
)
MAX_CONTENT_LENGTH = int(
    get_env_variable("MAX_CONTENT_LENGTH", 3 * 1024 * 1024 * 1024)
)  # 3GB
PROCESSING_TIMEOUT = int(get_env_variable("PROCESSING_TIMEOUT", 300))  # 5 minutes

LOG_DIRECTORY = get_env_variable("LOG_DIRECTORY")
LOG_LEVEL = get_env_variable("LOG_LEVEL", "INFO").upper()
