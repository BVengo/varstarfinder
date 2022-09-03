from warnings import warn

import ephem
import pandas as pd
from .config import Config


def get_twilight_times(config: Config, code: str, dates: list) -> pd.DataFrame:
    """
    Finds the start and end of twilight at the given times and position.

    :param config: A Config object containing locational data and API parameters
    :param code: which twilight - 'c' = civil, 'n' = nautical, 'a' = astronomical
    :param dates: A list of observational date-times in UTC
    :return: A tuple with the (start, end) date-times of twilight in UTC
    """
    obs = ephem.Observer()
    obs.lat = str(config.latitude)
    obs.lon = str(config.longitude)
    obs.elev = config.elevation

    if code == 'c':
        obs.horizon = -6
        name = 'civil'
    elif code == 'n':
        obs.horizon = -12
        name = 'nautical'
    elif code == 'a':
        name = 'astronomical'
        obs.horizon = -18
    else:
        warn("Invalid twilight code. Defaulting to astronomical twilight.")
        name = 'astronomical'
        obs.horizon = -18

    cols = [f'{name}_twilight_start', f'{name}_twilight_end']

    vals = []
    for date in dates:
        obs.date = date

        try:
            start = obs.previous_rising(ephem.Sun(), use_center=True).datetime().strftime("%Y-%m-%d %H:%M:%S")
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            start = None

        try:
            end = obs.next_setting(ephem.Sun(), use_center=True).datetime().strftime("%Y-%m-%d %H:%M:%S")
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            end = None

        vals.append((start, end))

    return pd.DataFrame(vals, columns=cols)