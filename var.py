import error
from variables import global_vars


def assign_variable(name, expr, variables, eval_expression, parse_in_call):
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
