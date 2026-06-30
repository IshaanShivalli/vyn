# vyn_struct_syntax.py - Vyn syntax layer for struct/union/typedef
# Wraps struct_native.py (the C-backed engine) behind Vyn syntax

import re
import error
import struct_native
from struct_methods import StructMethod


STRUCT_RE = re.compile(r'^struct\s+(?P<name>[A-Za-z_]\w*)\s*\{\s*$')
UNION_RE = re.compile(r'^union\s+(?P<name>[A-Za-z_]\w*)\s*\{\s*$')
TYPEDEF_RE = re.compile(r'^typedef\s+(?P<original>[A-Za-z_]\w*)\s+as\s+(?P<alias>[A-Za-z_]\w*)\s*$')
FIELD_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*:\s*(?P<type>int|float|char|bool|ptr)\s*$')
NEW_INSTANCE_RE = re.compile(r'^(?P<var>[A-Za-z_]\w*)\s*=\s*(?P<struct>[A-Za-z_]\w*)\s*\(\s*\)\s*$')
ATTR_ASSIGN_RE = re.compile(r'^(?P<obj>[A-Za-z_]\w*)\.(?P<field>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$')
ATTR_READ_RE = re.compile(r'^(?P<obj>[A-Za-z_]\w*)\.(?P<field>[A-Za-z_]\w*)$')

# alias name -> real struct name
_typedef_map = {}


class VynStructInstance:
    def __init__(self, struct_name, handle, methods=None):
        self.struct_name = struct_name
        self.handle = handle
        self._methods = methods or {}

    def get_attr(self, name):
    # Check if we already have this method bound
        if name in self._methods:
            return self._methods[name].__get__(self)

        # Check if this struct has method definitions stored
        if hasattr(struct_native, "_struct_methods"):
            method_defs = struct_native._struct_methods.get(self.struct_name, {})
            if name in method_defs:
                params, body = method_defs[name]
                # Create StructMethod on the fly
                method = StructMethod(
                    name, 
                    params, 
                    body, 
                    {},                    # outer_vars (can improve later)
                    None,                  # eval_expression (we'll handle inside StructMethod)
                    None                   # run_body
                )
                self._methods[name] = method
                return method.__get__(self)

        # Otherwise it's a normal field
        try:
            return struct_native.get_field(self.handle, name)
        except ValueError:
            return 'NIL'

    def set_attr(self, name, value):
        try:
            struct_native.set_field(self.handle, name, value)
            return value
        except ValueError as exc:
            error.print_error(exc)
            return None

    def __repr__(self):
        fields = struct_native.list_fields(self.struct_name)
        parts = []
        for fname in fields:
            try:
                parts.append(f"{fname}: {struct_native.get_field(self.handle, fname)}")
            except ValueError:
                parts.append(f"{fname}: ?")
        return f"<{self.struct_name} {{{', '.join(parts)}}}>"


def resolve_typedef(name):
    """Follow typedef chain back to the real struct name."""
    seen = set()
    while name in _typedef_map:
        if name in seen:
            error.print_error_msg(f"Circular typedef detected for '{name}'")
            return name
        seen.add(name)
        name = _typedef_map[name]
    return name


def parse_struct_header(line):
    m = STRUCT_RE.match(line.strip())
    if m:
        return m.group('name'), False
    m = UNION_RE.match(line.strip())
    if m:
        return m.group('name'), True
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


def read_struct_body(readline):
    fields = []
    methods = {}   # Store methods here

    while True:
        line = readline()
        if not line:
            continue
        s = line.strip()

        if s == '}':
            break

        # Check for method
        if s.startswith('method '):
            method_name, params, body = parse_method_definition(s, readline)
            if method_name:
                methods[method_name] = (params, body)
            continue

        # Normal field
        parsed = parse_field_line(s)
        if parsed:
            fields.append(parsed)

    return fields, methods


def parse_method_definition(first_line, readline):
    # Very basic method parser (you can improve later)
    import re
    match = re.match(r'method\s+(\w+)\s*\((.*?)\)\s*\{?\s*$', first_line.strip())
    if not match:
        return None, None, None

    name = match.group(1)
    params = [p.strip() for p in match.group(2).split(',') if p.strip()]
    body = []

    while True:
        line = readline()
        if not line:
            continue
        if line.strip() == '}':
            break
        body.append(line)

    return name, params, body

def handle_struct_header(header, readline):
    parsed = parse_struct_header(header)
    if not parsed:
        return False

    name, is_union = parsed
    if struct_native.struct_exists(name):
        error.print_error_msg(f"Struct '{name}' is already defined")
        return True

    # FIX: unpack both fields and methods
    fields, methods = read_struct_body(readline)

    if not fields:
        error.print_error_msg(f"Struct '{name}' has no fields")
        return True

    try:
        struct_native.define_struct(name, fields, is_union=is_union)
    except ValueError as exc:
        error.print_error(exc)
        return True

    # Store methods so we can attach them later when creating instances
    if not hasattr(struct_native, "_struct_methods"):
        struct_native._struct_methods = {}
    struct_native._struct_methods[name] = methods

    return True


def handle_typedef(line):
    parsed = parse_typedef(line)
    if not parsed:
        return False
    original, alias = parsed
    if not struct_native.struct_exists(original) and original not in _typedef_map:
        error.print_error_msg(f"Cannot typedef unknown struct '{original}'")
        return True
    _typedef_map[alias] = original
    return True


def try_new_instance(line, variables):
    m = NEW_INSTANCE_RE.match(line.strip())
    if not m:
        return False

    var_name = m.group('var')
    struct_name = resolve_typedef(m.group('struct'))

    if not struct_native.struct_exists(struct_name):
        return False

    try:
        handle = struct_native.new_instance(struct_name)
    except ValueError as exc:
        error.print_error(exc)
        return True

    # Create instance WITHOUT methods for now (we'll attach them later)
    variables[var_name] = VynStructInstance(struct_name, handle)
    return True


def try_attr_assign(line, variables, eval_expression):
    """
    Handles: p.x = 5
    Returns True if matched (and handled), else False.
    """
    m = ATTR_ASSIGN_RE.match(line.strip())
    if not m:
        return False

    obj_name = m.group('obj')
    field = m.group('field')
    expr = m.group('expr').strip()

    if obj_name not in variables or not isinstance(variables[obj_name], VynStructInstance):
        return False  # not a struct instance — let oop.py's attribute handling try it

    try:
        value = eval_expression(expr, variables)
    except ValueError as exc:
        error.print_error(exc)
        return True

    variables[obj_name].set_attr(field, value)
    return True


def try_attr_read(expr, variables):
    """
    Handles reading p.x inside expressions.
    Returns (True, value) if matched, else (False, None).
    """
    m = ATTR_READ_RE.match(expr.strip())
    if not m:
        return False, None

    obj_name = m.group('obj')
    field = m.group('field')

    if obj_name not in variables or not isinstance(variables[obj_name], VynStructInstance):
        return False, None

    return True, variables[obj_name].get_attr(field)


def free_struct_instance(var_name, variables):
    """Optional explicit free: freeStruct(p)"""
    if var_name not in variables or not isinstance(variables[var_name], VynStructInstance):
        error.print_error_msg(f"'{var_name}' is not a struct instance")
        return
    struct_native.free_instance(variables[var_name].handle)
    del variables[var_name]


# STRUCT SYNTAX EXAMPLES:
# struct Point {
#   x: int
#   y: float
# }
#
# union Number {
#   i: int
#   f: float
# }
#
# typedef Point as Coord
#
# p = Point()
# p.x = 5
# p.y = 2.5
# print(p.x)