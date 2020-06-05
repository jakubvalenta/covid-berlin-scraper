import argparse
import csv
import datetime
import itertools
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional
from urllib.parse import urlsplit, urlunsplit

import dateutil.tz
import feedparser
import regex
import requests
from bs4 import BeautifulSoup

from coronavirus_berlin_scraper.utils.file_utils import safe_filename
from coronavirus_berlin_scraper.utils.parse_utils import (
    get_element_text, parse_datetime, parse_int, parse_int_or_none,
)

logger = logging.getLogger(__name__)


class ParseError(Exception):
    pass


@dataclass
class PageMeta:
    timestamp: datetime.datetime
    title: str
    url: str

    @property
    def date(self) -> datetime.date:
        date = self.timestamp.date()
        if self.timestamp.hour < 12:
            return date - datetime.timedelta(days=1)
        return date


@dataclass
class PageStats:
    cases: int
    recovered: Optional[int]
    died: Optional[int]


@dataclass
class Page:
    meta: PageMeta
    stats: PageStats


def http_get(
    url: str, timeout: int, user_agent: int, cache_dir: Path,
):
    cache_file_path = cache_dir / safe_filename(url)
    if cache_file_path.is_file():
        logger.info('Reading %s from cache', url)
        return cache_file_path.read_text()
    logger.info('Downloading %s', url)
    r = requests.get(url, headers={'User-Agent': user_agent}, timeout=timeout)
    r.raise_for_status()
    text = r.text
    cache_file_path.parent.mkdir(parents=True, exist_ok=True)
    cache_file_path.write_text(text)
    return text


def parse_feed(text: str, default_tz: datetime.tzinfo) -> Iterator[PageMeta]:
    # Fetch the feed content using requests, because feedparser seems to have
    # some trouble with the Basic Auth -- the feed object contains an error.
    feed = feedparser.parse(text)
    for entry in feed.entries:
        logger.info('Found feed page %s', entry.title)
        yield PageMeta(
            timestamp=parse_datetime(entry.published, default_tz),
            title=entry.title,
            url=entry.link,
        )


def filter_pages(
    pages: Iterable[PageMeta], title_regex: regex.Regex,
) -> Iterator[PageMeta]:
    for meta in pages:
        if title_regex.search(meta.title):
            logger.info('Filtered page %s', meta.title)
            yield meta


def parse_page(
    html: str,
    cases_regex: regex.Regex,
    cases_regex_group: str,
    numbers_map: Dict[str, int],
    died_regex: regex.Regex,
    died_regex_group: str,
    row_index: int,
    expected_first_cell_content: str,
    cases_column_index: int,
    recovered_column_index: int,
    recovered_map: Dict[datetime.date, int],
    thousands_separator: str,
    regex_none: regex.Regex,
    timestamp: datetime.datetime,
) -> PageStats:
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table')
    if table:
        last_tr = table.find_all('tr')[-1]
        tds = last_tr.find_all('td')
        if get_element_text(tds[0]) != expected_first_cell_content:
            raise Exception(
                'Expected the first cell content to be "{}"'.format(
                    expected_first_cell_content
                )
            )
        cases = parse_int(
            get_element_text(tds[cases_column_index]),
            numbers_map,
            thousands_separator,
        )
        if len(tds) > recovered_column_index:
            recovered = parse_int_or_none(
                get_element_text(tds[recovered_column_index]),
                regex_none,
                numbers_map,
                thousands_separator,
            )
        else:
            recovered = recovered_map.get(timestamp.date())
    else:
        cases_m = cases_regex.search(html)
        if cases_m:
            cases = parse_int(
                cases_m.group(cases_regex_group),
                numbers_map,
                thousands_separator,
            )
        else:
            raise ParseError('Failed to parse case number')
        recovered = recovered_map.get(timestamp.date())
    died_m = died_regex.search(html)
    died = died_m and parse_int(
        died_m.group(died_regex_group), numbers_map, thousands_separator
    )
    return PageStats(cases=cases, recovered=recovered, died=died)


