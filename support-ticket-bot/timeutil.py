"""Timezone-aware timestamp helpers shared by the store and KPI modules."""

from datetime import datetime

import pytz

import config

TS_FORMAT = "%Y-%m-%d %H:%M:%S"


def tz():
    return pytz.timezone(config.TIMEZONE)


def now_iso():
    return datetime.now(tz()).strftime(TS_FORMAT)


def parse_ts(value):
    """Parse a sheet timestamp back into an aware datetime, or None."""
    if not value:
        return None
    try:
        return tz().localize(datetime.strptime(value, TS_FORMAT))
    except ValueError:
        return None
