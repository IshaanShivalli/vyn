"""
re.vyn implementation as real Python library.
"""
import re as _re


def match(pattern, text):
    return bool(_re.match(pattern, text))


def search(pattern, text):
    return bool(_re.search(pattern, text))


def findAll(pattern, text):
    return _re.findall(pattern, text)


def replace(pattern, replacement, text):
    return _re.sub(pattern, replacement, text)


def split(pattern, text):
    return _re.split(pattern, text)


def compile(pattern):
    return _re.compile(pattern)


def escape(text):
    return _re.escape(text)


def isMatch(pattern, text):
    return bool(_re.match(pattern, text))


def getGroups(pattern, text):
    m = _re.match(pattern, text)
    return m.groups() if m else ()


def substitute(pattern, replacement, text):
    return _re.sub(pattern, replacement, text)
