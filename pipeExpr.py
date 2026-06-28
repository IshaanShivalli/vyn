# pipeExpr.py - Pipeline operator implementation
# Syntax: value |> func1 |> func2 |> func3(extraArg)


def has_pipe(expr):
    """Returns True if expression contains a pipeline operator."""
    return '|>' in expr


def build_pipe_expr(expr):
    """
    Transform a pipeline expression into a nested function call.
    "hello" |> toUpperCase |> reverse
    becomes: reverse(toUpperCase("hello"))
    """
    parts = [p.strip() for p in expr.split('|>')]
    result_expr = parts[0].strip()

    for func in parts[1:]:
        func = func.strip()
        # If func has args e.g. padStart(10, " ")
        # inject piped value as first argument
        if '(' in func and func.endswith(')'):
            fname = func[:func.index('(')]
            existing_args = func[func.index('(')+1:-1].strip()
            if existing_args:
                result_expr = f"{fname}({result_expr}, {existing_args})"
            else:
                result_expr = f"{fname}({result_expr})"
        else:
            # plain function name
            result_expr = f"{func}({result_expr})"

    return result_expr


def resolve_pipe(expr, eval_expression, vars):
    """
    Resolve a pipeline expression and return the final value.
    """
    transformed = build_pipe_expr(expr)
    return eval_expression(transformed, vars)