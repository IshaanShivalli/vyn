import os
import sys
import re
import error

UNIONS_DIR = os.path.dirname(os.path.abspath(__file__))
if UNIONS_DIR not in sys.path:
    sys.path.insert(0, UNIONS_DIR)

import union_native

UNION_RE = re.compile(r'^union\s+(?P<name>[A-Za-z_]\w*)\s*\{\s*$')
TYPEDEF_RE = re.compile(r'^typedef\s+(?P<original>[A-Za-z_]\w*)\s+as\s+(?P<alias>[A-Za-z_]\w*)\s*$')
FIELD_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*:\s*(?P<type>int|float|char|bool|ptr)\s*$')
NEW_INSTANCE_RE = re.compile(r'^(?P<var>[A-Za-z_]\w*)\s*=\s*(?P<union>[A-Za-z_]\w*)\s*\(\s*\)\s*$')
ATTR_ASSIGN_RE = re.compile(r'^(?P<obj>[A-Za-z_]\w*)\.(?P<field>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$')
ATTR_READ_RE = re.compile(r'^(?P<obj>[A-Za-z_]\w*)\.(?P<field>[A-Za-z_]\w*)$')

_typedef_map = {}


class VynUnionInstance:
    def __init__(self, union_name, handle):
        self.union_name = union_name
        self.handle = handle

    def get_attr(self, name):
        try:
            return union_native.get_field(self.handle, name)
        except ValueError:
            return 'NIL'

    def set_attr(self, name, value):
        try:
            union_native.set_field(self.handle, name, value)
            return value
        except ValueError as exc:
            error.print_error(exc)
            return None

    def __repr__(self):
        fields = union_native.list_fields(self.union_name)
        parts = []
        for fname in fields:
            try:
                parts.append(f"{fname}: {union_native.get_field(self.handle, fname)}")
            except ValueError:
                parts.append(f"{fname}: ?")
        return f"<{self.union_name} {{{', '.join(parts)}}}>"


def resolve_typedef(name):
    seen = set()
    while name in _typedef_map:
        if name in seen:
            error.print_error_msg(f"Circular typedef detected for '{name}'")
            return name
        seen.add(name)
        name = _typedef_map[name]
    return name


def parse_union_header(line):
    m = UNION_RE.match(line.strip())
    if m:
        return m.group('name')
    return None


def parse_typedef(line):
    m = TYPEDEF_RE.match(line.strip())
    if not m:
        return None
    return m.group('original'), m.group('alias')


def parse_field_line(line):
    m = FIELD_RE.match(line.strip())
    if not m:
        return None
    return m.group('name'), m.group('type')


def read_union_body(readline):
    fields = []
    while True:
        line = readline()
        if not line:
            continue
        s = line.strip()
        if s == '}':
            break
        parsed = parse_field_line(s)
        if parsed:
            fields.append(parsed)
    return fields


def handle_union_header(header, readline, eval_expression=None, run_body=None, outer_vars=None):
    name = parse_union_header(header)
    if not name:
        return False
    if union_native.union_exists(name):
        error.print_error_msg(f"Union '{name}' is already defined")
        return True
    fields = read_union_body(readline)
    if not fields:
        error.print_error_msg(f"Union '{name}' has no fields")
        return True
    try:
        union_native.define_union(name, fields)
    except ValueError as exc:
        error.print_error(exc)
        return True
    return True


def handle_typedef(line):
    parsed = parse_typedef(line)
    if not parsed:
        return False
    original, alias = parsed
    if not union_native.union_exists(original) and original not in _typedef_map:
        error.print_error_msg(f"Cannot typedef unknown union '{original}'")
        return True
    _typedef_map[alias] = original
    return True


def try_new_instance(line, variables):
    m = NEW_INSTANCE_RE.match(line.strip())
    if not m:
        return False
    var_name = m.group('var')
    union_name = resolve_typedef(m.group('union'))
    if not union_native.union_exists(union_name):
        return False
    try:
        handle = union_native.new_instance(union_name)
    except ValueError as exc:
        error.print_error(exc)
        return True
    variables[var_name] = VynUnionInstance(union_name, handle)
    return True


def try_attr_assign(line, variables, eval_expression):
    m = ATTR_ASSIGN_RE.match(line.strip())
    if not m:
        return False
    obj_name = m.group('obj')
    field = m.group('field')
    expr = m.group('expr').strip()
    if obj_name not in variables or not isinstance(variables[obj_name], VynUnionInstance):
        return False
    try:
        value = eval_expression(expr, variables)
    except ValueError as exc:
        error.print_error(exc)
        return True
    variables[obj_name].set_attr(field, value)
    return True


def try_attr_read(expr, variables):
    m = ATTR_READ_RE.match(expr.strip())
    if not m:
        return False, None
    obj_name = m.group('obj')
    field = m.group('field')
    if obj_name not in variables or not isinstance(variables[obj_name], VynUnionInstance):
        return False, None
    return True, variables[obj_name].get_attr(field)
