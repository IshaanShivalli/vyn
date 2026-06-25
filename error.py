def invalid_bool_value(value):
    raise ValueError(f"Invalid bool value: {value}")


def invalid_in_syntax():
    raise ValueError("Invalid IN(...) syntax")


def unknown_datatype(datatype):
    raise ValueError(f"Unknown datatype '{datatype}'")


def unsupported_operator(op):
    raise ValueError(f"Unsupported operator: {op}")


def unsupported_comparator(op):
    raise ValueError(f"Unsupported comparator: {op}")


def unsupported_unary_operator(op):
    raise ValueError(f"Unsupported unary operator: {op}")


def unsupported_boolean_operator(op):
    raise ValueError(f"Unsupported boolean operator: {op}")


def unsupported_constant(value):
    raise ValueError(f"Unsupported constant: {value!r}")


def not_a_function():
    raise ValueError("Not a function")


def unsupported_expression(node):
    raise ValueError(f"Unsupported expression: {node}")


def invalid_expression(expr):
    raise ValueError(f"Invalid expression: {expr}")


def invalid_forloop_syntax():
    raise ValueError("Invalid forLoop syntax")


def invalid_forloop_increment_syntax():
    raise ValueError("Invalid forLoop increment syntax")


def invalid_forloop_increment_variable():
    raise ValueError("Invalid forLoop increment variable")


def invalid_whileloop_syntax():
    raise ValueError("Invalid whileLoop syntax")


def invalid_if_header():
    raise ValueError("Invalid IF header")


def invalid_forloop_init():
    raise ValueError("Invalid forLoop init")


def print_error(exc):
    print(f"Error: {exc}")


def print_error_msg(message):
    print(f"Error: {message}")


def print_function_call_error(exc):
    print(f"Error in function call: {exc}")


# ERROR HANDLING MODULE: Provides error reporting for the interpreter
# No direct language syntax - handles internal error messages
