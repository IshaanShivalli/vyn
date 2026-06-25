"""
re.vyn implementation as real Python library.
"""
import re as _re


def length(s):
    return len(str(s))

def toUpperCase(s):
    return str(s).upper()

def toLowerCase(s):
    return str(s).lower()

def trim(s):
    return str(s).strip()

def substring(s, start, end=None):
    if end is None:
        return str(s)[int(start):]
    return str(s)[int(start):int(end)]

def indexOf(s, search, start=0):
    return str(s).find(str(search), int(start))

def lastIndexOf(s, search, start=None):
    if start is None:
        return str(s).rfind(str(search))
    return str(s).rfind(str(search), 0, int(start) + 1)

def replace(s, find, replaceWith):
    return str(s).replace(str(find), str(replaceWith))

def split(s, delimiter=None):
    if delimiter is None:
        return [str(s)]
    return str(s).split(str(delimiter))

def join(*args):
    return " ".join(str(a) for a in args)

def startsWith(s, prefix):
    return str(s).startswith(str(prefix))

def endsWith(s, suffix):
    return str(s).endswith(str(suffix))

def contains(s, substring):
    return str(substring) in str(s)

def reverse(s):
    return str(s)[::-1]

def repeat(s, count):
    return str(s) * int(count)

def concat(*args):
    return "".join(str(a) for a in args)

def format(s, *args):
    return str(s).format(*args)

def padStart(s, length, char=""):
    c = str(char)[0] if char else " "
    return str(s).rjust(int(length), c)

def padEnd(s, length, char=""):
    c = str(char)[0] if char else " "
    return str(s).ljust(int(length), c)

def charCodeAt(s, index):
    s = str(s)
    i = int(index)
    return ord(s[i]) if 0 <= i < len(s) else -1

def charAt(s, index):
    s = str(s)
    i = int(index)
    return s[i] if 0 <= i < len(s) else ""