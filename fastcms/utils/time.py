# fastcms/utils/time.py
from datetime import datetime, UTC


def current_time() -> datetime:
    """
    Returns the current time in UTC.

    :return: Current time in UTC.
    """
    return datetime.now(UTC)
