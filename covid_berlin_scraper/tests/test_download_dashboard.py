import datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import dateutil.tz
import regex

from covid_berlin_scraper.download_dashboard import download_dashboard

dashboard_f = (Path(__file__).parent / 'test_data' / 'corona.html.gz').open(
    'rb'
)


class TestDownloadDashboard(TestCase):
    @patch(
        'covid_berlin_scraper.download_dashboard.http_get_raw',
        return_value=dashboard_f,
    )
    def test_download_dashboard(self, patched_http_get):
        default_tz = dateutil.tz.gettz('Europe/Berlin')
        dashboard = download_dashboard(
            url='foo',
            date_selector='.toptitle.h1 p',
            date_regex=regex.compile(
                'Lagebericht (?P<date>\\d+\\.\\d+\\.\\d+)'
            ),
            date_regex_group='date',
            default_tz=default_tz,
            timeout=10,
            user_agent='Spam',
        )
        self.assertEqual(
            dashboard.timestamp,
            datetime.datetime(year=2022, month=5, day=28, tzinfo=default_tz),
        )
        dashboard_f.seek(0)
        self.assertEqual(dashboard.content, dashboard_f.read())
