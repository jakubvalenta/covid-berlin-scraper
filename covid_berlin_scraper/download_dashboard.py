import datetime
import logging
from pathlib import Path

import dateutil.tz
import regex
from bs4 import BeautifulSoup

from covid_berlin_scraper.model import Dashboard, DashboardStore
from covid_berlin_scraper.utils.http_utils import http_get
from covid_berlin_scraper.utils.parse_utils import parse_datetime

logger = logging.getLogger(__name__)


def download_dashboard(
    url: str,
    date_selector: str,
    date_regex: regex.Regex,
    date_regex_group: str,
    default_tz: datetime.tzinfo,
    **http_kwargs,
) -> Dashboard:
    content = http_get(url, **http_kwargs)
    soup = BeautifulSoup(content, 'lxml')
    date_line = soup.select(date_selector)[0].contents[0]
    m = date_regex.search(date_line)
    date_str = m.group(date_regex_group)
    return Dashboard(
        timestamp=parse_datetime(date_str, default_tz),
        content=content,
    )


def save_dashboard(dashboard: Dashboard, db_path: Path):
    dashboard_store = DashboardStore(db_path)
    dashboard_store.append(dashboard)


def main(cache_path: Path, config: dict):
    default_tz = dateutil.tz.gettz(config['download_feed']['default_tz'])
    if not default_tz:
        raise Exception('Invalid time zone')
    dashboard = download_dashboard(
        url=config['download_dashboard']['url'],
        date_selector=config['parse_dashboard']['date_selector'],
        date_regex=regex.compile(config['parse_dashboard']['date_regex']),
        date_regex_group=config['parse_dashboard']['date_regex_group'],
        default_tz=default_tz,
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
    )
    save_dashboard(dashboard, db_path=cache_path / 'db.sqlite3')
