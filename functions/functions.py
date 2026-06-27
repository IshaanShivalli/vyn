import ast
import error
import dependency
import library
from .params import parse_function_header, parse_function_call
from loops import parse_for_header, parse_while_header, condition_truth, execute_for_loop, execute_while_loop
from conditionals import read_conditional_block, execute_conditional
from variables import global_vars, local
from input import parse_in_call
from var import assign_variable

dependency.register_io_functions(global_vars.variables)


# ---------------------------------------------------------------------------
# Line source
# ---------------------------------------------------------------------------
# All block readers (IF, loops, function body) pull lines from a thread-local
# line source instead of calling input() directly.  At the REPL the source
# wraps input(); inside a function body it drains the pre-captured body list.
# This is what allows IF/loop blocks inside functions to work correctly.

class _LineSource:
    """Stack of line iterators.  The top iterator is tried first; if it
    raises StopIteration we fall back to the one below (the REPL)."""

    def __init__(self):
        self._stack = []          # list of iterators
        self._repl_prompt = ">>> "

    def push(self, lines):
        """Push an iterable of lines (e.g. function body list)."""
        self._stack.append(iter(lines))

    def pop(self):
        if self._stack:
            self._stack.pop()

    def readline(self, prompt=">>> "):
        while self._stack:
            try:
                return next(self._stack[-1])
            except StopIteration:
                self._stack.pop()
        # Nothing on the stack — read from the real REPL
        return input(prompt)


_source = _LineSource()


def _read_line(prompt=">>> "):
    """Single entry-point for all line reading in the interpreter."""
    return _source.readline(prompt)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def strip_quotes(text):
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text


def split_top_level(text, sep):
    parts = []
    current = []
    quote = None
    depth = 0
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
            depth += 1
            current.append(ch)
            i += 1
            continue
        if ch == ')':
            depth -= 1
            current.append(ch)
            i += 1
            continue
        if depth == 0 and text.startswith(sep, i):
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


# ---------------------------------------------------------------------------
# Block readers  (use _read_line, never input() directly)
# ---------------------------------------------------------------------------

def read_block():
    """Read lines until 'end' or 'endLoop'. Used by loops."""
    body = []
    while True:
        line = _read_line()
        if not line:
            continue
        if line.strip() in {"endLoop", "end"}:
            break
        body.append(line)
    return body


def read_function_body():
    """Read lines until 'endFunc'."""
    body = []
    while True:
        line = _read_line()
        if not line:
            continue
        if line.strip() == 'endFunc':
            break
        body.append(line)
    return body


def _patched_read_conditional_block(first_header):
    """
    Wrapper around conditionals.read_conditional_block that replaces its
    internal input() calls with _read_line so function bodies work correctly.
    """
    import builtins
    original = builtins.input
    builtins.input = _read_line
    try:
        return read_conditional_block(first_header)
    finally:
        builtins.input = original


# ---------------------------------------------------------------------------
# Expression evaluator
# ---------------------------------------------------------------------------

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
        if node.id == 'NIL':
            return 'NIL'
        if node.id in self.variables:
            return self.variables[node.id]
        raise ValueError(f"Undefined variable '{node.id}'")

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
        args = [self.visit(arg) for arg in node.args]
        return func(*args)

    def generic_visit(self, node):
        error.unsupported_expression(ast.dump(node))


def eval_expression(expr, vars=None):
    expr = expr.strip()
    expr = replace_top_level(expr, '++', '+')

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


def eval_print_expression(expr, vars=None):
    if vars is None:
        vars = global_vars.variables
    expr = expr.strip()
    args = split_top_level(expr, ',')
    evaluated = []
    for arg in args:
        evaluated.append(str(eval_expression(arg, vars)))
    return ' '.join(evaluated)


# ---------------------------------------------------------------------------
# Function factory
# ---------------------------------------------------------------------------

def make_fn(params, body, outer_vars):
    def _fn(*call_args):
        current_vars = local.make_function_scope(params, call_args, outer_vars)
        # Push the pre-captured body lines as the active line source.
        # This means any IF/loop block readers will drain from this list
        # instead of blocking on real stdin.
        _source.push(body)
        try:
            while True:
                try:
                    line = _read_line()
                except StopIteration:
                    break
                if not line:
                    continue
                res = execute_line(line, current_vars)
                if isinstance(res, tuple) and res[0] == 'RETURN':
                    return res[1]
                if res in ('BREAK', 'CONTINUE'):
                    return res
        finally:
            # Always pop — even if an exception escapes
            try:
                _source.pop()
            except Exception:
                pass
        return None
    return _fn


# ---------------------------------------------------------------------------
# Main interpreter loop
# ---------------------------------------------------------------------------

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
        try:
            val = eval_expression(parts[1], variables)
        except ValueError as exc:
            error.print_error(exc)
            return
        return ('RETURN', val)

    if stripped.startswith("forLoop"):
        body = read_block()
        execute_for_loop(line, body, variables, eval_expression, execute_line)
        return

    if stripped.startswith("whileLoop"):
        body = read_block()
        execute_while_loop(line, body, variables, eval_expression, execute_line)
        return

    if stripped.startswith("DOF(") and stripped.endswith(")"):
        try:
            filename_part = stripped[4:-1].strip()
            if (filename_part.startswith('"') and filename_part.endswith('"')) or \
               (filename_part.startswith("'") and filename_part.endswith("'")):
                filename = filename_part[1:-1]
            else:
                filename = filename_part
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
        if dependency.is_stdlib_import(imported):
            lib_name = dependency.get_stdlib_name(imported)
            if not library.register_library(lib_name, variables):
                error.print_error_msg(f"Library '{lib_name}' not found")
        else:
            resolved = dependency.resolve_vyn_filename(imported)
            if not resolved or not dependency.exists(resolved):
                error.print_error_msg(f"File not found: {imported}")
                return
            dependency.load_vyn_file(resolved, execute_line, variables)
        return

    if stripped.startswith("IF"):
        blocks = _patched_read_conditional_block(line)
        execute_conditional(blocks, variables, eval_expression, execute_line, condition_truth)
        return

    if stripped.lower().startswith('function'):
        parsed = parse_function_header(stripped)
        if not parsed:
            error.print_error_msg("Invalid function header")
            return
        fname, params = parsed
        body = read_function_body()
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
                # Only auto-print at the top level (source stack is empty).
                # Inside a function body the stack has at least one entry.
                if result is not None and not _source._stack:
                    print(result)
            except Exception as exc:
                error.print_function_call_error(exc)
            return

    if stripped.startswith("print"):
        content = stripped[len("print"):].strip()
        if content.startswith("(") and content.endswith(")"):
            content = content[1:-1].strip()
        try:
            print(eval_print_expression(content, variables))
        except ValueError as exc:
            error.print_error(exc)
        return

    if stripped.startswith("IN"):
        try:
            parse_in_call(stripped)
        except ValueError as exc:
            error.print_error(exc)
        return

    print(line)


# ---------------------------------------------------------------------------
# REPL entry point
# ---------------------------------------------------------------------------

def start():
    while True:
        try:
            line = _read_line()
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
# Function with no parameters:
#   greet = function() perform
#     print("Hello")
#   endFunc
#
# Function with return value:
#   multiply = function(a, b) perform
#     return a * b
#   endFunc