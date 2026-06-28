import re
from collections import ChainMap

import error


CLASS_RE = re.compile(
    r'^Class\s+(?:obj\s+)?(?P<name>[A-Za-z_]\w*)\s*\(\s*(?P<params>.*?)\s*\)\s*have\s*$'
)
ATTRIBUTE_ASSIGN_RE = re.compile(
    r'^(?P<object>[A-Za-z_]\w*)\.(?P<field>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$'
)


def _parse_param(param):
    param = param.strip()
    if '=' in param:
        name, default = param.split('=', 1)
        return name.strip(), default.strip()
    return param, None


def parse_class_header(line):
    match = CLASS_RE.match(line.strip())
    if not match:
        return None
    raw_params = match.group('params')
    params = [_parse_param(p) for p in raw_params.split(',') if p.strip()]
    return match.group('name'), params


def read_class_body(readline):
    body = []
    while True:
        line = readline()
        if not line:
            continue
        if line.strip() == 'endClass':
            break
        body.append(line)
    return body


class VynObject:
    def __init__(self, class_name, fields):
        self.class_name = class_name
        self.fields = fields

    def get_attr(self, name):
        if name in self.fields:
            return self.fields[name]
        return 'NIL'

    def set_attr(self, name, value):
        self.fields[name] = value
        return value

    def __repr__(self):
        public = {
            key: value
            for key, value in self.fields.items()
            if key != 'this' and not callable(value)
        }
        return f"<{self.class_name} {public}>"


class VynClass:
    def __init__(self, name, params, body, outer_vars, eval_expression, run_body):
        self.name = name
        self.params = params
        self.body = body
        self.outer_vars = outer_vars
        self.eval_expression = eval_expression
        self.run_body = run_body

    def __call__(self, *args):
        fields = {}
        obj = VynObject(self.name, fields)
        fields['this'] = obj

        for i, (name, default) in enumerate(self.params):
            if i < len(args):
                fields[name] = args[i]
            elif default is not None:
                fields[name] = self.eval_expression(default, self.outer_vars)
            else:
                error.print_error_msg(f"Missing constructor argument '{name}'")
                return None

        scope = ChainMap(fields, self.outer_vars)
        self.run_body(self.body, scope)
        return obj

    def __repr__(self):
        return f"<Class {self.name}>"


def make_class(name, params, body, outer_vars, eval_expression, run_body):
    return VynClass(name, params, body, outer_vars, eval_expression, run_body)


def parse_attribute_assignment(line):
    match = ATTRIBUTE_ASSIGN_RE.match(line.strip())
    if not match:
        return None
    return match.group('object'), match.group('field'), match.group('expr').strip()
