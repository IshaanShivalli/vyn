import ast
import re
import copy
import error
import dependency
import library
from .params import parse_function_header, parse_function_call
from loops import (parse_for_header, parse_while_header, condition_truth,
                   execute_for_loop, execute_while_loop, execute_forin_loop,
                   execute_repeatuntil_loop, read_block)
from conditionals import read_conditional_block, execute_conditional
from variables import global_vars, local
from input import parse_in_call
from var import assign_variable, handle_augmented, handle_const
from trycatch import is_try_header, read_try_catch, execute_try_catch
from switch import read_switch, execute_switch, SWITCH_RE
import lazy as lazy_module
import lock as lock_module
import ghost as ghost_module
import oop as oop_module
import memory as mem_module
from pipeExpr import has_pipe, resolve_pipe

# FIX: import time module from lib/ for timed block support
import importlib.util as _ilu
import os as _os
import sys

structs_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "structs")
unions_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "unions")

# 1. Load struct_native first
struct_native_spec = _ilu.spec_from_file_location(
    "struct_native",
    _os.path.join(structs_dir, "struct_native.py")
)
struct_native_mod = _ilu.module_from_spec(struct_native_spec)
sys.modules["struct_native"] = struct_native_mod
struct_native_spec.loader.exec_module(struct_native_mod)

# 2. Now load vyn_struct_syntax
vyn_struct_spec = _ilu.spec_from_file_location(
    "vyn_struct_syntax",
    _os.path.join(structs_dir, "vyn_struct_syntax.py")
)
vyn_struct_syntax = _ilu.module_from_spec(vyn_struct_spec)
vyn_struct_spec.loader.exec_module(vyn_struct_syntax)

# 3. Load union runtime and syntax
union_native_spec = _ilu.spec_from_file_location(
    "union_native",
    _os.path.join(unions_dir, "union_native.py")
)
union_native_mod = _ilu.module_from_spec(union_native_spec)
sys.modules["union_native"] = union_native_mod
union_native_spec.loader.exec_module(union_native_mod)

vyn_union_spec = _ilu.spec_from_file_location(
    "vyn_union_syntax",
    _os.path.join(unions_dir, "union_syntax.py")
)
vyn_union_syntax = _ilu.module_from_spec(vyn_union_spec)
vyn_union_spec.loader.exec_module(vyn_union_syntax)

_timed_spec = _ilu.spec_from_file_location(
    "vyn_time",
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'lib', 'time.py')
)
timed_module = _ilu.module_from_spec(_timed_spec)
_timed_spec.loader.exec_module(timed_module)

dependency.register_io_functions(global_vars.variables)
global_vars.variables.update({
    'memsize': mem_module.memsize,
    'memzero': mem_module.memzero,
    'memcopy': mem_module.memcopy,
    'memdump': mem_module.memdump,
    'sizeof': mem_module.sizeof,
})

LAMBDA_RE = re.compile(r'^lambda\s+(?P<params>[\w,\s]*)\s*:\s*(?P<expr>.+)$')
MEM_ALLOC_RE = re.compile(r'^mem\s+(?P<name>[A-Za-z_]\w*)\s*<-\s*(?P<size>.+)$')
MEM_WRITE_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)@(?P<idx>.+?)\s*=\s*(?P<val>.+)$')
AT_RE = re.compile(r'([A-Za-z_]\w*)@(\w+)')
_EXPR_CACHE = {}
_MAX_EXPR_CACHE_SIZE = 256


def _get_cached_ast(expr):
    cached = _EXPR_CACHE.get(expr)
    if cached is not None:
        return cached
    tree = ast.parse(expr, mode='eval')
    if len(_EXPR_CACHE) >= _MAX_EXPR_CACHE_SIZE:
        _EXPR_CACHE.clear()
    _EXPR_CACHE[expr] = tree
    return tree

# ---------------------------------------------------------------------------
# Line source
# ---------------------------------------------------------------------------

class _LineSource:
    def __init__(self):
        self._stack = []

    def push(self, lines, stop_at_end=False):
        self._stack.append((iter(lines), stop_at_end))

    def pop(self):
        if self._stack:
            self._stack.pop()

    def readline(self, prompt=">>> "):
        while self._stack:
            try:
                return next(self._stack[-1][0])
            except StopIteration:
                _, stop_at_end = self._stack[-1]
                self._stack.pop()
                if stop_at_end:
                    raise
        return input(prompt)

    def at_top_level(self):
        return not self._stack


