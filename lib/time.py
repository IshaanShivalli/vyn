"""
time.vyn implementation as real Python library.
"""
import time as _time
import datetime as _dt


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
    if isinstance(t, str):
        dt = _dt.datetime.fromisoformat(t)
    else:
        dt = t
    return (dt + _dt.timedelta(hours=int(hours))).isoformat()


def addMinutes(t, minutes):
    if isinstance(t, str):
        dt = _dt.datetime.fromisoformat(t)
    else:
        dt = t
    return (dt + _dt.timedelta(minutes=int(minutes))).isoformat()


def addSeconds(t, seconds):
    if isinstance(t, str):
        dt = _dt.datetime.fromisoformat(t)
    else:
        dt = t
    return (dt + _dt.timedelta(seconds=int(seconds))).isoformat()


def differenceInSeconds(time1, time2):
    if isinstance(time1, str):
        t1 = _dt.datetime.fromisoformat(time1)
    else:
        t1 = time1
    if isinstance(time2, str):
        t2 = _dt.datetime.fromisoformat(time2)
    else:
        t2 = time2
    return int((t2 - t1).total_seconds())


def differenceInMinutes(time1, time2):
    if isinstance(time1, str):
        t1 = _dt.datetime.fromisoformat(time1)
    else:
        t1 = time1
    if isinstance(time2, str):
        t2 = _dt.datetime.fromisoformat(time2)
    else:
        t2 = time2
    return int((t2 - t1).total_seconds() / 60)


def differenceInHours(time1, time2):
    if isinstance(time1, str):
        t1 = _dt.datetime.fromisoformat(time1)
    else:
        t1 = time1
    if isinstance(time2, str):
        t2 = _dt.datetime.fromisoformat(time2)
    else:
        t2 = time2
    return int((t2 - t1).total_seconds() / 3600)


def isLeapSecond(second):
    return int(second) == 60


def getTimestamp():
    return int(_time.time())


def toISOString():
    return _dt.datetime.now().isoformat()
