"""Beijing time (UTC+8) helpers."""
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    return datetime.now(CST)


def beijing_today():
    return beijing_now().date()