def parse_archive(
    html: str, base_url: str, default_tz: datetime.tzinfo
) -> Iterator[PageMeta]:
    soup = BeautifulSoup(html, 'lxml')
    rows = soup.find(class_='modul-autoteaser').find_all(class_='row-fluid')
    for row in rows:
        link = row.find(class_='text').a
        logger.info('Found archive page %s', link.string)
        yield PageMeta(
            timestamp=parse_datetime(
                row.find(class_='date').string, default_tz
            ),
            title=link.string,
            url=base_url + link['href'],
        )


def download_and_parse_archive(
    url: str, default_tz: datetime.tzinfo, **http_kwargs
) -> Iterator[PageMeta]:
    html = http_get(url, **http_kwargs)
    u = urlsplit(url)
    base_url = urlunsplit((u.scheme, u.netloc, '', '', ''))
    return parse_archive(html, base_url, default_tz)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config', help='Configuration file path', required=True
    )
    parser.add_argument(
        '-a', '--cache', help='Cache directory path', required=True
    )
    parser.add_argument(
        '-o', '--output', help='Output CSV file path', required=True
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
    cache_dir = Path(args.cache)
    http_get_kwargs = {
        'timeout': int(config['http']['timeout']),
        'user_agent': config['http']['user_agent'],
        'cache_dir': cache_dir,
    }
    default_tz = dateutil.tz.gettz(config['parse_feed']['default_tz'])

    feed_text = http_get(config['download_feed']['url'], **http_get_kwargs)
    feed_pages = parse_feed(feed_text, default_tz=default_tz)
    archived_pages = itertools.chain.from_iterable(
        download_and_parse_archive(
            archive_url, default_tz=default_tz, **http_get_kwargs,
        )
        for archive_url in config['download_archive']['urls']
    )
    pages = itertools.chain(feed_pages, archived_pages)
    pages_filtered = filter_pages(
        pages,
        title_regex=regex.compile(
            config['filter_feed_entries']['title_regex']
        ),
    )
    parse_page_kwargs = {
        'cases_regex': regex.compile(config['parse_page']['cases_regex']),
        'cases_regex_group': config['parse_page']['cases_regex_group'],
        'numbers_map': {
            s: int(v) for s, v in config['parse_page']['numbers_map'].items()
        },
        'died_regex': regex.compile(config['parse_page']['died_regex']),
        'died_regex_group': config['parse_page']['died_regex_group'],
        'row_index': int(config['parse_page']['row_index']),
        'expected_first_cell_content': config['parse_page'][
            'expected_first_cell_content'
        ],
        'cases_column_index': int(config['parse_page']['cases_column_index']),
        'recovered_column_index': int(
            config['parse_page']['recovered_column_index']
        ),
        'recovered_map': {
            datetime.date.fromisoformat(s): int(v)
            for s, v in config['parse_page']['recovered_map'].items()
        },
        'thousands_separator': config['parse_page']['thousands_separator'],
        'regex_none': regex.compile(config['parse_page']['regex_none']),
    }
    pages = []
    for meta in pages_filtered:
        page_html = http_get(meta.url, **http_get_kwargs)
        try:
            stats = parse_page(
                page_html, timestamp=meta.timestamp, **parse_page_kwargs
            )
        except ParseError:
            logger.error('Failed to parse %s', meta.title)
            continue
        logger.info(
            '%s,%d,%s,%s',
            meta.timestamp.isoformat(),
            stats.cases,
            stats.recovered,
            stats.died,
        )
        pages.append(Page(meta=meta, stats=stats))
    pages_by_date_unique = {}
    for page in sorted(pages, key=lambda page: page.meta.timestamp):
        pages_by_date_unique[page.meta.date] = page
    with open(args.output, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(('date', 'cases', 'recovered', 'died'))
        writer.writerows(
            (
                page.meta.date.isoformat(),
                page.stats.cases,
                page.stats.recovered
                if page.stats.recovered is not None
                else '',
                page.stats.died if page.stats.died is not None else '',
            )
            for page in pages_by_date_unique.values()
        )


if __name__ == '__main__':
    main()
