import re
import error

IMPL_RE = re.compile(r'^impl\s+(?P<trait>[A-Za-z_]\w*)\s+for\s+(?P<type>[A-Za-z_]\w*)\s*\{\s*$')
METHOD_RE = re.compile(r'^method\s+(?P<name>[A-Za-z_]\w*)\s*\(\s*(?P<params>.*?)\s*\)\s*\{\s*$')

def parse_impl_header(line):
    m = IMPL_RE.match(line.strip())
    if not m:
        return None
    return m.group('trait'), m.group('type')

def read_impl_body(readline, outer_vars, eval_expression, run_body):
    methods = {}
    while True:
        line = readline()
        if not line:
            continue
        if line.strip() == '}':
            break
        m = METHOD_RE.match(line.strip())
        if not m:
            error.print_error_msg(f"Invalid method signature: {line.strip()}")
            continue
        name = m.group('name')
        params = [p.strip() for p in m.group('params').split(',') if p.strip()]
        # Read method body until }
        body = []
        while True:
            bline = readline()
            if not bline:
                continue
            if bline.strip() == '}':
                break
            body.append(bline)
        methods[name] = (params, body, outer_vars, eval_expression, run_body)
    return methods