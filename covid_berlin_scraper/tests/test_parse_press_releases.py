import datetime
from pathlib import Path
from unittest import TestCase

from covid_berlin_scraper.model import Dashboard
from covid_berlin_scraper.parse_press_releases import parse_dashboard


class TestParsePressReleases(TestCase):
    def test_parse_dashboard(self):
        timestamp = datetime.datetime.now()
        content = (
            Path(__file__).parent / 'test_data' / 'corona.html.gz'
        ).read_bytes()
        dashboard = Dashboard(timestamp=timestamp, content=content)
        press_release_stats = parse_dashboard(
            dashboard,
            cases_selector='#box-fallzahl .value',
            recovered_selector='#box-genesene .value',
            deaths_selector='#box-todesfaelle .value',
            hospitalized_text='Patient*innen in stationärer Behandlung',
            icu_text='└─ ITS-Versorgung',
        )
        self.assertIs(press_release_stats.timestamp, timestamp)
        self.assertEqual(press_release_stats.cases, 1046873)
        self.assertEqual(press_release_stats.recovered, 1001066)
        self.assertEqual(press_release_stats.deaths, 4610)
        self.assertEqual(press_release_stats.hospitalized, 281)
        self.assertEqual(press_release_stats.icu, 44)
