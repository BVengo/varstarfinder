from warnings import warn


class Config:
    def __init__(self, api_key: str, latitude: float, longitude: float, elevation: float, ut_offset: int, **kwargs):
        """
        Holds all configurations for the API queries and positional information.
        See the 'GET targets' section of https://filtergraph.com/aavso/api for other parameter input options.

        :param API_KEY: an API key for accessing the AAVSO API - make an account at the link above to generate one
        :param latitude: angular distance north (+) or south (-) of the earth's equator, expressed as a float
        :param longitude: angular distance east (+) or west (-) of the earth's equator, expressed as a float
        :param elevation: elevation in metres
        :param ut_offset:
        :param kwargs: Other parameters for the API request to the AAVSO Target Tool database
        """
        self.API_KEY = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.ut_offset = ut_offset

        self._extract_params(latitude, longitude, **kwargs)

    def _extract_params(self, latitude: float, longitude: float, **kwargs):
        self.params = {
            "obs_section": None,
            "observable": None,
            "orderby": None,
            "reverse": None,
            "latitude": latitude,
            "longitude": longitude,
            "targetaltitude": None,
            "sunaltitude": None,
            "time": None
        }

        missing_params = []
        for key in self.params.keys():
            if key in kwargs:
                self.params[key] = kwargs[key]
            elif self.params[key] is None:
                missing_params.append(key)

        if len(missing_params) > 0:
            warn(f"Missing API parameters: {missing_params}")

        self.params = {key: value for key, value in self.params.items() if value is not None}