_source = _LineSource()


def _read_line(prompt=">>> "):
    return _source.readline(prompt)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def strip_quotes(text):
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text


def split_top_level(text, sep):
    parts, current, quote, depth = [], [], None, 0
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            current.append(ch)
            if ch == quote: quote = None
            i += 1; continue
        if ch in ('"', "'"):
            quote = ch; current.append(ch); i += 1; continue
        if ch == '(':
            depth += 1; current.append(ch); i += 1; continue
        if ch == ')':
            depth -= 1; current.append(ch); i += 1; continue
        if depth == 0 and text.startswith(sep, i):
            parts.append(''.join(current).strip())
            current = []; i += len(sep); continue
        current.append(ch); i += 1
    parts.append(''.join(current).strip())
    return parts


def replace_top_level(text, old, new):
    result, quote, i = [], None, 0
    while i < len(text):
        if quote:
            ch = text[i]; result.append(ch)
            if ch == quote: quote = None
            i += 1; continue
        if text[i] in ('"', "'"):
            quote = text[i]; result.append(text[i]); i += 1; continue
        if text.startswith(old, i):
            result.append(new); i += len(old); continue
        result.append(text[i]); i += 1
    return ''.join(result)


def interpolate(s, variables, eval_expr):
    def replacer(m):
        try:
            return str(eval_expr(m.group(1).strip(), variables))
        except Exception:
            return m.group(0)
    return re.sub(r'\{([^}]+)\}', replacer, s)


def _run_body(body, variables):
    """
    FIX: Push body onto _source and drain it via execute_line.
    Used by proof, watch, lock, timed blocks so that nested
    forLoop/whileLoop/IF inside them work correctly.
    Previously these blocks used plain 'for bl in body' loops
    which bypassed _source, causing nested blocks to hang on input().
    """
    _source.push(body, stop_at_end=True)
    try:
        while True:
            try:
                line = _read_line()
            except StopIteration:
                break
            if not line:
                continue
            res = execute_line(line, variables)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                return res
            if res in ('BREAK', 'CONTINUE'):
                return res
    finally:
        _source.pop()
    return None


# ---------------------------------------------------------------------------
# Block readers
# ---------------------------------------------------------------------------

def read_function_body():
    body = []
    while True:
        line = _read_line()
        if not line:
            continue
        if line.strip() == 'endFunc':
            break
        body.append(line)
    return body


def _read_conditional_block(first_header):
    return read_conditional_block(first_header, readline=_read_line)


def read_class_body():
    return oop_module.read_class_body(_read_line)


# ---------------------------------------------------------------------------
# Expression evaluator
# ---------------------------------------------------------------------------

class ExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, variables_map):
        self.variables = variables_map

    def visit_Expression(self, node): return self.visit(node.body)

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return str(left)+str(right) if isinstance(left,str) or isinstance(right,str) else left+right
        if isinstance(op, ast.Sub):  return left - right
        if isinstance(op, ast.Mult): return left * right
        if isinstance(op, ast.Div):  return left / right
        if isinstance(op, ast.Mod):  return left % right
        if isinstance(op, ast.Pow):  return left ** right
        error.unsupported_operator(ast.dump(op))

    def visit_Compare(self, node):
        left = self.visit(node.left)
        results = []
        for op, comp in zip(node.ops, node.comparators):
            right = self.visit(comp)
            if   isinstance(op, ast.Lt):    results.append(left <  right)
            elif isinstance(op, ast.LtE):   results.append(left <= right)
            elif isinstance(op, ast.Gt):    results.append(left >  right)
            elif isinstance(op, ast.GtE):   results.append(left >= right)
            elif isinstance(op, ast.Eq):    results.append(left == right)
            elif isinstance(op, ast.NotEq): results.append(left != right)
            else: error.unsupported_comparator(ast.dump(op))
            left = right
        return all(results)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        op = node.op
        if isinstance(op, ast.UAdd): return +operand
        if isinstance(op, ast.USub): return -operand
        if isinstance(op, ast.Not):  return not operand
        error.unsupported_unary_operator(ast.dump(op))

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            for v in node.values:
                if not self.visit(v): return False
            return True
        if isinstance(node.op, ast.Or):
            for v in node.values:
                if self.visit(v): return True
            return False
        error.unsupported_boolean_operator(ast.dump(node.op))

    def visit_IfExp(self, node):
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    def visit_List(self, node): return [self.visit(el) for el in node.elts]
    def visit_Tuple(self, node): return tuple(self.visit(el) for el in node.elts)
    def visit_Dict(self, node):
        return {self.visit(k): self.visit(v) for k, v in zip(node.keys, node.values)}

    def visit_Subscript(self, node):
        obj = self.visit(node.value)
        idx = self.visit(node.slice)
        try: return obj[idx]
        except (IndexError, KeyError): return 'NIL'

    def visit_Name(self, node):
        if node.id == 'NIL': return 'NIL'
        if ghost_module.is_ghost(node.id):
            if ghost_module.is_expired(node.id):
                raise ValueError(f"Ghost variable '{node.id}' has expired")
            value = ghost_module.resolve_ghost(node.id)
            self.variables.pop(node.id, None)
            return value
        if lazy_module.is_lazy(node.id) and node.id not in lazy_module._lazy_evaluated:
            return lazy_module.resolve_lazy(node.id, self.variables, eval_expression)
        if node.id in self.variables: return self.variables[node.id]
        raise ValueError(f"Undefined variable '{node.id}'")

    def visit_Attribute(self, node):
        obj = self.visit(node.value)
        if isinstance(obj, oop_module.VynObject):
            return obj.get_attr(node.attr)
        if hasattr(obj, "get_attr"):           # ← Support for VynStructInstance
            return obj.get_attr(node.attr)
        try:
            return getattr(obj, node.attr)
        except AttributeError:
            return 'NIL'

    def visit_Constant(self, node):
        if isinstance(node.value, (str, int, float, bool)): return node.value
        error.unsupported_constant(node.value)

    def visit_Num(self, node): return node.n
    def visit_Str(self, node): return node.s

    

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'typeof':
            val = self.visit(node.args[0])
            mapping = {'list':'list','dict':'dict','tuple':'tuple',
                       'bool':'bool','int':'int','float':'float','str':'str',
                       'VynObject':'object','VynClass':'class'}
            return mapping.get(type(val).__name__, 'unknown')
        if isinstance(node.func, ast.Name) and node.func.id == 'not_in':
            return self.visit(node.args[0]) not in self.visit(node.args[1])
        if isinstance(node.func, ast.Name) and node.func.id == 'sizeof':
            val = self.visit(node.args[0])
            return mem_module.sizeof(val)
        if isinstance(node.func, ast.Name) and node.func.id == 'memsize':
            mid = self.visit(node.args[0])
            return mem_module.memsize(mid)
        func = self.visit(node.func)
        if func == 'NIL': return 'NIL'
        if not callable(func): error.not_a_function()
        return func(*[self.visit(a) for a in node.args])

    def generic_visit(self, node):
        error.unsupported_expression(ast.dump(node))


def eval_expression(expr, vars=None):
    expr = expr.strip()
    expr = replace_top_level(expr, '++', '+')

    m = LAMBDA_RE.match(expr)
    if m:
        params = [(p.strip(), None) for p in m.group('params').split(',') if p.strip()]
        if vars is None: vars = global_vars.variables
        return make_fn(params, [f'return {m.group("expr").strip()}'], vars)

    if has_pipe(expr):
        return resolve_pipe(expr, eval_expression, vars)

    def transform_ternary(s):
        s = s.strip()
        i, quote, depth = 0, None, 0
        while i < len(s):
            ch = s[i]
            if quote:
                if ch == quote: quote = None
                i += 1; continue
            if ch in ('"', "'"): quote = ch; i += 1; continue
            if ch == '(': depth += 1; i += 1; continue
            if ch == ')': depth -= 1; i += 1; continue
            if ch == '?' and depth == 0:
                qpos = i; j, q, d = i+1, None, 0
                while j < len(s):
                    cj = s[j]
                    if q:
                        if cj == q: q = None
                        j += 1; continue
                    if cj in ('"', "'"): q = cj; j += 1; continue
                    if cj == '(': d += 1; j += 1; continue
                    if cj == ')': d -= 1; j += 1; continue
                    if cj == ':' and d == 0:
                        cond = s[:qpos].strip()
                        true_part = s[qpos+1:j].strip()
                        false_part = s[j+1:].strip()
                        return transform_ternary(f"({true_part}) if ({cond}) else ({false_part})")
                    j += 1
                return s
            i += 1
        return s

    expr = transform_ternary(expr)
    # FIX: re already imported at module level, no need to import inside function
    expr = re.sub(r'\bnot\s+in\b', 'not_in', expr)

    # In eval_expression, after pipeline check:

    def replace_at(expr, variables):
        def replacer(m):
            name = m.group(1)
            idx = m.group(2)
            return f'__mem_read__({name}, {idx})'
        return AT_RE.sub(replacer, expr)

    if '@' in expr:
        expr = replace_at(expr, vars)
        if vars is None:
            vars = global_vars.variables
        vars['__mem_read__'] = mem_module.read_byte


    try:
        tree = _get_cached_ast(expr)
    except SyntaxError:
        error.invalid_expression(expr)

    if vars is None: vars = global_vars.variables
    return ExpressionEvaluator(vars).visit(tree)


