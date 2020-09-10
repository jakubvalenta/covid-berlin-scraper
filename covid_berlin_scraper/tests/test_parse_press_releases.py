import datetime
from pathlib import Path
from unittest import TestCase

from covid_berlin_scraper.model import Dashboard
from covid_berlin_scraper.parse_press_releases import parse_dashboard


class TestParsePressReleases(TestCase):
    def test_parse_dashboard(self):
        timestamp = datetime.datetime.now()
        content = (
            Path(__file__).parent / 'test_data' / 'corona.html'
        ).read_text()
        dashboard = Dashboard(timestamp=timestamp, content=content)
        press_release_stats = parse_dashboard(
            dashboard,
            cases_selector='#box-fallzahl .value',
            recovered_selector='#box-genesene .value',
            deaths_selector='#box-todesfaelle .value',
        )
        self.assertIs(press_release_stats.timestamp, timestamp)
        self.assertEqual(press_release_stats.cases, 12089)
        self.assertEqual(press_release_stats.recovered, 11012)
        self.assertEqual(press_release_stats.deaths, 226)
        self.assertIsNone(press_release_stats.hospitalized)
        self.assertIsNone(press_release_stats.icu)
