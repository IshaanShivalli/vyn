import math as _math

pi = _math.pi
e = _math.e

def sqrt(x): return _math.sqrt(float(x))
def sin(x): return _math.sin(float(x))
def cos(x): return _math.cos(float(x))
def tan(x): return _math.tan(float(x))
def log(x, base=None): return _math.log(float(x)) if base is None else _math.log(float(x), float(base))
def floor(x): return _math.floor(float(x))
def ceil(x): return _math.ceil(float(x))
def pow(x, y): return _math.pow(float(x), float(y))
def factorial(x): return _math.factorial(int(float(x)))
def gcd(a, b): return _math.gcd(int(float(a)), int(float(b)))