def eval_print_expression(expr, vars=None):
    if vars is None: vars = global_vars.variables
    return ' '.join(str(eval_expression(a, vars))
                    for a in split_top_level(expr.strip(), ','))


# ---------------------------------------------------------------------------
# Function factory
# ---------------------------------------------------------------------------

def make_fn(params, body, outer_vars):
    def _fn(*call_args):
        local_vars = {}
        for i, (name, default) in enumerate(params):
            if i < len(call_args):
                local_vars[name] = call_args[i]
            elif default is not None:
                local_vars[name] = eval_expression(default, outer_vars)
            else:
                error.print_error_msg(f"Missing argument '{name}'")
                return None
        current_vars = local.make_function_scope(
            list(local_vars.keys()), list(local_vars.values()), outer_vars)
        _source.push(body, stop_at_end=True)
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
            _source.pop()
        return None
    return _fn


# ---------------------------------------------------------------------------
# execute_line
# ---------------------------------------------------------------------------

def execute_line(line, variables=None):
    if variables is None:
        variables = global_vars.variables

    stripped = line.strip()
    if not stripped: return

    if handle_augmented(stripped, variables, eval_expression): return

    if stripped == 'break':    return 'BREAK'
    if stripped == 'continue': return 'CONTINUE'

    if stripped.endswith('++'):
        name = stripped[:-2].strip()
        if lock_module.is_locked(name):
            error.print_error_msg(f"Cannot modify '{name}' — variable is locked"); return
        if name in variables: variables[name] += 1
        else: error.print_error_msg(f"Undefined variable '{name}'")
        return
    
    if stripped.endswith('--'):
        name = stripped[:-2].strip()
        if lock_module.is_locked(name):
            error.print_error_msg(f"Cannot modify '{name}' — variable is locked"); return
        if name in variables: variables[name] -= 1
        else: error.print_error_msg(f"Undefined variable '{name}'")
        return

    if stripped.startswith('return'):
        rest = stripped[6:].strip()  # after 'return'
        if not rest:
            return ('RETURN', None)
        # Split by commas at top level (respect parentheses, strings, etc.)
        parts = split_top_level(rest, ',')
        if len(parts) == 1:
            try:
                val = eval_expression(parts[0], variables)
                return ('RETURN', val)
            except ValueError as exc:
                error.print_error(exc)
                return
        else:
            # Multiple return values
            values = []
            for p in parts:
                try:
                    values.append(eval_expression(p, variables))
                except ValueError as exc:
                    error.print_error(exc)
                    return
            return ('RETURN', tuple(values))

    if stripped.startswith('throw '):
        try: val = eval_expression(stripped[6:].strip(), variables)
        except Exception: val = stripped[6:].strip()
        raise RuntimeError(str(val))

    if vyn_struct_syntax.try_attr_assign(stripped, variables, eval_expression):
        return

    if vyn_union_syntax.try_attr_assign(stripped, variables, eval_expression):
        return

    attribute_assignment = oop_module.parse_attribute_assignment(stripped)
    if attribute_assignment:
        object_name, field_name, expr = attribute_assignment
        try:
            obj = eval_expression(object_name, variables)
            if not isinstance(obj, oop_module.VynObject):
                error.print_error_msg(f"'{object_name}' is not an object")
                return
            obj.set_attr(field_name, eval_expression(expr, variables))
        except ValueError as exc:
            error.print_error(exc)
        return

    if stripped.startswith('assert '):
        rest = stripped[7:].strip()
        if ',' in rest:
            cond_expr, msg_expr = rest.split(',', 1)
            msg_expr = msg_expr.strip()
        else:
            cond_expr = rest
            msg_expr = f'"{rest}"'
        try:
            if not eval_expression(cond_expr.strip(), variables):
                raise AssertionError(str(eval_expression(msg_expr, variables)))
        except (AssertionError, RuntimeError): raise
        except ValueError as exc: error.print_error(exc)
        return

    if stripped.startswith('lazy '):
        rest = stripped[5:].strip()
        m = global_vars.ASSIGNMENT_RE.match(rest)
        if not m: error.print_error_msg("Invalid lazy syntax"); return
        lazy_module.register_lazy(m.group('name'), m.group('expr').strip())
        return

    if stripped == 'lazyList':
        names = lazy_module.list_lazy()
        if not names: print("No lazy variables")
        else:
            for n in names:
                status = "evaluated" if n in lazy_module._lazy_evaluated else "pending"
                print(f"  {n} -> {status}")
        return

    if stripped.startswith("forLoop"):
        body = read_block(readline=_read_line)
        return execute_for_loop(line, body, variables, eval_expression, execute_line)

    if stripped.startswith("whileLoop"):
        body = read_block(readline=_read_line)
        return execute_while_loop(line, body, variables, eval_expression, execute_line)

    if stripped.startswith("repeatUntil"):
        body = read_block(readline=_read_line)
        return execute_repeatuntil_loop(line, body, variables, eval_expression, execute_line)

    if stripped.startswith("forIn"):
        body = read_block(readline=_read_line)
        return execute_forin_loop(line, body, variables, eval_expression, execute_line)

        # === Struct / Union / Typedef wiring ===
    

    if is_try_header(stripped):
        try_body, catch_var, catch_body = read_try_catch(_read_line)
        return execute_try_catch(try_body, catch_var, catch_body, variables, execute_line)

    # mem x <- 16
    
    m = MEM_ALLOC_RE.match(stripped)
    if m:
        name = m.group('name')
        try:
            size = eval_expression(m.group('size').strip(), variables)
            variables[name] = mem_module.alloc(size)
        except Exception as exc:
            error.print_error(exc)
        return

    # release x
    if stripped.startswith('release '):
        name = stripped[8:].strip()
        if name not in variables:
            error.print_error_msg(f"Undefined variable '{name}'")
            return
        try:
            mem_module.free(variables[name])
            del variables[name]
        except Exception as exc:
            error.print_error(exc)
        return

    # memdump(x)
    if stripped.startswith('memdump(') and stripped.endswith(')'):
        name = stripped[8:-1].strip()
        if name not in variables:
            error.print_error_msg(f"Undefined variable '{name}'")
            return
        try:
            mem_module.memdump(variables[name])
        except Exception as exc:
            error.print_error(exc)
        return

    # memzero(x)
    if stripped.startswith('memzero(') and stripped.endswith(')'):
        name = stripped[8:-1].strip()
        if name not in variables:
            error.print_error_msg(f"Undefined variable '{name}'")
            return
        try:
            mem_module.memzero(variables[name])
        except Exception as exc:
            error.print_error(exc)
        return

    # memcopy(src, dest, size)
    if stripped.startswith('memcopy(') and stripped.endswith(')'):
        args_text = stripped[8:-1].strip()
        parts = split_top_level(args_text, ',') if args_text else []
        if len(parts) != 3:
            error.print_error_msg("memcopy expects: memcopy(src, dest, size)")
            return
        try:
            src = eval_expression(parts[0], variables)
            dest = eval_expression(parts[1], variables)
            size = eval_expression(parts[2], variables)
            mem_module.memcopy(src, dest, size)
        except Exception as exc:
            error.print_error(exc)
        return

    # memlist
    if stripped == 'memlist':
        print(mem_module.memlist())
        return

    # sizeof(x)
    if stripped.startswith('sizeof(') and stripped.endswith(')'):
        expr = stripped[7:-1].strip()
        try:
            val = eval_expression(expr, variables)
            result = mem_module.sizeof(val)
            if _source.at_top_level():
                print(result)
            else:
                variables['__sizeof__'] = result
        except Exception as exc:
            error.print_error(exc)
        return
    

    m = MEM_WRITE_RE.match(stripped)
    if m:
        name = m.group('name')
        if name in variables:
            try:
                idx = eval_expression(m.group('idx').strip(), variables)
                val = eval_expression(m.group('val').strip(), variables)
                mem_module.write_byte(variables[name], idx, val)
            except Exception as exc:
                error.print_error(exc)
        else:
            error.print_error_msg(f"Undefined variable '{name}'")
        return

    if SWITCH_RE.match(stripped):
        m = SWITCH_RE.match(stripped)
        expr_val = eval_expression(m.group('expr'), variables)
        cases, default_body = read_switch(_read_line)
        return execute_switch(expr_val, cases, default_body, variables, execute_line, eval_expression)

    if stripped.startswith("DOF(") and stripped.endswith(")"):
        try:
            fp = stripped[4:-1].strip()
            if (fp.startswith('"') and fp.endswith('"')) or \
               (fp.startswith("'") and fp.endswith("'")):
                fp = fp[1:-1]
            resolved = dependency.resolve_vyn_filename(fp)
            if not resolved or not dependency.exists(resolved):
                error.print_error_msg(f"File not found: {fp}"); return
            print(f"\n--- Executing {fp} ---")
            dependency.load_vyn_file(resolved, execute_line, variables)
            print(f"--- Finished {fp} ---\n")
        except Exception as exc: error.print_error(exc)
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
                error.print_error_msg(f"File not found: {imported}"); return
            dependency.load_vyn_file(resolved, execute_line, variables)
        return

    if stripped.startswith('react '):
        rest = stripped[6:].strip()
        m = global_vars.ASSIGNMENT_RE.match(rest)
        if not m: error.print_error_msg("Invalid react syntax"); return
        name = m.group('name')
        expr = m.group('expr').strip()
        global_vars.reactive[name] = expr
        # FIX: re already imported at top, no need to import inside execute_line
        deps = set(re.findall(r'\b[A-Za-z_]\w*\b', expr))
        deps -= {'and', 'or', 'not', 'true', 'false', 'NIL', name}
        for dep in deps:
            global_vars.dependencies.setdefault(dep, set()).add(name)
        try: variables[name] = eval_expression(expr, variables)
        except ValueError as exc: error.print_error(exc)
        return

    if stripped.startswith('watch '):
        rest = stripped[6:].strip()
        if not rest.endswith(' do'):
            error.print_error_msg("Invalid watch syntax, expected: watch x do"); return
        var_name = rest[:-3].strip()
        body = []
        while True:
            line = _read_line()
            if not line: continue
            if line.strip() == 'endWatch': break
            body.append(line)
        global_vars.watchers.setdefault(var_name, []).append(body)
        return

    if stripped.startswith('proof '):
        rest = stripped[6:].strip()
        if rest.endswith(' do'): rest = rest[:-3].strip()
        if (rest.startswith('"') and rest.endswith('"')) or \
           (rest.startswith("'") and rest.endswith("'")):
            proof_name = rest[1:-1]
        else:
            proof_name = rest
        body = []
        while True:
            line = _read_line()
            if not line: continue
            if line.strip() == 'endProof': break
            body.append(line)
        passed, failed, errors = 0, 0, []
        # FIX: use _run_body so nested loops/IFs inside proof work correctly
        for bl in body:
            s = bl.strip()
            if not s or s.startswith('#'): continue
            try:
                _run_body([bl], variables)
                passed += 1
            except AssertionError as exc:
                failed += 1; errors.append(str(exc))
            except Exception as exc:
                failed += 1; errors.append(str(exc))
        global_vars.proof_results.append(
            {'name': proof_name, 'passed': passed, 'failed': failed, 'errors': errors})
        total = passed + failed
        status = 'PASSED' if failed == 0 else 'FAILED'
        print(f"[PROOF] {proof_name} — {status} ({passed}/{total})")
        for err in errors: print(f"  ✗ {err}")
        return

    if stripped in ('proofReport', 'proof_report'):
        if not global_vars.proof_results: print("No proofs run"); return
        total_p = sum(p['passed'] for p in global_vars.proof_results)
        total_f = sum(p['failed'] for p in global_vars.proof_results)
        print("=== Proof Report ===")
        for p in global_vars.proof_results:
            status = 'PASSED' if p['failed'] == 0 else 'FAILED'
            print(f"  [{status}] {p['name']} ({p['passed']}/{p['passed']+p['failed']})")
            for err in p['errors']: print(f"    ✗ {err}")
        print(f"  Total: {total_p}/{total_p+total_f} passed")
        return

    if stripped.startswith("IF"):
        blocks = _read_conditional_block(line)
        return execute_conditional(blocks, variables, eval_expression, execute_line, condition_truth)

    if stripped.startswith("Class"):
        parsed = oop_module.parse_class_header(stripped)
        if not parsed:
            error.print_error_msg("Invalid class syntax")
            return
        class_name, params = parsed
        body = read_class_body()
        variables[class_name] = oop_module.make_class(
            class_name, params, body, variables, eval_expression, _run_body)
        return

    if stripped.lower().startswith('function'):
        parsed = parse_function_header(stripped)
        if not parsed: error.print_error_msg("Invalid function header"); return
        fname, params = parsed
        body = read_function_body()
        if not fname:
            error.print_error_msg("unnamed standalone function must be assigned to a variable"); return
        variables[fname] = make_fn(params, body, variables)
        return

    if handle_const(stripped, variables, eval_expression, parse_in_call): return

    if stripped.startswith('lock ') and stripped.endswith(' do'):
        rest = stripped[5:-3].strip()
        names = [n.strip() for n in rest.split(',') if n.strip()]
        body = []
        while True:
            line = _read_line()
            if not line: continue
            if line.strip() == 'endLock': break
            body.append(line)
        for name in names: lock_module.lock(name)
        try:
            # FIX: use _run_body so nested loops/IFs inside lock work correctly
            _run_body(body, variables)
        finally:
            # FIX: unlock all vars AFTER loop completes, not inside it
            for name in names:
                lock_module.unlock(name)
        return

    if stripped.startswith('lockGroup '):
        rest = stripped[10:].strip()
        parts = rest.split(None, 1)
        if len(parts) < 2: error.print_error_msg("Invalid lockGroup syntax"); return
        names = [n.strip() for n in parts[1].split(',') if n.strip()]
        lock_module.lock_group(parts[0], names)
        return

    if stripped.startswith('unlockGroup '):
        lock_module.unlock_group(stripped[12:].strip())
        return

    if stripped == 'lockList':
        locked = lock_module.list_locked()
        if not locked: print("No locked variables")
        else:
            for name in locked: print(f"  locked: {name}")
        return

    if stripped == 'unlockAll':
        lock_module.clear_all()
        return

    # FIX: timed block handler restored using time.py via timed_module
    if (stripped == 'timed do' or (stripped.startswith('timed ') and stripped.endswith(' do'))) \
            and not stripped.startswith('timedReport'):
        rest = stripped[5:].strip()
        label = None
        if rest != 'do':
            label = rest[:-3].strip()
            if (label.startswith('"') and label.endswith('"')) or \
               (label.startswith("'") and label.endswith("'")):
                label = label[1:-1]
        body = []
        while True:
            line = _read_line()
            if not line: continue
            if line.strip() == 'endTimed': break
            body.append(line)
        start = timed_module.start_timer()
        try:
            # FIX: use _run_body so nested loops/IFs inside timed work correctly
            _run_body(body, variables)
        finally:
            elapsed = timed_module.stop_timer(start)
            if label:
                timed_module.store_result(label, elapsed)
                print(f"[TIMED] {label} — {elapsed}")
            else:
                print(f"[TIMED] {elapsed}")
        return

    if stripped == 'timedReport':
        results = timed_module.list_results()
        if not results: print("No timed results"); return
        print("=== Timed Report ===")
        for label, elapsed in results.items(): print(f"  {label} — {elapsed}")
        return

    if stripped == 'timedClear':
        timed_module.clear_results()
        return

    if stripped.startswith('ghost '):
        rest = stripped[6:].strip()
        m = global_vars.ASSIGNMENT_RE.match(rest)
        if not m: error.print_error_msg("Invalid ghost syntax"); return
        name = m.group('name')
        try:
            value = eval_expression(m.group('expr').strip(), variables)
            ghost_module.register_ghost(name, value)
            variables[name] = value
        except ValueError as exc: error.print_error(exc)
        return

    if stripped == 'ghostList':
        ghosts = ghost_module.list_ghosts()
        if not ghosts: print("No ghost variables")
        else:
            for name, status in ghosts.items(): print(f"  {name} -> {status}")
        return

    if stripped.startswith('snapshot '):
        snap_name = stripped[9:].strip()
        global_vars.snapshots[snap_name] = {
            k: copy.deepcopy(v)
            for k, v in variables.items()
            if not callable(v) and not k.startswith('__')
        }
        return

    if stripped.startswith('rollback '):
        snap_name = stripped[9:].strip()
        if snap_name not in global_vars.snapshots:
            error.print_error_msg(f"Snapshot '{snap_name}' not found"); return
        snap = global_vars.snapshots[snap_name]
        for k, v in snap.items(): variables[k] = v
        for k in [k for k in list(variables.keys())
                  if k not in snap and not callable(variables[k]) and not k.startswith('__')]:
            del variables[k]
        return

    if stripped == 'snapshots':
        if not global_vars.snapshots: print("No snapshots")
        else:
            for name in global_vars.snapshots: print(name)
        return

    if stripped.startswith('dropsnap '):
        snap_name = stripped[9:].strip()
        if snap_name in global_vars.snapshots: del global_vars.snapshots[snap_name]
        else: error.print_error_msg(f"Snapshot '{snap_name}' not found")
        return


    if vyn_union_syntax.parse_union_header(stripped):
        vyn_union_syntax.handle_union_header(
            stripped,
            _read_line,
            eval_expression=eval_expression,
            run_body=_run_body,
            outer_vars=variables,
        )
        return

    if vyn_struct_syntax.parse_struct_header(stripped):
        vyn_struct_syntax.handle_struct_header(
            stripped,
            _read_line,
            eval_expression=eval_expression,
            run_body=_run_body,
            outer_vars=variables,
        )
        return

    if vyn_struct_syntax.handle_typedef(stripped):
        return

    if vyn_union_syntax.handle_typedef(stripped):
        return

    if vyn_struct_syntax.try_new_instance(stripped, variables):
        return

    if vyn_union_syntax.try_new_instance(stripped, variables):
        return

    if vyn_struct_syntax.try_attr_assign(stripped, variables, eval_expression):
        return

    if vyn_union_syntax.try_attr_assign(stripped, variables, eval_expression):
        return

    multi = global_vars.MULTI_ASSIGN_RE.match(stripped)
    if multi:
        names_str, expr = multi.group(1), multi.group(2).strip()
        names = [n.strip() for n in names_str.split(',')]
        # Evaluate RHS
        try:
            result = eval_expression(expr, variables)
        except ValueError as exc:
            error.print_error(exc)
            return
        # If result is not a tuple with enough elements, error
        if not isinstance(result, tuple) or len(result) != len(names):
            error.print_error_msg(f"Expected {len(names)} values, got {type(result).__name__}")
            return
        for name, val in zip(names, result):
            # Respect locks and constants (call assign_variable or do manually)
            assign_variable(name, str(val), variables, eval_expression, parse_in_call, execute_line)
        return

    assignment = global_vars.ASSIGNMENT_RE.match(stripped)
    if assignment:
        name = assignment.group("name")
        expr = assignment.group("expr").strip()
        assign_variable(name, expr, variables, eval_expression, parse_in_call, execute_line)
        return

    function_call = parse_function_call(stripped)
    if function_call:
        fname, args_text = function_call
        if fname in variables and callable(variables[fname]):
            parts = split_top_level(args_text, ',') if args_text.strip() else []
            evaluated = []
            try:
                for p in parts: evaluated.append(eval_expression(p, variables))
            except ValueError as exc: error.print_error(exc); return
            try:
                result = variables[fname](*evaluated)
                if result is not None and _source.at_top_level(): print(result)
            except Exception as exc: error.print_function_call_error(exc)
            return

    if re.match(r'^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\s*\(.*\)\s*$', stripped):
        try:
            result = eval_expression(stripped, variables)
            if result is not None and _source.at_top_level():
                print(result)
        except ValueError as exc:
            error.print_error(exc)
        return

    if stripped.startswith("typeof(") and stripped.endswith(")"):
        try:
            val = eval_expression(stripped[7:-1].strip(), variables)
            mapping = {'list':'list','dict':'dict','tuple':'tuple',
                       'bool':'bool','int':'int','float':'float','str':'str',
                       'VynObject':'object','VynClass':'class'}
            t = mapping.get(type(val).__name__, 'unknown')
            if _source.at_top_level(): print(t)
            else: variables['__typeof__'] = t
        except ValueError as exc: error.print_error(exc)
        return

    if stripped.startswith("print"):
        content = stripped[len("print"):].strip()
        if content.startswith("(") and content.endswith(")"):
            content = content[1:-1].strip()
        if content.startswith('f"') or content.startswith("f'"):
            print(interpolate(content[2:-1], variables, eval_expression))
            return
        try: print(eval_print_expression(content, variables))
        except ValueError as exc: error.print_error(exc)
        return

    if stripped.startswith("IN"):
        try: parse_in_call(stripped)
        except ValueError as exc: error.print_error(exc)
        return

    print(line)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

def start():
    while True:
        try:
            line = _read_line()
            if not line: break
            execute_line(line, global_vars.variables)
        except EOFError:
            break
