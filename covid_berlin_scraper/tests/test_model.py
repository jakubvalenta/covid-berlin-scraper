import datetime
from unittest import TestCase

from covid_berlin_scraper.model import UncompressedDashboard


class TestModel(TestCase):
    def test_uncompressed_dashboard_content_utf8(self):
        dashboard = UncompressedDashboard(
            timestamp=datetime.datetime(2020, 10, 7),
            content='StationÃ¤re Behandlung',
        )
        self.assertEqual(dashboard.content_utf8, 'Stationäre Behandlung')

    def test_uncompressed_dashboard_content_utf8_already_converted(self):
        dashboard = UncompressedDashboard(
            timestamp=datetime.datetime(2020, 10, 7),
            content='Stationäre Behandlung',
        )
        self.assertEqual(dashboard.content_utf8, 'Stationäre Behandlung')
