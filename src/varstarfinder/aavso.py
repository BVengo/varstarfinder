import json
import re
from warnings import warn

import pandas as pd
import requests
from .config import Config


def request_api_dict(config: Config, export: str = None) -> pd.DataFrame:
    """
    Requests the raw data from the AAVSO Targets Database.
    :param config: A Config object containing locational data and API parameters
    :param export: A JSON file to export the dataframe to
    :return: an HTTP requests response
    """
    response = requests.get("https://filtergraph.com/aavso/api/v1/targets",
                            auth=(config.API_KEY, "api_token"),
                            params=config.params)

    targets_json = response.json()['targets']
    targets = pd.json_normalize(targets_json)

    if export is not None:
        with open(export, "w") as f:
            json.dump(targets_json, f, indent=4)

    return targets


def _extract_url(row) -> str | None:
    # The ephemeris url is stored in the 'other_info' column, if it exists
    notes = row['other_info']
    if notes is None:
        return None

    url = re.findall(r"https://www.aavso.org/vsx/index.php\?view=detail.ephemeris[^\s|\]]*", notes)

    if url is None or len(url) == 0:
        return None

    if len(url) > 1:
        warn("Multiple ephemeris URL values found, and functionality has not been provided for this. "
             "Taking the first only.")

    return url[0]