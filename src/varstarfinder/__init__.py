"""
Variable Star Finder Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VarStarFinder is a library that provides potential observing times for variable stars by leveraging the AAVSO API and
scraping the ephemeris data that is currently inaccessible via the API.

Below is an example of exporting potential observing times for eclipsing binaries and generating their staralt plots.
The location parameters used correspond to the Macquarie University, and further filters are for demonstration
purposes.

>>> import varstarfinder as vsf
>>>
>>>
>>> API_KEY = 'AN API KEY'
>>> out_dir = "./out"
>>>
>>> config = vsf.Config(API_KEY, latitude=-33.7738, longitude=151.1126, ut_offset=10,
...                     obs_section=['eb'], observable = True)
>>>
>>> data = vsf.VSFFrame(config) \
...     .request_targets() \
...     .filter_targets(dec_range = [-90, 0]) \
...     .scrape_ephemeris() \
...     .filter_ephemeris(
...         date_range = ["2022-09-19", "2022-10-10"],
...         time_range = ["19:30", "00:00"],
...         transit_range = [0.0, 6.0],
...         export = f"{out_dir}/data.xlsx") \
...     .scrape_staralt_plots(group = 'start', export = out_dir)

:copyright: (c) 2022 by Benjamin van de Vorstenbosch.
:license: MIT, see LICENSE for more details.
"""
from .__version__ import __title__, __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__, __copyright__

from .vsfframe import VSFFrame
from .config import Config
from .exceptions import OrderError
