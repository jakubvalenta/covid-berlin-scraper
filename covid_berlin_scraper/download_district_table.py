import logging
from pathlib import Path

import dateparser
import requests

from covid_berlin_scraper.model import DistrictTable, DistrictTableStore

logger = logging.getLogger(__name__)


def download_district_table(
    url: str, timeout: int, user_agent: str
) -> DistrictTable:
    logger.info('Downloading %s', url)
    r = requests.get(url, headers={'User-Agent': user_agent}, timeout=timeout)
    r.raise_for_status()
    timestamp = dateparser.parse(r.headers['Last-Modified'])
    if not timestamp.tzinfo:
        raise Exception('Missing time zone')
    content = r.text
    if not content:
        raise Exception('Missing content')
    return DistrictTable(
        timestamp=timestamp,
        content=content,
    )


def save_district_table(district_table: DistrictTable, db_path: Path):
    district_table_store = DistrictTableStore(db_path)
    district_table_store.append(district_table)


def main(cache_path: Path, config: dict):
    district_table = download_district_table(
        url=config['download_district_table']['url'],
        timeout=int(config['http']['timeout']),
        user_agent=config['http']['user_agent'],
    )
    save_district_table(district_table, db_path=cache_path / 'db.sqlite3')
