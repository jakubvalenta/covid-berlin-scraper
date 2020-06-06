import argparse
import datetime
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlsplit, urlunsplit

import dateutil.tz
import regex
from bs4 import BeautifulSoup

from coronavirus_berlin_scraper.download_feed import (
    filter_press_releases, save_press_releases,
)
from coronavirus_berlin_scraper.model import PressRelease
from coronavirus_berlin_scraper.utils.http_utils import http_get
from coronavirus_berlin_scraper.utils.parse_utils import parse_datetime

logger = logging.getLogger(__name__)


@dataclass
class Archive:
    html: str
    base_url: str


def download_archives(
    urls: Iterable[str], **http_kwargs,
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
    archives: Iterable[Archive], default_tz: datetime.tzinfo,
) -> Iterator[PressRelease]:
    for archive in archives:
        yield from parse_archive(archive, default_tz)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--cache', help='Cache directory path', required=True
    )
    parser.add_argument(
        '-c', '--config', help='Configuration JSON file path', required=True
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable debugging output'
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stderr, level=logging.INFO, format='%(message)s'
        )
    with open(args.config, 'r') as f:
        config = json.load(f)
    archives = download_archives(
        urls=config['download_archives']['urls'],
        cache_dir=Path(args.cache) / 'archive',
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
    )
    press_releases = parse_archives(
        archives,
        default_tz=dateutil.tz.gettz(config['download_feed']['default_tz']),
    )
    filtered_press_releases = filter_press_releases(
        press_releases,
        title_regex=regex.compile(config['download_feed']['title_regex']),
    )
    save_press_releases(
        filtered_press_releases, db_path=Path(args.cache) / 'db.sqlite3'
    )


if __name__ == '__main__':
    main()
