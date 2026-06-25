import ast
import error
import dependency
import library
from .params import parse_function_header, parse_function_call
from loops import parse_for_header, parse_while_header, condition_truth, execute_for_loop, execute_while_loop
from conditionals import read_conditional_block, execute_conditional
from variables import global_vars, local
from input import parse_in_call
from print import Printstr
from var import assign_variable

dependency.register_io_functions(global_vars.variables)


def strip_quotes(text):
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text


def split_top_level(text, sep):
    parts = []
    current = []
    quote = None
    paren_depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            current.append(ch)
            i += 1
            continue
        if ch == '(':
            paren_depth += 1
            current.append(ch)
            i += 1
            continue
        if ch == ')':
            paren_depth -= 1
            current.append(ch)
            i += 1
            continue
        if paren_depth == 0 and text.startswith(sep, i):
            parts.append(''.join(current).strip())
            current = []
            i += len(sep)
            continue
        current.append(ch)
        i += 1
    parts.append(''.join(current).strip())
    return parts


def replace_top_level(text, old, new):
    result = []
    quote = None
    i = 0
    while i < len(text):
        if quote:
            ch = text[i]
            result.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if text[i] in ('"', "'"):
            quote = text[i]
            result.append(text[i])
            i += 1
            continue
        if text.startswith(old, i):
            result.append(new)
            i += len(old)
            continue
        result.append(text[i])
        i += 1
    return ''.join(result)


class ExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, variables_map):
        self.variables = variables_map

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        if isinstance(node.op, ast.BitAnd):
            return str(left) + str(right)
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left ** right
        error.unsupported_operator(ast.dump(node.op))

    def visit_Compare(self, node):
        left = self.visit(node.left)
        results = []
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Lt):
                results.append(left < right)
            elif isinstance(op, ast.LtE):
                results.append(left <= right)
            elif isinstance(op, ast.Gt):
                results.append(left > right)
            elif isinstance(op, ast.GtE):
                results.append(left >= right)
            elif isinstance(op, ast.Eq):
                results.append(left == right)
            elif isinstance(op, ast.NotEq):
                results.append(left != right)
            else:
                error.unsupported_comparator(ast.dump(op))
            left = right
        return all(results)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            return not operand
        error.unsupported_unary_operator(ast.dump(node.op))

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            for value in node.values:
                v = self.visit(value)
                if not v:
                    return False
            return True
        if isinstance(node.op, ast.Or):
            for value in node.values:
                v = self.visit(value)
                if v:
                    return True
            return False
        error.unsupported_boolean_operator(ast.dump(node.op))

    def visit_IfExp(self, node):
        test = self.visit(node.test)
        if test:
            return self.visit(node.body)
        return self.visit(node.orelse)

    def visit_Name(self, node):
        if node.id == 'true':
            return True
        if node.id == 'false':
            return False
        if node.id == 'nil':
            return 'NIL'
        if node.id in self.variables:
            return self.variables[node.id]
        return 'NIL'

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return node.value
        if isinstance(node.value, (int, float, bool)):
            return node.value
        error.unsupported_constant(node.value)

    def visit_Num(self, node):
        return node.n

    def visit_Str(self, node):
        return node.s

    def visit_Call(self, node):
        func = self.visit(node.func)
        if func == 'NIL':
            return 'NIL'
        if not callable(func):
            error.not_a_function()

        # Positional arguments
        args = [self.visit(arg) for arg in node.args]

        # Keyword arguments (NEW)
        kwargs = {}
        for kw in node.keywords:
            if kw.arg is not None:
                kwargs[kw.arg] = self.visit(kw.value)

        if kwargs:
            return func(*args, **kwargs)
        else:
            return func(*args)

    def generic_visit(self, node):
        error.unsupported_expression(ast.dump(node))


def eval_expression(expr, vars=None):
    expr = expr.strip()
    expr = replace_top_level(expr, '++', ' & ')

    def transform_ternary(s):
        s = s.strip()
        i = 0
        quote = None
        depth = 0
        while i < len(s):
            ch = s[i]
            if quote:
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in ('"', "'"):
                quote = ch
                i += 1
                continue
            if ch == '(':
                depth += 1
                i += 1
                continue
            if ch == ')':
                depth -= 1
                i += 1
                continue
            if ch == '?' and depth == 0:
                qpos = i
                j = i + 1
                q = None
                d = 0
                while j < len(s):
                    cj = s[j]
                    if q:
                        if cj == q:
                            q = None
                        j += 1
                        continue
                    if cj in ('"', "'"):
                        q = cj
                        j += 1
                        continue
                    if cj == '(':
                        d += 1
                        j += 1
                        continue
                    if cj == ')':
                        d -= 1
                        j += 1
                        continue
                    if cj == ':' and d == 0:
                        colon = j
                        cond = s[:qpos].strip()
                        true_part = s[qpos+1:colon].strip()
                        false_part = s[colon+1:].strip()
                        new = f"({true_part}) if ({cond}) else ({false_part})"
                        return transform_ternary(new)
                    j += 1
                return s
            i += 1
        return s

    expr = transform_ternary(expr)
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError:
        error.invalid_expression(expr)
    if vars is None:
        vars = global_vars.variables
    evaluator = ExpressionEvaluator(vars)
    return evaluator.visit(tree)


