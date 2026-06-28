import re

SWITCH_RE  = re.compile(r'^switch\s*[\(\{]\s*(?P<expr>.+?)\s*[\)\}]\s*do\s*$')
CASE_RE    = re.compile(r'^case\s+(?P<val>.+?)\s+do\s*$')
DEFAULT_RE = re.compile(r'^default\s+do\s*$')

def read_switch(readline):
    cases = []   # list of (value_expr, body_lines)
    default_body = None
    current_val = None
    current_body = []

    while True:
        line = readline()
        if not line:
            continue
        s = line.strip()

        if s == 'endSwitch':
            if current_val is not None:
                cases.append((current_val, current_body))
            elif default_body is None and current_body:
                default_body = current_body
            break

        m_case = CASE_RE.match(s)
        m_default = DEFAULT_RE.match(s)

        if m_case:
            if current_val is not None:
                cases.append((current_val, current_body))
            current_val = m_case.group('val')
            current_body = []
        elif m_default:
            if current_val is not None:
                cases.append((current_val, current_body))
            current_val = None
            current_body = []
            default_body = current_body
        elif s == 'end':
            pass
        else:
            current_body.append(line)

    return cases, default_body

def execute_switch(expr_val, cases, default_body, variables, execute_line, eval_expression):
    for val_expr, body in cases:
        try:
            val = eval_expression(val_expr, variables)
        except:
            continue
        if expr_val == val:
            for line in body:
                res = execute_line(line, variables)
                if isinstance(res, tuple) and res[0] == 'RETURN':
                    return res
                if res in ('BREAK', 'CONTINUE'):
                    return res
            return
    if default_body:
        for line in default_body:
            res = execute_line(line, variables)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res