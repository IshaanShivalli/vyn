"""
strings library for Vyn.

import strings

Named "strings" (not "string") to avoid colliding with any existing
string-type keyword/name elsewhere in the interpreter.
"""


def upper(s):
    return str(s).upper()


def lower(s):
    return str(s).lower()


def trim(s):
    return str(s).strip()


def trim_start(s):
    return str(s).lstrip()


def trim_end(s):
    return str(s).rstrip()


def replace(s, old, new):
    return str(s).replace(old, new)


def split(s, sep=" "):
    return str(s).split(sep)


def join(sep, items):
    return sep.join(str(x) for x in items)


def concat(*parts):
    return "".join(str(p) for p in parts)


def contains(s, sub):
    return str(sub) in str(s)


def starts_with(s, prefix):
    return str(s).startswith(prefix)


def ends_with(s, suffix):
    return str(s).endswith(suffix)


def index_of(s, sub):
    """-1 if not found, matching common string-library convention."""
    return str(s).find(sub)


def repeat(s, n):
    return str(s) * int(n)


def reverse(s):
    return str(s)[::-1]


def pad_left(s, width, fill=" "):
    return str(s).rjust(int(width), fill)


def pad_right(s, width, fill=" "):
    return str(s).ljust(int(width), fill)


def capitalize(s):
    return str(s).capitalize()


def title_case(s):
    return str(s).title()


def char_at(s, i):
    return str(s)[int(i)]


def substring(s, start, end=None):
    return str(s)[int(start):int(end) if end is not None else None]


def is_numeric(s):
    return str(s).replace(".", "", 1).replace("-", "", 1).isdigit()


def is_alpha(s):
    return str(s).isalpha()


def is_empty(s):
    return len(str(s)) == 0