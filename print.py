import error


def Printstr(output):
    from functions.functions import eval_print_expression
    
    content = output.strip()
    if content.startswith("print"):
        content = content[len("print"):].strip()
    if content.startswith("(") and content.endswith(")"):
        content = content[1:-1].strip()
    try:
        print(eval_print_expression(content))
    except ValueError as exc:
        error.print_error(exc)


# SYNTAX EXAMPLES:
# print(expression)           - prints a single expression
# print(x, y, z)             - prints multiple expressions separated by spaces
# print("hello" + " world")  - prints string concatenation
# print(count + 1)           - prints arithmetic expression
