# Variable Star Finder Library

VarStarFinder is a library that provides potential observing times for variable stars by leveraging the AAVSO API and
scraping the ephemeris data that is currently inaccessible via the API.

Below is an example of requesting potential observing times for eclipsing binaries from the Macquarie University
observatory and exporting it to an xlsx file. It leverages the .env file to hold the API_KEY variable for security purposes. 

```python
import os
from dotenv import load_dotenv  # python-dotenv
import varstarfinder as vsf


load_dotenv()
API_KEY = os.environ.get("API_KEY")

if API_KEY is None:
    raise OSError("Missing API_KEY in environment variables.")

config = vsf.Config(API_KEY, latitude=-33.7738, longitude=151.1126, elevation=61, ut_offset=10,
                    obs_section=["eb"], observable=True)

data = vsf.get_observing_times(config, "./star_selection.xlsx")

```

### Installing
By default, this package will be built as a tar.gz file in the `dist` folder. To do so, run the following commands:
```
pip install build
python3 -m build
```

To then add it to your own project, install it using
```
pip install "path/to/file/varstarfinder-0.0.1.tar.gz"
```
