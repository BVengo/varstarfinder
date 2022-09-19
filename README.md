# Variable Star Finder Library
VarStarFinder is a library that provides potential observing times for variable stars by leveraging the AAVSO API and
scraping the ephemeris data that is currently inaccessible via the API. It also adds functionality to generate staralt
plots using http://catserver.ing.iac.es/staralt/.

Below is an example of exporting potential observing times for eclipsing binaries and generating their staralt plots.
The location parameters used correspond to the Macquarie University, and further filters are for demonstration
purposes. It also leverages the .env file holding the API_KEY variable for secure usage. 

```python
# Imports
from dotenv import load_dotenv
import os
import varstarfinder as vsf


# Loading API variables
load_dotenv()
API_KEY = os.environ.get("API_KEY")

if API_KEY is None:
    raise OSError("Missing API_KEY in environment variables.")

# Setup directories
out_dir = "./out"

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Setup config containing the API key, observing location parameters, and optional API request parameters
config = vsf.Config(API_KEY, latitude=-33.7738, longitude=151.1126, elevation=61, ut_offset=10,
                    obs_section=["eb"], observable=True)


# Exporting data
# --------------
# Each function builds upon the previous datasets, allowing partial sets of data to be accessed. Additional
# filtering functions have also been provided to assist with maintaining a simple data flow without
# needing to break out for extra adjustments to the interim datasets.
data = vsf.VSFFrame(config) \
    .request_targets() \
    .filter_targets(dec_range = [-90, 0]) \
    .scrape_ephemeris() \
    .filter_ephemeris(
        date_range = ["2022-09-19", "2022-10-10"],
        time_range = ["19:30", "00:00"],
        transit_range = [0.0, 6.0],
        export = f"{out_dir}/data.xlsx") \
    .scrape_staralt_plots(group = 'start', export = out_dir)
```

### Installing
By default, this package will be built as a tar.gz file in the `dist` folder. To do so, run the following commands:
```bash
pip install build
python3 -m build
```

To then add it to your own project, install it using
```bash
pip install "path/to/file/varstarfinder-0.0.1.tar.gz"
```
