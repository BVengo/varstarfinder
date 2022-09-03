import re
from datetime import datetime, timedelta


def _convert_to_date(date: str) -> datetime | None:
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


def _offset_time(t: datetime, ut_offset: int):
    if t is None or isinstance(t, float):
        return None

    # TODO: pinpoint why some dates become strings despite earlier formatting
    if isinstance(t, str):
        t = _convert_to_date(t)

    return t + timedelta(hours=ut_offset)