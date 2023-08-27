import datetime
from typing import Dict, Optional

import dateparser
import regex


def get_element_text(el) -> str:
    return ''.join(el.strings).strip()


def parse_int(
    s: str, numbers_map: Dict[str, int], thousands_separator: str
) -> int:
    m = regex.search(r'\d+', s.strip().replace(thousands_separator, ''))
    if not m:
        s_clean = s.lower()
        for substr, value in numbers_map.items():
            if substr == s_clean:
                return value
        raise Exception(f'Failed to parse number "{s}"')
    return int(m[0])


def parse_int_or_none(
    s: str, regex_none: regex.Pattern, *args, **kwargs
) -> Optional[int]:
    if regex_none.search(s):
        return None
    return parse_int(s, *args, **kwargs)


def parse_datetime(s: str, default_tz: datetime.tzinfo) -> datetime.datetime:
    dt = dateparser.parse(s)
    if not dt:
        raise Exception(f'Failed to parse datetime "{s}"')
    if not dt.tzinfo:
        return dt.replace(tzinfo=default_tz)
    return dt
