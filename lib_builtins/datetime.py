"""
datetime library for Vyn.

import datetime

Named "datetime" to match Python convention, loaded via a distinct
importlib module name ("lib.datetime") internally so it doesn't collide
with Python's own datetime module, which this library wraps.
"""

import datetime as _dt


def now():
    """ISO 8601 timestamp string, e.g. '2026-07-17T14:30:00.123456'."""
    return _dt.datetime.now().isoformat()


def today():
    """ISO date string, e.g. '2026-07-17'."""
    return _dt.date.today().isoformat()


def timestamp():
    """Unix timestamp (seconds since epoch) as a float."""
    return _dt.datetime.now().timestamp()


def _parse(value):
    """Accepts an ISO string or a unix timestamp number."""
    if isinstance(value, str):
        return _dt.datetime.fromisoformat(value)
    return _dt.datetime.fromtimestamp(value)


def parse_date(s, fmt):
    """Parses a string using an explicit strptime-style format, e.g.
    parse_date("17/07/2026", "%d/%m/%Y")."""
    return _dt.datetime.strptime(s, fmt).isoformat()


def format_date(value, fmt):
    """format_date(now(), "%Y-%m-%d %H:%M:%S")."""
    return _parse(value).strftime(fmt)


def date_diff(a, b):
    """Difference in whole days between two dates (a - b)."""
    return (_parse(a) - _parse(b)).days


def seconds_diff(a, b):
    return (_parse(a) - _parse(b)).total_seconds()


def add_days(value, n):
    return (_parse(value) + _dt.timedelta(days=int(n))).isoformat()


def add_seconds(value, n):
    return (_parse(value) + _dt.timedelta(seconds=int(n))).isoformat()


def weekday(value):
    """0 = Monday ... 6 = Sunday, matching Python's date.weekday()."""
    return _parse(value).weekday()


def weekday_name(value):
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[_parse(value).weekday()]


def year(value):
    return _parse(value).year


def month(value):
    return _parse(value).month


def day(value):
    return _parse(value).day


def is_leap_year(y):
    y = int(y)
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)