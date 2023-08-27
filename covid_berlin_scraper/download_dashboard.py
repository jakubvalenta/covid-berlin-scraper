import datetime
import gzip
import logging
from pathlib import Path
from typing import Iterable

import dateutil.tz
import regex
from bs4 import BeautifulSoup

from covid_berlin_scraper.model import Dashboard, DashboardStore
from covid_berlin_scraper.utils.http_utils import http_get_raw

logger = logging.getLogger(__name__)


def download_dashboard(
    url: str,
    date_selector: str,
    date_regex: regex.Pattern,
    date_regex_group: str,
    default_tz: datetime.tzinfo,
    **http_kwargs,
) -> Dashboard:
    content = http_get_raw(url, **http_kwargs).read()
    soup = BeautifulSoup(gzip.decompress(content), 'lxml')
    date_line = soup.select(date_selector)[0].contents[0]
    m = date_regex.search(date_line)
    if not m:
        raise Exception('Failed to parse date')
    date_str = m.group(date_regex_group)
    return Dashboard(
        timestamp=datetime.datetime.strptime(date_str, '%d.%m.%Y').replace(
            tzinfo=default_tz
        ),
        content=content,
    )


def save_dashboards(dashboards: Iterable[Dashboard], db_path: Path):
    dashboard_store = DashboardStore(db_path)
    for dashboard in dashboards:
        dashboard_store.append(dashboard)


def main(cache_path: Path, config: dict):
    default_tz = dateutil.tz.gettz(config['download_feed']['default_tz'])
    if not default_tz:
        raise Exception('Invalid time zone')
    if 'url' in config['download_dashboard']:
        urls = [config['download_dashboard']['url']]
    else:
        urls = config['download_dashboard']['urls']
    dashboards = (
        download_dashboard(
            url=url,
            date_selector=config['parse_dashboard']['date_selector'],
            date_regex=regex.compile(config['parse_dashboard']['date_regex']),
            date_regex_group=config['parse_dashboard']['date_regex_group'],
            default_tz=default_tz,
            timeout=int(config['http']['timeout']),
            user_agent=config['http']['user_agent'],
        )
        for url in urls
    )
    save_dashboards(dashboards, db_path=cache_path / 'db.sqlite3')
