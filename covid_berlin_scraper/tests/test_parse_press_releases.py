import datetime
from pathlib import Path
from unittest import TestCase

from ddt import data, ddt, unpack

from covid_berlin_scraper.model import Dashboard
from covid_berlin_scraper.parse_press_releases import parse_dashboard


@ddt
class TestParsePressReleases(TestCase):
    @data(
        [
            'corona.html.gz',
            {
                'cases': 1046873,
                'recovered': 1001066,
                'deaths': 4610,
                'hospitalized': 281,
                'icu': 44,
            },
        ],
        [
            'corona-230827.html.gz',
            {
                'cases': 1442300,
                'recovered': None,
                'deaths': 5834,
                'hospitalized': None,
                'icu': None,
            },
        ],
    )
    @unpack
    def test_parse_dashboard(self, filename, expected_dict):
        timestamp = datetime.datetime.now()
        content = (Path(__file__).parent / 'test_data' / filename).read_bytes()
        dashboard = Dashboard(timestamp=timestamp, content=content)
        press_release_stats = parse_dashboard(
            dashboard,
            cases_selectors=[
                '#box-fallzahl .value',
                (
                    '#fallzahlen-berlin tbody tr:nth-of-type(1) '
                    'td:nth-of-type(5) span'
                ),
            ],
            recovered_selectors=['#box-genesene .value'],
            deaths_selectors=[
                '#box-todesfaelle .value',
                (
                    '#fallzahlen-berlin tbody tr:nth-of-type(3) '
                    'td:nth-of-type(5) span'
                ),
            ],
            hospitalized_selectors=[
                (
                    '#selbstauskunft-der-krankenhäuser-in-ivena '
                    'tbody tr:nth-of-type(1) td:nth-of-type(2) span'
                )
            ],
            icu_selectors=[
                (
                    '#selbstauskunft-der-krankenhäuser-in-ivena '
                    'tbody tr:nth-of-type(3) td:nth-of-type(2) span'
                )
            ],
        )
        self.assertIs(press_release_stats.timestamp, timestamp)
        for prop, value in expected_dict.items():
            self.assertEqual(getattr(press_release_stats, prop), value)
