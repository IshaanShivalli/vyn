import datetime as _dt
import time as _time


def _add_or_sub_days(d, n, add=True):
    """Internal: accept iso str or datetime obj, return new datetime obj."""
    if isinstance(d, str):
        try:
            dt = _dt.datetime.fromisoformat(d)
        except ValueError:
            dt = _dt.datetime.fromisoformat(d + "T00:00:00")
    elif hasattr(d, "year"):
        dt = d
    else:
        dt = _dt.datetime.now()
    delta = _dt.timedelta(days=int(n))
    return (dt + delta) if add else (dt - delta)


# --- Flat API matching datetime.vyn ---
def now():
    return _dt.datetime.now()


def getYear():
    return _dt.datetime.now().year


def getMonth():
    return _dt.datetime.now().month


def getDay():
    return _dt.datetime.now().day


def formatDate(year, month, day):
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def parseDate(dateStr):
    if isinstance(dateStr, str):
        try:
            return _dt.datetime.fromisoformat(dateStr)
        except ValueError:
            return dateStr
    return dateStr


def getCurrentTime():
    return _dt.datetime.now().time()


def addDays(d, n):
    return _add_or_sub_days(d, n, add=True)


def subtractDays(d, n):
    return _add_or_sub_days(d, n, add=False)


def getTimestamp():
    return int(_time.time() * 1000)


def toISOString(dt):
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)


# Expose the real datetime module for dotted access and full objects/methods
datetime = _dt
