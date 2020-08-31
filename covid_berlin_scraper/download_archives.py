import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlsplit, urlunsplit

import dateutil.tz
import regex
from bs4 import BeautifulSoup

from covid_berlin_scraper.download_feed import (
    filter_press_releases, save_press_releases,
)
from covid_berlin_scraper.model import PressRelease
from covid_berlin_scraper.utils.http_utils import http_get
from covid_berlin_scraper.utils.parse_utils import parse_datetime

logger = logging.getLogger(__name__)


@dataclass
class Archive:
    html: str
    base_url: str


def download_archives(
    urls: Iterable[str],
    **http_kwargs,
) -> Iterator[Archive]:
    for url in urls:
        html = http_get(url, **http_kwargs)
        u = urlsplit(url)
        base_url = urlunsplit((u.scheme, u.netloc, '', '', ''))
        yield Archive(html=html, base_url=base_url)


def parse_archive(
    archive: Archive, default_tz: datetime.tzinfo
) -> Iterator[PressRelease]:
    soup = BeautifulSoup(archive.html, 'lxml')
    rows = soup.find(class_='modul-autoteaser').find_all(class_='row-fluid')
    for row in rows:
        link = row.find(class_='text').a
        logger.info('Found archive press_release %s', link.string)
        yield PressRelease(
            timestamp=parse_datetime(
                row.find(class_='date').string, default_tz
            ),
            title=link.string,
            url=archive.base_url + link['href'],
        )


def parse_archives(
    archives: Iterable[Archive],
    default_tz: datetime.tzinfo,
) -> Iterator[PressRelease]:
    for archive in archives:
        yield from parse_archive(archive, default_tz)


def main(cache_path: Path, config: dict):
    archives = download_archives(
        urls=config['download_archives']['urls'],
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
    )
    default_tz = dateutil.tz.gettz(config['download_feed']['default_tz'])
    if not default_tz:
        raise Exception('Invalid time zone')
    press_releases = parse_archives(
        archives,
        default_tz=default_tz,
    )
    filtered_press_releases = filter_press_releases(
        press_releases,
        title_regex=regex.compile(config['download_feed']['title_regex']),
    )
    save_press_releases(
        filtered_press_releases, db_path=cache_path / 'db.sqlite3'
    )
