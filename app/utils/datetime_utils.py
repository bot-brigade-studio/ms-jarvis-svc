from datetime import datetime, timezone
from dateutil.parser import parse
from typing import Optional


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(format)


def parse_datetime(date_string: str) -> Optional[datetime]:
    try:
        return parse(date_string)
    except (ValueError, TypeError):
        return None


def get_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_year_month_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y/%m/%d")
