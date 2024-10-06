# time_utils.py
from datetime import datetime, timezone


def get_current_utc_time():
    """Return the current UTC time as a formatted string."""
    return datetime.now(timezone.utc).strftime("%m-%d %H:%M:%S")


def format_time(timestamp, datefmt=None):
    """Format a given timestamp to a specified format."""
    dt = datetime.fromtimestamp(timestamp, timezone.utc)
    if datefmt:
        return dt.strftime(datefmt)
    return dt.isoformat()
