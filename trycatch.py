import re
import error

TRY_RE   = re.compile(r'^try\s+do\s*$')
CATCH_RE = re.compile(r'^catch\s+(?P<var>[A-Za-z_]\w*)\s+do\s*$')

def is_try_header(line):
    return bool(TRY_RE.match(line.strip()))

def parse_catch_header(line):
    m = CATCH_RE.match(line.strip())
    return m.group('var') if m else None

def read_try_catch(readline):
    try_body, catch_var, catch_body = [], None, []

    # Read try body until 'catch'
    while True:
        line = readline()
        if not line:
            continue
        s = line.strip()
        catch_var = parse_catch_header(s)
        if catch_var is not None:
            break
        try_body.append(line)

    # Read catch body until 'end'
    while True:
        line = readline()
        if not line:
            continue
        if line.strip() == 'end':
            break
        catch_body.append(line)

    return try_body, catch_var, catch_body

def execute_try_catch(try_body, catch_var, catch_body, variables, execute_line):
    try:
        for line in try_body:
            res = execute_line(line, variables)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res
            if res in ('BREAK', 'CONTINUE'):
                return res
    except Exception as exc:
        variables[catch_var] = str(exc)
        for line in catch_body:
            res = execute_line(line, variables)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res
            if res in ('BREAK', 'CONTINUE'):
                return res