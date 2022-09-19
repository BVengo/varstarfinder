from __future__ import annotations
from datetime import datetime, timedelta
import re
import pandas as pd


def in_range(val, value_range: list, date_format: str = None) -> bool:
    """
    Determines if a value lies within a given range [start, end] inclusive.
    If val is a datetime value, please provide str value ranges and provide the date_format parameter.

    :param val: The variable to be checked
    :param value_range: The bounding range (inclusive)
    :param date_format: Formats for date or time ranges
    :return:
    """
    if val is None or pd.isna(val):
        return False

    if isinstance(val, int) or isinstance(val, float):
        return value_range[0] <= val <= value_range[1]

    if isinstance(val, datetime) and date_format is not None:
        start = datetime.strptime(value_range[0], date_format)
        end = datetime.strptime(value_range[1], date_format)

        if not re.match("%H", date_format):  # is a date range
            return start <= val <= end

        # is a time range
        midnight = datetime.strptime("00:00", "%H:%M").time()
        time_val = val.time()
        start = start.time()
        end = end.time()

        # No looping over midnight
        if start <= end <= midnight:
            return start <= time_val <= end

        # Range loops over midnight
        return (end <= start <= time_val) or (time_val <= end <= start)

    return False


def convert_to_date(date: str) -> datetime | None:
    if isinstance(date, float):
        return None

    # These should be the only date formats seen in the datasets
    if re.search(r"^[0-9]{2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}$", date):
        date = datetime.strptime(date, '%d %b %Y %H:%M').strftime("%Y-%m-%d %H:%M")
    elif re.search(r"^[0-9]{2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}$", date):
        date = datetime.strptime(date, '%d %b %Y %H:%M:%S').strftime("%Y-%m-%d %H:%M:%S")
    elif re.search(r"^[0-9]{2} [A-Za-z]{3} [0-9]{4}$", date):
        date = datetime.strptime(date, '%d %b %Y').strftime("%Y-%m-%d")
    elif re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$", date):
        date = datetime.strptime(date, "%Y-%m-%d %H:%M")
    elif re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", date):
        date = datetime.strptime(date, "%Y-%m-%d")
    elif re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$", date):
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    else:
        raise ValueError(f"Invalid date format for {date}")

    return date


def offset_time(t: datetime, ut_offset: int) -> datetime | None:
    if t is None or isinstance(t, float):
        return None

    if isinstance(t, str):
        t = convert_to_date(t)

    return t + timedelta(hours=ut_offset)
