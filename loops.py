import re
import error

FOR_RE = re.compile(r'^forLoop\s*\{\s*(?P<init>[^;]+?)\s*;\s*(?P<cond>[^;]+?)\s*;\s*(?P<step>[^}]+?)\s*\}\s*do\s*$')
FORIN_RE = re.compile(r'^forIn\s*\{\s*(?P<var>[A-Za-z_]\w*)\s+in\s+(?P<iter>.+?)\s*\}\s*do\s*$')
WHILE_RE = re.compile(r'^whileLoop\s*\{\s*(?P<cond>.+?)\s*\}\s*do\s*$')
IDENTIFIER_RE = re.compile(r'^[A-Za-z_]\w*$')



def parse_for_header(line):
    match = FOR_RE.match(line.strip())
    if not match:
        error.invalid_forloop_syntax()

    init = match.group("init").strip()
    cond = match.group("cond").strip()
    step = match.group("step").strip()
    if ':' not in step:
        error.invalid_forloop_increment_syntax()

    step_var, step_expr = [part.strip() for part in step.split(':', 1)]
    if not IDENTIFIER_RE.match(step_var):
        error.invalid_forloop_increment_variable()

    return init, cond, step_var, step_expr


def parse_while_header(line):
    match = WHILE_RE.match(line.strip())
    if not match:
        error.invalid_whileloop_syntax()
    return match.group("cond").strip()


def condition_truth(expr, variables, eval_expression):
    # FIX: pass variables so condition uses correct scope
    value = eval_expression(expr, variables)
    if value == 'NIL':
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) != 0
    return bool(value)


# LOOP SYNTAX EXAMPLES:
# forLoop { i = 1; i < 10; i: i + 1 } do
#   print(i)
# endLoop
#
# whileLoop { x < 100 } do
#   x = x + 1
#   print(x)
# endLoop
def read_block():
    body = []
    while True:
        line = input(">>> ")
        if not line:
            continue
        if line.strip() in {"endLoop", "end"}:
            break
        body.append(line)
    return body





def execute_for_loop(header, body_lines, variables, eval_expression, execute_line):
    try:
        init, cond, step_var, step_expr = parse_for_header(header)
    except ValueError as exc:
        error.print_error(exc)
        return

    init_match = re.match(r'^(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$', init)
    if not init_match:
        error.print_error_msg("Invalid forLoop init")
        return

    init_name = init_match.group("name")
    init_expr = init_match.group("expr").strip()
    try:
        variables[init_name] = eval_expression(init_expr, variables)
    except ValueError as exc:
        error.print_error(exc)
        return

    while condition_truth(cond, variables, eval_expression):
        for body_line in body_lines:
            # FIX: pass variables so loop body uses correct scope
            res = execute_line(body_line, variables)
            if res == 'BREAK':
                return
            if res == 'CONTINUE':
                break
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res
        else:
            # Only step if we didn't break/continue
            try:
                variables[step_var] = eval_expression(step_expr, variables)
            except ValueError as exc:
                error.print_error(exc)
                return
            continue
        # CONTINUE hit: step then loop again
        try:
            variables[step_var] = eval_expression(step_expr, variables)
        except ValueError as exc:
            error.print_error(exc)
            return


def execute_while_loop(header, body_lines, variables, eval_expression, execute_line):
    try:
        cond = parse_while_header(header)
    except ValueError as exc:
        error.print_error(exc)
        return

    while condition_truth(cond, variables, eval_expression):
        for body_line in body_lines:
            # FIX: pass variables so loop body uses correct scope
            res = execute_line(body_line, variables)
            if res == 'BREAK':
                return
            if res == 'CONTINUE':
                break
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res



def parse_forin_header(line):
    m = FORIN_RE.match(line.strip())
    if not m:
        return None
    return m.group('var').strip(), m.group('iter').strip()

def execute_forin_loop(header, body_lines, variables, eval_expression, execute_line):
    parsed = parse_forin_header(header)
    if not parsed:
        error.print_error_msg("Invalid forIn syntax")
        return
    var_name, iter_expr = parsed
    try:
        iterable = eval_expression(iter_expr, variables)
    except ValueError as exc:
        error.print_error(exc)
        return
    if not hasattr(iterable, '__iter__'):
        error.print_error_msg(f"'{iter_expr}' is not iterable")
        return
    for item in iterable:
        variables[var_name] = item
        for line in body_lines:
            res = execute_line(line, variables)
            if res == 'BREAK':
                return
            if res == 'CONTINUE':
                break
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res


# LOOP SYNTAX:
# forLoop { init; condition; step } do
#   statements
# endLoop
#
# whileLoop { condition } do
#   statements
# endLoop
#
# break   - exit loop
# continue - skip to next iteration