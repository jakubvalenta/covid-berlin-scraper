import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Iterable, Iterator

import dateutil.tz
import feedparser
import regex

from coronavirus_berlin_scraper.model import PressRelease, PressReleasesStore
from coronavirus_berlin_scraper.utils.http_utils import http_get
from coronavirus_berlin_scraper.utils.parse_utils import parse_datetime

logger = logging.getLogger(__name__)


def download_feed(
    url: str, default_tz: datetime.tzinfo, **http_kwargs,
) -> Iterator[PressRelease]:
    feed_text = http_get(url, **http_kwargs)
    feed = feedparser.parse(feed_text)
    for entry in feed.entries:
        logger.info('Found press release %s', entry.title)
        yield PressRelease(
            timestamp=parse_datetime(entry.published, default_tz),
            title=entry.title,
            url=entry.link,
        )


def filter_press_releases(
    press_releases: Iterable[PressRelease], title_regex: regex.Regex
) -> Iterator[PressRelease]:
    for press_release in press_releases:
        if press_release.matches_title_regex(title_regex):
            logger.info('Filtered press release %s', press_release.title)
            yield press_release


def save_press_releases(press_releases: Iterable[PressRelease], db_path: Path):
    press_releases_store = PressReleasesStore(db_path)
    for press_release in press_releases:
        press_releases_store.append(press_release)


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
    press_releases = download_feed(
        url=config['download_feed']['url'],
        default_tz=dateutil.tz.gettz(config['download_feed']['default_tz']),
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
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
