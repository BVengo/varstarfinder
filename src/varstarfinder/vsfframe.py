from __future__ import annotations

import os
import time
from urllib.request import urlopen
from warnings import warn
from bs4 import BeautifulSoup
from os.path import abspath
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import numpy as np
import requests

from .config import Config
from ._utils import *
from .exceptions import OrderError


class VSFFrame:
    def __init__(self, config: Config, func_flags: dict = None, *args, **kwargs):
        """
        A wrapper for the Pandas DataFrame class that provides decorators and flags specific to the VarStarFinder
        datasets.
        :param config: A Config object containing all the relevant observing options
        :param func_flags: A dictionary of flags provided internally by VSFFrame to track function calls -
            not to be used manually.
        :param data: Existing data to be stored in the dataframe
        """
        self.data = pd.DataFrame(*args, **kwargs)
        self._config = config
        self._func_flags = func_flags if func_flags is not None else {
            "request_targets": False,
            "scrape_ephemeris": False,
            "scrape_staralt": False
        }

    def request_targets(self, export: str = None) -> VSFFrame:
        """
        Requests the target data from https://filtergraph.com/aavso using the provided API.
        :param export: A path to export the dataset as an xlsx file
        :return: The targets dataset
        """
        # Request data and transform into pandas DataFrame
        response = requests.get("https://filtergraph.com/aavso/api/v1/targets",
                                auth=(self._config.API_KEY, "api_token"),
                                params=self._config.params)

        targets_json = response.json()['targets']
        targets = pd.json_normalize(targets_json)

        # Export to xlsx
        if export is not None:
            with open(export, "w") as f:
                targets.to_excel(export, index=False)

        # Set function flag so future functions know this has been run
        self._func_flags['request_targets'] = True

        return VSFFrame(self._config, self._func_flags, data=targets)

    @staticmethod
    def _extract_ephemeris_url(value: str) -> str | None:
        """
        Returns the ephemeris URL from a string (if it exists)
        :param value: A string that may contain the URL to ephemeris data
        :return: The ephemeris data URL
        """
        if value is None:
            return None

        url = re.findall(r"https://www.aavso.org/vsx/index.php\?view=detail.ephemeris[^\s|\]]*", value)

        if url is None or len(url) == 0:
            return None

        if len(url) > 1:
            warn("Multiple ephemeris URL values found, and functionality has not been provided for this. "
                 "Taking the first only.")

        return url[0]

    @staticmethod
    def _scrape_star_ephemeris(star_name: str, url: str) -> pd.DataFrame | None:
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
            vals[col] = [convert_to_date(d) for d in vals[col]]

        return vals

    def filter_targets(self, star_names: list[str] = None, dec_range: list[float, float] = None,
                       ra_range: list[float, float] = None, export: str = None) -> VSFFrame:
        """
        Filters the targets data
        :param star_names: A list of stars to be targeted
        :param dec_range: A declination range (inclusive)
        :param ra_range: A right ascension range (inclusive)
        :param export: A path to export the dataset as an xlsx file
        :return: The filtered dataset
        """
        # Check previous function call ran successfully
        prev_function = "request_targets"
        if not self._func_flags[prev_function]:
            raise OrderError(self._func_flags, prev_function)

        # Filter dataset based on the parameters provided
        filtered = self.data.copy()

        if star_names is not None:
            filtered = filtered[filtered['star_name'].isin(star_names)]

        if dec_range is not None:
            filtered = filtered[filtered.apply(lambda row: in_range(row['dec'], dec_range), axis=1)]

        if ra_range is not None:
            filtered = filtered[filtered.apply(lambda row: in_range(row['ra'], ra_range), axis=1)]

        # Export to xlsx
        if export is not None:
            with open(export, "w") as f:
                filtered.to_excel(export, index=False)

        return VSFFrame(self._config, self._func_flags, data=filtered)

    def scrape_ephemeris(self, export: str = None) -> VSFFrame:
        """
        Attaches the ephemeris data to the VSFFrame, provided the request_targets function has already been called.
        :param export: A path to export the dataset as an xlsx file
        :return: The ephemeris data joined to the targets dataset
        """
        # Check previous function call ran successfully
        prev_function = "request_targets"
        if not self._func_flags[prev_function]:
            raise OrderError(self._func_flags, prev_function)

        # Scrape the ephemeris data for each star
        self.data['ephemeris_url'] = self.data.apply(lambda row: self._extract_ephemeris_url(row['other_info']), axis=1)

        ephemeris_list = [pd.DataFrame(columns=["star_name", "epoch", "start", "mid", "end"])] + \
                         [self._scrape_star_ephemeris(x, y) for x, y in zip(self.data['star_name'],
                                                                            self.data['ephemeris_url'])]

        ephemeris_data = pd.concat(ephemeris_list)

        # Fix datetime formats
        date_cols = ['start', 'mid', 'end']
        for c in date_cols:
            ephemeris_data[c] = ephemeris_data[c].apply(offset_time, args=[self._config.ut_offset])

        ephemeris_data['ecliptic_period'] = ephemeris_data.apply(
            lambda row: (row['end'] - row['start']).total_seconds() / 3600, axis=1)

        self.data.drop('ephemeris_url', axis=1)
        new_dataset = self.data.merge(ephemeris_data, on="star_name", how="left")

        # Export data to xlsx
        if export is not None:
            with open(export, "w") as f:
                new_dataset.to_excel(export, index=False)

        # Set function flag so future functions know this has been run
        self._func_flags['scrape_ephemeris'] = True

        return VSFFrame(self._config, self._func_flags, data=new_dataset)

    def filter_ephemeris(self, date_range: list[str, str] = None, time_range: list[str, str] = None,
                         transit_range: list[float, float] = None, export: str = None) -> VSFFrame:
        """
        Filters the ephemeris data
        :param date_range: A date range (inclusive) based on the mid-transit date. Dates in the format "%Y-%m-%d"
        :param time_range: A time range (inclusive) based on the mid-transit time. Times in the format "%H:%M"
        :param transit_range: A length of time for the transit to occur, in hours (inclusive)
        :param export: A path to export the dataset as an xlsx file
        :return: The filtered dataset
        """
        # Check previous function call ran successfully
        prev_function = "scrape_ephemeris"
        if not self._func_flags[prev_function]:
            raise OrderError(self._func_flags, prev_function)

        # Filter dataset based on the parameters provided
        filtered = self.data.copy()

        if date_range is not None:
            filtered = filtered[filtered.apply(lambda row: in_range(row['mid'], date_range, "%Y-%m-%d"), axis=1)]

        if time_range is not None:
            filtered = filtered[filtered.apply(lambda row: in_range(row['mid'], time_range, "%H:%M"), axis=1)]

        if transit_range is not None:
            filtered = filtered[filtered.apply(lambda row: in_range(row['ecliptic_period'], transit_range), axis=1)]

        # Export to xlsx
        if export is not None:
            with open(export, "w") as f:
                filtered.to_excel(export, index=False)

        return VSFFrame(self._config, self._func_flags, data=filtered)

    def _scrape_staralt_plot(self, driver, staralt_input: dict, export: str):
        """
        Downloads a staralt plot from http://catserver.ing.iac.es/staralt/. The driver must already be on that
        page for this function to work.
        :param driver:
        :param staralt_input:
        :param export: The folder that the plot is downloaded to
        :return:
        """
        # Night date (date that the night begins)
        day_element = Select(driver.find_element(By.NAME, "form[day]"))
        day_element.select_by_visible_text(staralt_input['date'].strftime("%d"))  # 2 digit

        month_element = Select(driver.find_element(By.NAME, "form[month]"))
        month_element.select_by_visible_text(staralt_input['date'].strftime("%B"))  # Full month name

        year_element = Select(driver.find_element(By.NAME, "form[year]"))
        year_element.select_by_visible_text(staralt_input['date'].strftime("%Y"))  # Full year

        # Observatory location
        obs_element = driver.find_element(By.NAME, "form[sitecoord]")
        obs_element.clear()
        obs_element.send_keys(
            f"{self._config.longitude} {self._config.latitude} {self._config.elevation} {self._config.ut_offset}")

        # Star coordinates
        coords_element = driver.find_element(By.NAME, "form[coordlist]")
        coords_element.clear()
        coords_element.send_keys(staralt_input['coords'])

        # Export options
        format_element = Select(driver.find_element(By.NAME, "form[format]"))
        format_element.select_by_visible_text("GIF [attachment]")

        # Retrieve
        driver.find_element(By.NAME, "submit").click()

        # Rename file
        file_path = f"{export}/image.gif"

        while not os.path.exists(file_path):
            time.sleep(1)

        os.rename(file_path, f"{export}/{staralt_input['date']}.gif")

    def scrape_staralt_plots(self, export: str, group: str = 'start'):
        """
        Downloads the staralt plots for each day in the dataset. Plots are downloaded as gif files, named with the date
        they correspond to.
        :param export: The folder that the plots are downloaded to
        :param group: How the dates should be grouped. If 'start' or 'end', any stars missing that ephemeris data won't
        appear in the plots, although 'start' typically makes it easier to view them together.
        :return:
        """
        # Check previous function call ran successfully
        prev_function = "scrape_ephemeris"
        if not self._func_flags[prev_function]:
            raise OrderError(self._func_flags, prev_function)

        # Extract required staralt data, grouped by start date
        start_dates = self.data[group].dt.date.unique()
        staralt_inputs = []

        for obs_date in start_dates:
            star_data = self.data[self.data[group].dt.date == obs_date][['star_name', 'ra', 'dec']]
            star_data['star_name'] = star_data['star_name'].str.replace(' ', '_')

            star_string = star_data.to_string(header=False, index=False, index_names=False)
            star_string = re.sub("^\s+", "", star_string)

            staralt_inputs.append({"date": obs_date, "coords": star_string})

        opts = Options()
        opts.add_experimental_option("prefs", {
            "download.default_directory": abspath(export),
            "download.prompt_for_download": False
        })
        opts.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=opts, service=Service(ChromeDriverManager().install()))

        driver.get("http://catserver.ing.iac.es/staralt/")

        for staralt_input in staralt_inputs:
            self._scrape_staralt_plot(driver, staralt_input, export)

        driver.close()
