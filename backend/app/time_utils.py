"""Beijing time (UTC+8) helpers."""
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    return datetime.now(CST)


def beijing_now_naive() -> datetime:
    return beijing_now().replace(tzinfo=None)


def to_beijing_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(CST).replace(tzinfo=None)


def beijing_today():
    return beijing_now().date()
