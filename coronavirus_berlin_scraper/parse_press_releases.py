import argparse
import csv
import datetime
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

import regex
from bs4 import BeautifulSoup

from coronavirus_berlin_scraper.model import PressRelease, PressReleasesStore
from coronavirus_berlin_scraper.utils.http_utils import http_get
from coronavirus_berlin_scraper.utils.parse_utils import (
    get_element_text, parse_int, parse_int_or_none,
)

logger = logging.getLogger(__name__)


class ParseError(Exception):
    pass


@dataclass
class PressReleaseContent:
    press_release: PressRelease
    html: str


@dataclass
class PressReleaseStats:
    press_release: PressRelease
    cases: int
    recovered: Optional[int]
    died: Optional[int]

    @property
    def date(self) -> datetime.date:
        date = self.press_release.timestamp.date()
        if self.press_release.timestamp.hour < 12:
            return date - datetime.timedelta(days=1)
        return date


def download_press_releases(
    db_path: Path, **http_get_kwargs
) -> Iterator[PressReleaseContent]:
    press_releases = PressReleasesStore(db_path)
    for press_release in press_releases:
        html = http_get(press_release.url, **http_get_kwargs)
        yield PressReleaseContent(press_release=press_release, html=html)


def parse_press_release(
    content: PressReleaseContent,
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
) -> PressReleaseStats:
    soup = BeautifulSoup(content.html, 'lxml')
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
            recovered = recovered_map.get(
                content.press_release.timestamp.date()
            )
    else:
        cases_m = cases_regex.search(content.html)
        if cases_m:
            cases = parse_int(
                cases_m.group(cases_regex_group),
                numbers_map,
                thousands_separator,
            )
        else:
            raise ParseError('Failed to parse case number')
        recovered = recovered_map.get(content.press_release.timestamp.date())
    died_m = died_regex.search(content.html)
    died = died_m and parse_int(
        died_m.group(died_regex_group), numbers_map, thousands_separator
    )
    return PressReleaseStats(
        press_release=content.press_release,
        cases=cases,
        recovered=recovered,
        died=died,
    )


def parse_press_releases(
    contents: Iterable[PressReleaseContent], **parse_press_release_kwargs
) -> Iterator[PressReleaseStats]:
    for content in contents:
        try:
            stats = parse_press_release(content, **parse_press_release_kwargs)
        except ParseError:
            logger.error(
                'Failed to parse %s', content.press_release.title,
            )
            continue
        logger.info(
            '%s,%d,%s,%s',
            content.press_release.timestamp.isoformat(),
            stats.cases,
            stats.recovered,
            stats.died,
        )
        yield stats


def write_csv(stats_list: Iterable[PressReleaseStats], path: Path):
    stats_by_date_unique = {}
    for stats in stats_list:
        stats_by_date_unique[stats.press_release.date] = stats
    with path.open('w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(('date', 'cases', 'recovered', 'died'))
        writer.writerows(
            (
                stats.press_release.date.isoformat(),
                stats.cases,
                stats.recovered if stats.recovered is not None else '',
                stats.died if stats.died is not None else '',
            )
            for stats in stats_by_date_unique.values()
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--cache', help='Cache directory path', required=True
    )
    parser.add_argument(
        '-c', '--config', help='Configuration JSON file path', required=True
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
    contents = download_press_releases(
        db_path=Path(args.cache) / 'db.sqlite3',
        cache_dir=Path(args.cache) / 'pages',
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
    )
    stats_list = parse_press_releases(
        contents,
        cases_regex=regex.compile(
            config['parse_press_release']['cases_regex']
        ),
        cases_regex_group=config['parse_press_release']['cases_regex_group'],
        numbers_map={
            s: int(v)
            for s, v in config['parse_press_release']['numbers_map'].items()
        },
        died_regex=regex.compile(config['parse_press_release']['died_regex']),
        died_regex_group=config['parse_press_release']['died_regex_group'],
        row_index=int(config['parse_press_release']['row_index']),
        expected_first_cell_content=config['parse_press_release'][
            'expected_first_cell_content'
        ],
        cases_column_index=int(
            config['parse_press_release']['cases_column_index']
        ),
        recovered_column_index=int(
            config['parse_press_release']['recovered_column_index']
        ),
        recovered_map={
            datetime.date.fromisoformat(s): int(v)
            for s, v in config['parse_press_release']['recovered_map'].items()
        },
        thousands_separator=config['parse_press_release'][
            'thousands_separator'
        ],
        regex_none=regex.compile(config['parse_press_release']['regex_none']),
    )
    write_csv(stats_list, Path(args.output))


if __name__ == '__main__':
    main()
