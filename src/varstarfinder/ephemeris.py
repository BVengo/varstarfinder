from urllib.request import urlopen

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from .datehandler import _convert_to_date


def scrape_ephemeris(star_name: str, url: str) -> pd.DataFrame | None:
    """
    Scrapes the ephemeris data at the given URL, formatting it into a usable pandas DataFrame

    :param star_name: The name of the star, taken from the original dataset. Used as a joining ID
    :param url: The url of the ephemeris data, taken from the original dataset.
    :return: A Pandas DataFrame containing the ephemeris data of a star (if it exists)
    """
    if url is None:
        return None

    content = urlopen(url).read()

    soup = BeautifulSoup(content, 'html.parser')

    # Get all table values, and remove the header / footer values
    vals = [element.text for element in soup.find_all("td")][3:-2]
    row_length = vals.index("")

    vals = list(filter(lambda val: val != "", vals))

    # Remove titles and reshape into columns
    cols = [str.lower(x) for x in vals[0:row_length]]
    cols.insert(0, "star_name")

    vals = vals[row_length:]
    vals = np.reshape(vals, (-1, row_length))

    id_col = np.full(vals.shape[0], star_name)
    vals = np.concatenate((id_col[:, np.newaxis], vals), axis=1)

    vals = pd.DataFrame(columns=cols, data=vals)

    # Fix date formats (exclude ID and epoch column)
    for col in cols[2:]:
        vals[col] = [_convert_to_date(d) for d in vals[col]]

    return vals


def _get_ephemeris_data(targets: pd.DataFrame) -> pd.DataFrame:
    ephemeris_list = [pd.DataFrame(columns=["star_name", "epoch", "start", "mid", "end"])] + \
                     [scrape_ephemeris(x, y) for x, y in zip(targets['star_name'], targets['ephemeris_url'])]

    return pd.concat(ephemeris_list)