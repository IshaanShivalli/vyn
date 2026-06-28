import re

TYPE_CONVERTERS = {
    "int": int,
    "float": float,
    "lint": int,
    "sint": int,
    # FIX: added "str" key to match documented syntax IN(str "...")
    "str": str,
    "string": str,
}

# FIX: regex updated to match documented syntax: IN(int "prompt")
# Previously matched IN(int("prompt")) — double parens, which was wrong
INPUT_RE = re.compile(
    r'^IN\s*\(\s*(?P<datatype>\w+)\s+(?P<quote>["\'])(?P<prompt>.*?)(?P=quote)\s*\)\s*$'
)
ASSIGNMENT_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$')

variables = {}
variables['not_in'] = lambda item, container: item not in container
variables['in_list'] = lambda item, container: item in container
variables['range'] = lambda *args: list(range(*[int(a) for a in args]))
variables['len'] = lambda x: len(x)
constants = set()
reactive = {}
dependencies = {}
watchers = {}


# GLOBAL VARIABLES MODULE: Stores and manages global variable state
# x = 10                       - integer assignment
# name = "John"                - string assignment
# result = x + 5               - expression evaluation
# value = IN(int "Enter: ")    - input assignment