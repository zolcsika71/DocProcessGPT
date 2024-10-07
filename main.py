import sys
import os
from app import app
from logging_config import logger
from config import PROJECT_ROOT


# Use the logger from LoggerManager

logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")


if __name__ == "__main__":
    print("About to start Flask app...")
    try:
        app.run(host="0.0.0.0", port=5001, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask app: {e}")
        print(f"Failed to start Flask app: {e}")
