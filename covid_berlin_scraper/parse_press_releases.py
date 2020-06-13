import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, Optional

import regex
from bs4 import BeautifulSoup

from covid_berlin_scraper.model import PressRelease, PressReleasesStore
from covid_berlin_scraper.utils.http_utils import http_get
from covid_berlin_scraper.utils.parse_utils import (
    get_element_text, parse_int, parse_int_or_none,
)

logger = logging.getLogger(__name__)


def ensure_str(v: Any) -> str:
    if v is None:
        return ''
    return str(v)


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
    deaths: Optional[int]
    hospitalized: Optional[int]
    icu: Optional[int]

    @property
    def date(self) -> datetime.date:
        date = self.press_release.timestamp.date()
        if self.press_release.timestamp.hour < 12:
            return date - datetime.timedelta(days=1)
        return date

    def astuple(
        self, field_funcs: Iterable[Callable[['PressReleaseStats'], str]]
    ) -> tuple:
        return tuple(func(self) for func in field_funcs)

    def __repr__(self) -> str:
        return ','.join(
            [
                self.press_release.timestamp.isoformat(),
                ensure_str(self.cases),
                ensure_str(self.recovered),
                ensure_str(self.deaths),
                ensure_str(self.hospitalized),
                ensure_str(self.icu),
            ]
        )


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
    deaths_regex: regex.Regex,
    deaths_regex_group: str,
    hospitalized_regex: regex.Regex,
    hospitalized_regex_group: str,
    icu_regex: regex.Regex,
    icu_regex_group: str,
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
    deaths_m = deaths_regex.search(content.html)
    deaths = deaths_m and parse_int(
        deaths_m.group(deaths_regex_group), numbers_map, thousands_separator
    )
    hospitalized_m = hospitalized_regex.search(content.html)
    hospitalized = hospitalized_m and parse_int(
        hospitalized_m.group(hospitalized_regex_group),
        numbers_map,
        thousands_separator,
    )
    icu_m = icu_regex.search(content.html)
    icu = icu_m and parse_int(
        icu_m.group(icu_regex_group), numbers_map, thousands_separator
    )
    return PressReleaseStats(
        press_release=content.press_release,
        cases=cases,
        recovered=recovered,
        deaths=deaths,
        hospitalized=hospitalized,
        icu=icu,
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
        logger.info(stats)
        yield stats


def write_csv(
    stats_list: Iterable[PressReleaseStats],
    path: Path,
    fields: Dict[str, Callable[[PressReleaseStats], Any]],
):
    stats_by_date_unique = {}
    for stats in stats_list:
        stats_by_date_unique[stats.press_release.date] = stats
    with path.open('w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(fields.keys())
        writer.writerows(
            stats.astuple(fields.values())
            for stats in stats_by_date_unique.values()
        )


def main(
    cache_path: Path,
    config: dict,
    output_path: Path,
    output_hosp_path: Optional[Path] = None,
):
    contents = download_press_releases(
        db_path=cache_path / 'db.sqlite3',
        cache_dir=cache_path / 'pages',
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
    )
    stats_list = list(
        parse_press_releases(
            contents,
            cases_regex=regex.compile(
                config['parse_press_release']['cases_regex']
            ),
            cases_regex_group=config['parse_press_release'][
                'cases_regex_group'
            ],
            numbers_map={
                s: int(v)
                for s, v in config['parse_press_release'][
                    'numbers_map'
                ].items()
            },
            deaths_regex=regex.compile(
                config['parse_press_release']['deaths_regex']
            ),
            deaths_regex_group=config['parse_press_release'][
                'deaths_regex_group'
            ],
            hospitalized_regex=regex.compile(
                config['parse_press_release']['hospitalized_regex']
            ),
            hospitalized_regex_group=config['parse_press_release'][
                'hospitalized_regex_group'
            ],
            icu_regex=regex.compile(
                config['parse_press_release']['icu_regex']
            ),
            icu_regex_group=config['parse_press_release']['icu_regex_group'],
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
                for s, v in config['parse_press_release'][
                    'recovered_map'
                ].items()
            },
            thousands_separator=config['parse_press_release'][
                'thousands_separator'
            ],
            regex_none=regex.compile(
                config['parse_press_release']['regex_none']
            ),
        )
    )
    write_csv(
        stats_list,
        output_path,
        {
            'date': lambda stats: stats.date.isoformat(),
            'cases': lambda stats: stats.cases,
            'recovered': lambda stats: ensure_str(stats.recovered),
            'deaths': lambda stats: ensure_str(stats.deaths),
        },
    )
    if output_hosp_path:
        write_csv(
            stats_list,
            output_hosp_path,
            {
                'date': lambda stats: stats.date.isoformat(),
                'cases': lambda stats: stats.cases,
                'recovered': lambda stats: ensure_str(stats.recovered),
                'deaths': lambda stats: ensure_str(stats.deaths),
                'hospitalized': lambda stats: ensure_str(stats.hospitalized),
                'icu': lambda stats: ensure_str(stats.icu),
            },
        )
