import error
from variables import global_vars


def parse_bool(value):
    lowered = value.strip().lower()
    if lowered in {"true", "t", "yes", "y", "1"}:
        return True
    if lowered in {"false", "f", "no", "n", "0"}:
        return False
    error.invalid_bool_value(value)


def parse_in_call(expr):
    match = global_vars.INPUT_RE.match(expr.strip())
    if not match:
        error.invalid_in_syntax()

    datatype = match.group("datatype").lower()
    prompt = match.group("prompt")
    raw_value = input(prompt)
    if datatype == "bool":
        return parse_bool(raw_value)
    if datatype not in global_vars.TYPE_CONVERTERS:
        error.unknown_datatype(datatype)

    converter = global_vars.TYPE_CONVERTERS[datatype]
    return converter(raw_value)


# SYNTAX EXAMPLES:
# name = IN(int "Enter a number: ")           - reads integer input
# age = IN(float "Enter your age: ")          - reads floating point input
# message = IN(str "Enter text: ")            - reads string input
# active = IN(bool "Are you active? ")       - reads boolean (true/false, yes/no, 1/0)
