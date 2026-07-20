"""
math library for Vyn.

import math

Then either bare names (sqrt(16)) or dotted access (math.sqrt(16)) both
work, since library.register_library() drops every public name here
straight into the flat `variables` namespace AND keeps the module itself
registered as `math` / `Math`.

None of Python's abs/round/min/max/sum/pow are pre-registered in Vyn
(only range/len/not_in/in_list are, per global.py) -- so this library
supplies them explicitly rather than assuming they're already available.
"""

import math as _math

pi = _math.pi
e = _math.e
inf = _math.inf
nan = _math.nan


def sqrt(x):
    return _math.sqrt(x)


def cbrt(x):
    return _math.copysign(abs(x) ** (1 / 3), x)


def pow(x, y):
    return _math.pow(x, y)


def abs(x):
    return x if x >= 0 else -x


def round(x, n=0):
    return _math.floor(x * (10 ** n) + 0.5) / (10 ** n) if n else float(_math.floor(x + 0.5))


def floor(x):
    return _math.floor(x)


def ceil(x):
    return _math.ceil(x)


def trunc(x):
    return _math.trunc(x)


def min(*args):
    values = args[0] if len(args) == 1 and hasattr(args[0], '__iter__') else args
    best = None
    for v in values:
        if best is None or v < best:
            best = v
    return best


def max(*args):
    values = args[0] if len(args) == 1 and hasattr(args[0], '__iter__') else args
    best = None
    for v in values:
        if best is None or v > best:
            best = v
    return best


def sum(items):
    total = 0
    for v in items:
        total += v
    return total


def avg(items):
    items = list(items)
    if not items:
        return 0
    return sum(items) / len(items)


def gcd(a, b):
    return _math.gcd(int(a), int(b))


def lcm(a, b):
    a, b = int(a), int(b)
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // _math.gcd(a, b)


def factorial(n):
    return _math.factorial(int(n))


def log(x, base=_math.e):
    return _math.log(x, base)


def log2(x):
    return _math.log2(x)


def log10(x):
    return _math.log10(x)


def exp(x):
    return _math.exp(x)


def sin(x):
    return _math.sin(x)


def cos(x):
    return _math.cos(x)


def tan(x):
    return _math.tan(x)


def degrees(x):
    return _math.degrees(x)


def radians(x):
    return _math.radians(x)


def is_prime(n):
    n = int(n)
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x