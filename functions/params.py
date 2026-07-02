import re

try:
    from golan.syntax import parse_function_header as _golan_parse_function_header
except ImportError:
    _golan_parse_function_header = None

FUNCTION_HEADER_RE = re.compile(
    r'^function\s*(?P<fname>[A-Za-z_]\w*)?\s*\(\s*(?P<params>.*?)\s*\)\s*(?:returns\s*\(\s*(?P<returns>.*?)\s*\)\s*)?perform\s*$',
    re.IGNORECASE,
)
CALL_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*\(\s*(?P<args>.*)\s*\)\s*$')


def _parse_param(p):
    """Parse a single param string into (name, default_or_None)."""
    p = p.strip()
    if '=' in p:
        name, default = p.split('=', 1)
        return name.strip(), default.strip()
    return p, None


def parse_function_header(line):
    m = FUNCTION_HEADER_RE.match(line.strip())
    if not m:
        return None
    fname = m.group('fname')
    raw = m.group('params')
    returns_raw = m.group('returns')
    # FIX: return list of (name, default) tuples so make_fn can handle defaults
    params = [_parse_param(p) for p in raw.split(',') if p.strip()]
    returns = None
    if returns_raw:
        returns = [r.strip() for r in returns_raw.split(',') if r.strip()]
        if not returns:
            returns = None
    return fname, params, returns


def parse_function_call(line):
    m = CALL_RE.match(line.strip())
    if not m:
        return None
    return m.group('name'), m.group('args')

# FUNCTION DEFINITION SYNTAX:
# function add(x, y) perform
#   return x + y
# endFunc
#
# With defaults:
# function greet(name, greeting = "Hello") perform
#   print(greeting + " " + name)
# endFunc
#
# FUNCTION CALL SYNTAX:
# add(3, 5)
# greet("Ishaan")
# greet("Ishaan", "Hi")