import error
from variables import global_vars
import re
import lock as lock_module

CONST_RE = re.compile(r'^const\s+(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$')


def assign_variable(name, expr, variables, eval_expression, parse_in_call, execute_line=None):
    # FIX: check lock before doing anything
    if lock_module.is_locked(name):
        error.print_error_msg(f"Cannot modify '{name}' — variable is locked")
        return
    if name in global_vars.constants:
        error.print_error_msg(f"Cannot reassign constant '{name}'")
        return
    expr = expr.strip()
    if expr.startswith("IN"):
        try:
            variables[name] = parse_in_call(expr)
        except ValueError as exc:
            error.print_error(exc)
    elif expr.lower().startswith('function'):
        from functions.params import parse_function_header
        from functions.functions import make_fn

        parsed = parse_function_header(expr)
        if not parsed:
            error.print_error_msg("Invalid function header")
            return
        _, params = parsed
        body = []
        while True:
            l = input('>>> ')
            if not l:
                continue
            if l.strip() == 'endFunc':
                break
            body.append(l)
        variables[name] = make_fn(params, body, variables)
    else:
        try:
            variables[name] = eval_expression(expr, variables)
        except ValueError as exc:
            error.print_error(exc)
    update_reactive(name, variables, eval_expression)
    trigger_watchers(name, variables, execute_line)

AUGMENTED_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*(?P<op>[+\-*\/])=\s*(?P<expr>.+)$')

def handle_augmented(line, variables, eval_expression):
    m = AUGMENTED_RE.match(line.strip())
    if not m:
        return False
    name = m.group('name')
    op = m.group('op')
    expr = m.group('expr').strip()
    if name not in variables:
        error.print_error_msg(f"Undefined variable '{name}'")
        return True
    right = eval_expression(expr, variables)
    left = variables[name]
    if op == '+':
        variables[name] = str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
    elif op == '-': variables[name] = left - right
    elif op == '*': variables[name] = left * right
    elif op == '/': variables[name] = left / right
    return True

def handle_const(line, variables, eval_expression, parse_in_call):
    m = CONST_RE.match(line.strip())
    if not m:
        return False
    name = m.group('name')
    expr = m.group('expr').strip()
    if name in global_vars.constants:
        error.print_error_msg(f"Cannot reassign constant '{name}'")
        return True
    assign_variable(name, expr, variables, eval_expression, parse_in_call)
    global_vars.constants.add(name)
    return True


def update_reactive(changed_var, variables, eval_expression):
    """Called after every assignment to recalculate dependent reactive vars."""
    from variables import global_vars
    deps = global_vars.dependencies.get(changed_var, set())
    for react_name in deps:
        expr = global_vars.reactive.get(react_name)
        if expr:
            try:
                variables[react_name] = eval_expression(expr, variables)
            except Exception:
                pass

def trigger_watchers(name, variables, execute_line):
    """Called after every assignment to fire any watchers on that variable."""
    from variables import global_vars
    watchers = global_vars.watchers.get(name, [])
    for body in watchers:
        for line in body:
            execute_line(line, variables)


# SYNTAX EXAMPLES FOR VARIABLE ASSIGNMENT:
# x = 10                                       - simple assignment
# name = "John"                                - string assignment
# result = x + 5                               - arithmetic expression
# message = IN(str "Enter text: ")            - input assignment
#
# SYNTAX EXAMPLES FOR FUNCTION DEFINITION:
# myFunc = function(x, y) perform              - function with parameters
#   return x + y
# endFunc
#
# SYNTAX EXAMPLES FOR LOOPS:
# forLoop i = 1 to 10                          - for loop from 1 to 10
#   print(i)
# endLoop
#
# whileLoop x < 100                            - while loop
#   x = x + 1
# endLoop
