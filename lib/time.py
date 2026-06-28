"""
time.vyn implementation as real Python library.
Includes timed block support (start_timer, stop_timer, store_result etc.)
"""
import time as _time
import datetime as _dt

# ---------------------------------------------------------------------------
# Existing time functions
# ---------------------------------------------------------------------------

def currentTimeMillis():
    return int(_time.time() * 1000)


def currentTimeSeconds():
    return int(_time.time())


def sleep(milliseconds):
    _time.sleep(float(milliseconds) / 1000.0)
    return "slept"


def sleepSeconds(seconds):
    _time.sleep(float(seconds))
    return "slept"


def getHour():
    return _dt.datetime.now().hour


def getMinute():
    return _dt.datetime.now().minute


def getSecond():
    return _dt.datetime.now().second


def getMillisecond():
    return _dt.datetime.now().microsecond // 1000


def formatTime(hour, minute, second):
    return f"{int(hour):02d}:{int(minute):02d}:{int(second):02d}"


def parseTime(timeStr):
    return timeStr


def getTimezone():
    return str(_time.tzname)


def setTimezone(tz):
    return tz


def addHours(t, hours):
    dt = _dt.datetime.fromisoformat(t) if isinstance(t, str) else t
    return (dt + _dt.timedelta(hours=int(hours))).isoformat()


def addMinutes(t, minutes):
    dt = _dt.datetime.fromisoformat(t) if isinstance(t, str) else t
    return (dt + _dt.timedelta(minutes=int(minutes))).isoformat()


def addSeconds(t, seconds):
    dt = _dt.datetime.fromisoformat(t) if isinstance(t, str) else t
    return (dt + _dt.timedelta(seconds=int(seconds))).isoformat()


def differenceInSeconds(time1, time2):
    t1 = _dt.datetime.fromisoformat(time1) if isinstance(time1, str) else time1
    t2 = _dt.datetime.fromisoformat(time2) if isinstance(time2, str) else time2
    return int((t2 - t1).total_seconds())


def differenceInMinutes(time1, time2):
    t1 = _dt.datetime.fromisoformat(time1) if isinstance(time1, str) else time1
    t2 = _dt.datetime.fromisoformat(time2) if isinstance(time2, str) else time2
    return int((t2 - t1).total_seconds() / 60)


def differenceInHours(time1, time2):
    t1 = _dt.datetime.fromisoformat(time1) if isinstance(time1, str) else time1
    t2 = _dt.datetime.fromisoformat(time2) if isinstance(time2, str) else time2
    return int((t2 - t1).total_seconds() / 3600)


def isLeapSecond(second):
    return int(second) == 60


def getTimestamp():
    return int(_time.time())


def toISOString():
    return _dt.datetime.now().isoformat()


# ---------------------------------------------------------------------------
# Timed block support (used by timed do...endTimed in the interpreter)
# ---------------------------------------------------------------------------

_timed_results = {}


def start_timer():
    """Returns current time in nanoseconds."""
    return _time.perf_counter_ns()


def stop_timer(start_ns):
    """
    Returns elapsed time as a readable string.
    Automatically picks the best unit.
    """
    elapsed_ns = _time.perf_counter_ns() - start_ns
    if elapsed_ns < 1_000:
        return f"{elapsed_ns}ns"
    elif elapsed_ns < 1_000_000:
        return f"{elapsed_ns / 1_000:.3f}µs"
    elif elapsed_ns < 1_000_000_000:
        return f"{elapsed_ns / 1_000_000:.3f}ms"
    else:
        return f"{elapsed_ns / 1_000_000_000:.3f}s"


def store_result(label, elapsed_str):
    """Store a timed result under a label."""
    _timed_results[label] = elapsed_str


def get_result(label):
    """Get a stored timed result by label."""
    return _timed_results.get(label, None)


def list_results():
    """Return all stored timed results."""
    return dict(_timed_results)


def clear_results():
    """Clear all stored timed results."""
    _timed_results.clear()