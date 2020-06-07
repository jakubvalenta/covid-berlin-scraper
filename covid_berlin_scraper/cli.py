import argparse
import json
import logging
import sys
from pathlib import Path

from covid_berlin_scraper import __title__

logger = logging.getLogger(__name__)


def download_feed(cache_path, config, args):
    from covid_berlin_scraper.download_feed import main

    main(cache_path, config)


def download_archives(cache_path, config, args):
    from covid_berlin_scraper.download_archives import main

    main(cache_path, config)


def parse_press_releases(cache_path, config, args):
    from covid_berlin_scraper.parse_press_releases import main

    output_path = Path(args.output)
    main(cache_path, config, output_path)


def main():
    parser = argparse.ArgumentParser(prog=__title__)
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable debugging output'
    )
    parser.add_argument(
        '-a', '--cache', help='Cache directory path', required=True
    )
    parser.add_argument(
        '-c',
        '--config',
        help='Configuration JSON file path',
        default=str(Path(__file__).parents[1] / 'config.sample.json'),
    )
    subparsers = parser.add_subparsers()
    download_feed_parser = subparsers.add_parser(
        'download-feed', help='Download feed'
    )
    download_feed_parser.set_defaults(func=download_feed)
    download_archives_parser = subparsers.add_parser(
        'download-archives', help='Download archives'
    )
    download_archives_parser.set_defaults(func=download_archives)
    parse_press_releases_parser = subparsers.add_parser(
        'parse-press-releases', help='Parse press releases'
    )
    parse_press_releases_parser.add_argument(
        '-o', '--output', help='Output CSV file path', required=True
    )
    parse_press_releases_parser.set_defaults(func=parse_press_releases)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stderr, level=logging.INFO, format='%(message)s'
        )
    cache_path = Path(args.cache)
    with open(args.config, 'r') as f:
        config = json.load(f)
    args.func(cache_path, config, args)


if __name__ == '__main__':
    main()
