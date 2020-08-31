import logging
from hashlib import sha256
from pathlib import Path
from typing import Optional

import regex
import requests

logger = logging.getLogger(__name__)


def safe_filename(s: str, max_length: int = 64) -> str:
    short_hash = sha256(s.encode()).hexdigest()[:7]
    safe_str = regex.sub(r'[^A-Za-z0-9_\-\.]', '_', s).strip('_')[:max_length]
    return f'{safe_str}--{short_hash}'


def http_get(
    url: str,
    timeout: int,
    user_agent: str,
    cache_dir: Optional[Path] = None,
):
    if cache_dir:
        cache_file_path = cache_dir / safe_filename(url)
        if cache_file_path.is_file():
            logger.info('Reading %s from cache', url)
            return cache_file_path.read_text()
    logger.info('Downloading %s', url)
    r = requests.get(url, headers={'User-Agent': user_agent}, timeout=timeout)
    r.raise_for_status()
    text = r.text
    if cache_dir:
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        cache_file_path.write_text(text)
    return text
