import re

FUNCTION_HEADER_RE = re.compile(
    r'^function\s*(?P<fname>[A-Za-z_]\w*)?\s*\(\s*(?P<params>.*?)\s*\)\s*perform\s*$',
    re.IGNORECASE,
)
CALL_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*\(\s*(?P<args>.*)\s*\)\s*$')


def parse_function_header(line):
    m = FUNCTION_HEADER_RE.match(line.strip())
    if not m:
        return None
    fname = m.group('fname')
    params = [p.strip() for p in m.group('params').split(',') if p.strip()]
    return fname, params


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
# myFunc = function(a, b) perform
#   result = a * b
#   return result
# endFunc
#
# FUNCTION CALL SYNTAX:
# add(3, 5)
# myFunc(2, 4)