def eval_print_expression(expr):
    expr = expr.strip()
    if not expr:
        return ''
    args = split_top_level(expr, ',')
    evaluated = []
    for arg in args:
        evaluated.append(str(eval_expression(arg)))
    return ' '.join(evaluated)





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


def make_fn(params, body, variables):
    def _fn(*call_args):
        current_vars = local.make_function_scope(params, call_args, variables)
        for bl in body:
            res = execute_line(bl, current_vars)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res[1]
        return None
    return _fn


def execute_line(line, variables=None):
    if variables is None:
        variables = global_vars.variables

    stripped = line.strip()
    if not stripped:
        return

    if stripped == 'break':
        return 'BREAK'
    if stripped == 'continue':
        return 'CONTINUE'
    if stripped.startswith('return'):
        parts = stripped.split(None, 1)
        if len(parts) == 1:
            return ('RETURN', None)
        expr = parts[1]
        try:
            val = eval_expression(expr, variables)
        except ValueError as exc:
            error.print_error(exc)
            return
        return ('RETURN', val)

    if stripped.startswith("forLoop"):
        body = read_block()
        return execute_for_loop(line, body, variables, eval_expression, execute_line)

    if stripped.startswith("whileLoop"):
        body = read_block()
        return execute_while_loop(line, body, variables, eval_expression, execute_line)

    # Handle DOF("filename") - Execute file and show output
    if stripped.startswith("DOF(") and stripped.endswith(")"):
        try:
            # Extract filename from DOF("filename")
            filename_part = stripped[4:-1].strip()
            # Remove quotes
            if (filename_part.startswith('"') and filename_part.endswith('"')) or \
               (filename_part.startswith("'") and filename_part.endswith("'")):
                filename = filename_part[1:-1]
            else:
                filename = filename_part
            
            # Resolve and load the file
            resolved = dependency.resolve_vyn_filename(filename)
            if not resolved or not dependency.exists(resolved):
                error.print_error_msg(f"File not found: {filename}")
                return
            
            print(f"\n--- Executing {filename} ---")
            dependency.load_vyn_file(resolved, execute_line, variables)
            print(f"--- Finished {filename} ---\n")
        except Exception as exc:
            error.print_error(exc)
        return

    imported = dependency.parse_import(stripped)
    if imported:
        # Check if it's a standard library import
        if dependency.is_stdlib_import(imported):
            lib_name = dependency.get_stdlib_name(imported)
            if not library.register_library(lib_name, variables):
                error.print_error_msg(f"Library '{lib_name}' not found")
            return
        
        # Otherwise load as .vyn file
        resolved = dependency.resolve_vyn_filename(imported)
        if not resolved or not dependency.exists(resolved):
            error.print_error_msg("File not found")
            return
        dependency.load_vyn_file(resolved, execute_line, variables)
        return

    if stripped.startswith("IF"):
        blocks = read_conditional_block(line)
        return execute_conditional(blocks, variables, eval_expression, execute_line, condition_truth)

    if stripped.lower().startswith('function'):
        parsed = parse_function_header(stripped)
        if not parsed:
            error.print_error_msg("Invalid function header")
            return
        fname, params = parsed
        body = []
        while True:
            l = input('>>> ')
            if not l:
                continue
            if l.strip() == 'endFunc':
                break
            body.append(l)
        if not fname:
            error.print_error_msg("unnamed standalone function must be assigned to a variable")
            return
        variables[fname] = make_fn(params, body, variables)
        return

    assignment = global_vars.ASSIGNMENT_RE.match(stripped)
    if assignment:
        name = assignment.group("name")
        expr = assignment.group("expr").strip()
        assign_variable(name, expr, variables, eval_expression, parse_in_call)
        return

    function_call = parse_function_call(stripped)
    if function_call:
        fname, args_text = function_call
        if fname in variables and callable(variables[fname]):
            parts = split_top_level(args_text, ',') if args_text.strip() else []
            evaluated = []
            try:
                for p in parts:
                    evaluated.append(eval_expression(p, variables))
            except ValueError as exc:
                error.print_error(exc)
                return
            try:
                result = variables[fname](*evaluated)
                if result is not None:
                    print(result)
            except Exception as exc:
                error.print_function_call_error(exc)
            return

    if stripped.startswith("print"):
        Printstr(line)
        return

    if stripped.startswith("IN"):
        try:
            parse_in_call(stripped)
        except ValueError as exc:
            error.print_error(exc)
        return

    print(line)


def start():
    while True:
        try:
            line = input(">>> ")
            if not line:
                break
            execute_line(line, global_vars.variables)
        except EOFError:
            break


# FUNCTION DEFINITION & CALLING:
# Basic function:
#   myFunc = function(x, y) perform
#     sum = x + y
#     return sum
#   endFunc
#
# Calling a function:
#   result = myFunc(3, 5)
#   myFunc(10, 20)
#
# Function without name (standalone):
#   function(a, b) perform
#     print(a + b)
#   endFunc
#
# Function with no parameters:
#   greet = function() perform
#     print("Hello")
#   endFunc
#
# Function with return value:
#   multiply = function(a, b) perform
#     return a * b
#   endFunc
