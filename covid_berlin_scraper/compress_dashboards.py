import logging
from pathlib import Path

from covid_berlin_scraper.model import (
    Dashboard, DashboardStore, UncompressedDashboardStore,
)

logger = logging.getLogger(__name__)


def main(cache_path: Path, config: dict):
    db_path = db_path = cache_path / 'db.sqlite3'
    uncompressed_dashboard_store = UncompressedDashboardStore(db_path)
    dashboard_store = DashboardStore(db_path)
    for uncompressed_dashboard_id in uncompressed_dashboard_store.list_ids():
        uncompressed_dashboard = uncompressed_dashboard_store.find_one(
            uncompressed_dashboard_id
        )
        dashboard = Dashboard.from_uncompressed_dashboard(
            uncompressed_dashboard
        )
        dashboard_store.append(dashboard)
