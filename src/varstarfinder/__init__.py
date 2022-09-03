"""
Variable Star Finder Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VarStarFinder is a library that provides potential observing times for variable stars by leveraging the AAVSO API and
scraping the ephemeris data that is currently inaccessible via the API.

Below is an example of requesting potential observing times for eclipsing binaries from the Macquarie University
observatory and exporting it to an xlsx file..
   >>> import varstarfinder as vsf
   >>> API_KEY = 'AN API KEY'
   >>> c = vsf.Config(API_KEY, latitude=-33.7738, longitude=151.1126, elevation=61, ut_offset=10,
   ...                obs_section=['eb'], observable = True)
   >>> data = vsf.get_observing_times(c, './observing_times.xlsx')

:copyright: (c) 2022 by Benjamin van de Vorstenbosch.
:license: MIT, see LICENSE for more details.
"""
import pandas as pd

from .__version__ import __title__, __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__, __copyright__

from .config import Config
from .datehandler import _convert_to_date, _offset_time
from .aavso import request_api_dict, _extract_url
from .ephemeris import _get_ephemeris_data
from .twilight import get_twilight_times


def get_observing_times(config: Config, file:str = None) -> pd.DataFrame:
    """
    Generates a DataFrame of observing times for variable stars based on the parameters provided to Config. This
    includes all ephemeris data and astronomical twilight times.

    :param config: A Config object containing locational data and API parameters
    :param file: The xlsx file that the data should be exported to. Will overwrite existing files.
    :return:
    """
    targets = request_api_dict(config)
    targets['ephemeris_url'] = targets.apply(lambda row: _extract_url(row), axis=1)

    ephemeris = _get_ephemeris_data(targets)
    twilight_times = get_twilight_times(config, 'a', ephemeris['mid'])

    ephemeris = ephemeris.join(twilight_times)

    data = targets.merge(ephemeris, on="star_name", how="left")

    data.to_excel("./out/pre_dates.xlsx")

    # Adjust dates to correct timeframe. Hardcoded date columns because they're all dtype 'object', so can't be
    # differentiated between without extensive and (quite likely slow) column checks
    date_cols = ['start', 'mid', 'end', 'astronomical_twilight_start', 'astronomical_twilight_end']
    for c in date_cols:
        data[c] = data[c].apply(_offset_time, args=[config.ut_offset])

    if file is not None:
        # Check if directory exists. If not, ask user if they want it created else the program will end.
        data.to_excel(file)

    return data
