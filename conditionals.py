import re
import error

IF_RE = re.compile(r'^IF\s*(?:\(|\{)\s*(?P<cond>.+?)\s*(?:\)|\})\s*do\s*$')
ELIF_RE = re.compile(r'^Elif\s*(?:\(|\{)\s*(?P<cond>.+?)\s*(?:\)|\})\s*do\s*$')
ELSE_RE = re.compile(r'^Else\s*do\s*$')


def parse_if_header(line):
    m = IF_RE.match(line.strip())
    if not m:
        return None
    return m.group('cond').strip()


def parse_elif_header(line):
    m = ELIF_RE.match(line.strip())
    if not m:
        return None
    return m.group('cond').strip()


def is_else_header(line):
    return bool(ELSE_RE.match(line.strip()))


def read_conditional_block(first_header, readline=None):
    if readline is None:
        readline = lambda: input(">>> ")
    blocks = []  # list of (type, condition, body_lines)
    cond = parse_if_header(first_header)
    if cond is None:
        error.invalid_if_header()
    body = []
    while True:
        line = readline()
        if not line:
            continue
        s = line.strip()
        elif_cond = parse_elif_header(s)
        if is_else_header(s):
            blocks.append(("IF", cond, body))
            # read else body until end
            else_body = []
            while True:
                l2 = readline()
                if not l2:
                    continue
                if l2.strip() in {"end", "endLoop"}:
                    break
                else_body.append(l2)
            blocks.append(("ELSE", None, else_body))
            break
        if elif_cond is not None:
            blocks.append(("IF", cond, body))
            cond = elif_cond
            body = []
            continue
        if s in {"end", "endLoop"}:
            blocks.append(("IF", cond, body))
            break
        body.append(line)
    return blocks


def execute_conditional(blocks, variables, eval_expression, execute_line, condition_truth):
    # CONDITIONAL SYNTAX EXAMPLES:
    # IF ( x > 5 ) do
    #   print("x is greater than 5")
    # end
    #
    # IF { x == 10 } do
    #   print("x equals 10")
    # Elif { x == 5 } do
    #   print("x equals 5")
    # Else do
    #   print("x is something else")
    # end
    for kind, cond, body in blocks:
        if kind == "ELSE":
            for bl in body:
                res = execute_line(bl, variables)
                if res in ('BREAK', 'CONTINUE') or (isinstance(res, tuple) and res[0] == 'RETURN'):
                    return res
            break
        if condition_truth(cond, variables, eval_expression):
            for bl in body:
                res = execute_line(bl, variables)
                if res in ('BREAK', 'CONTINUE') or (isinstance(res, tuple) and res[0] == 'RETURN'):
                    return res
            break

