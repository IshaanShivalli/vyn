import ast
import re
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
from pipeExpr import has_pipe, resolve_pipe
dependency.register_io_functions(global_vars.variables)

# FIX: LAMBDA_RE at module level, not recompiled on every eval_expression call
LAMBDA_RE = re.compile(r'^lambda\s+(?P<params>[\w,\s]*)\s*:\s*(?P<expr>.+)$')

# ---------------------------------------------------------------------------
# Line source
# ---------------------------------------------------------------------------

class _LineSource:
    def __init__(self):
        self._stack = []

    def push(self, lines):
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
            if ch == quote:
                quote = None
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


# ---------------------------------------------------------------------------
# Block readers
# ---------------------------------------------------------------------------

def _read_block():
    # FIX: always use _read_line, never raw input()
    return read_block(readline=_read_line)


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
    # FIX: pass _read_line directly instead of patching builtins.input
    # Patching caused infinite recursion because _read_line calls input()
    # when the stack is empty, and patching input = _read_line made it recursive
    return read_conditional_block(first_header, readline=_read_line)


# ---------------------------------------------------------------------------
# Expression evaluator
# ---------------------------------------------------------------------------

class ExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, variables_map):
        self.variables = variables_map

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
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

    def visit_List(self, node):
        return [self.visit(el) for el in node.elts]

    def visit_Tuple(self, node):
        return tuple(self.visit(el) for el in node.elts)

    def visit_Dict(self, node):
        return {self.visit(k): self.visit(v) for k, v in zip(node.keys, node.values)}

    def visit_Subscript(self, node):
        obj = self.visit(node.value)
        idx = self.visit(node.slice)
        try:
            return obj[idx]
        except (IndexError, KeyError):
            return 'NIL'

    def visit_Name(self, node):
        if node.id == 'NIL': return 'NIL'

        # Ghost variable check
        if ghost_module.is_ghost(node.id):
            if ghost_module.is_expired(node.id):
                raise ValueError(f"Ghost variable '{node.id}' has expired")
            value = ghost_module.resolve_ghost(node.id)
            # Remove from variables after access
            self.variables.pop(node.id, None)
            return value

        # Lazy variable check
        if lazy_module.is_lazy(node.id) and node.id not in lazy_module._lazy_evaluated:
            return lazy_module.resolve_lazy(node.id, self.variables, eval_expression)

        if node.id in self.variables: return self.variables[node.id]
        raise ValueError(f"Undefined variable '{node.id}'")

    def visit_Constant(self, node):
        if isinstance(node.value, (str, int, float, bool)): return node.value
        error.unsupported_constant(node.value)

    def visit_Num(self, node): return node.n
    def visit_Str(self, node): return node.s

    # FIX: single visit_Call that handles typeof, not_in, and general calls
    # Previously two visit_Call methods were defined — Python silently drops
    # the first one, so not_in and typeof handling never ran
    def visit_Call(self, node):
        # typeof handled before function lookup
        if isinstance(node.func, ast.Name) and node.func.id == 'typeof':
            val = self.visit(node.args[0])
            mapping = {'list': 'list', 'dict': 'dict', 'tuple': 'tuple',
                       'bool': 'bool', 'int': 'int', 'float': 'float', 'str': 'str'}
            return mapping.get(type(val).__name__, 'unknown')

        # not_in handled before function lookup
        if isinstance(node.func, ast.Name) and node.func.id == 'not_in':
            item = self.visit(node.args[0])
            container = self.visit(node.args[1])
            return item not in container

        func = self.visit(node.func)
        if func == 'NIL': return 'NIL'
        if not callable(func): error.not_a_function()
        return func(*[self.visit(a) for a in node.args])

    def generic_visit(self, node):
        error.unsupported_expression(ast.dump(node))


def eval_expression(expr, vars=None):
    expr = expr.strip()
    expr = replace_top_level(expr, '++', '+')

    # FIX: try_parse_lambda is now actually called
    m = LAMBDA_RE.match(expr)
    if m:
        params_raw = [p.strip() for p in m.group('params').split(',') if p.strip()]
        params = [(p, None) for p in params_raw]
        body_line = f'return {m.group("expr").strip()}'
        if vars is None:
            vars = global_vars.variables
        return make_fn(params, [body_line], vars)

    # Pipeline operator
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
                qpos = i; j, q, d = i + 1, None, 0
                while j < len(s):
                    cj = s[j]
                    if q:
                        if cj == q: q = None
                        j += 1; continue
                    if cj in ('"', "'"): q = cj; j += 1; continue
                    if cj == '(': d += 1; j += 1; continue
                    if cj == ')': d -= 1; j += 1; continue
                    if cj == ':' and d == 0:
                        cond      = s[:qpos].strip()
                        true_part = s[qpos+1:j].strip()
                        false_part = s[j+1:].strip()
                        return transform_ternary(f"({true_part}) if ({cond}) else ({false_part})")
                    j += 1
                return s
            i += 1
        return s

    expr = transform_ternary(expr)
    expr = re.sub(r'\bnot\s+in\b', 'not_in', expr)

    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError:
        error.invalid_expression(expr)

    if vars is None:
        vars = global_vars.variables
    return ExpressionEvaluator(vars).visit(tree)


def eval_print_expression(expr, vars=None):
    if vars is None:
        vars = global_vars.variables
    return ' '.join(str(eval_expression(a, vars))
                    for a in split_top_level(expr.strip(), ','))


# ---------------------------------------------------------------------------
# Function factory
# ---------------------------------------------------------------------------

def make_fn(params, body, outer_vars):
    """
    params: list of (name, default_expr_or_None)
    body:   list of line strings
    """
    def _fn(*call_args):
        local_vars = {}
        for i, (name, default) in enumerate(params):
            if i < len(call_args):
                local_vars[name] = call_args[i]
            elif default is not None:
                # FIX: eval default against outer scope
                local_vars[name] = eval_expression(default, outer_vars)
            else:
                error.print_error_msg(f"Missing argument '{name}'")
                return None
        # FIX: use make_function_scope (which exists) not make_function_scope_from_dict
        current_vars = local.make_function_scope(list(local_vars.keys()),
                                                  list(local_vars.values()),
                                                  outer_vars)
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
    if not stripped:
        return

    # Augmented assignment: +=, -=, *=, /=
    if handle_augmented(stripped, variables, eval_expression):
        return

    if stripped == 'break':    return 'BREAK'
    if stripped == 'continue': return 'CONTINUE'

    # ++/--
    if stripped.endswith('++'):
        name = stripped[:-2].strip()
        if lock_module.is_locked(name):
            error.print_error_msg(f"Cannot modify '{name}' — variable is locked")
            return
        if name in variables:
            variables[name] = variables[name] + 1
        else:
            error.print_error_msg(f"Undefined variable '{name}'")
        return

    if stripped.endswith('--'):
        name = stripped[:-2].strip()
        if lock_module.is_locked(name):
            error.print_error_msg(f"Cannot modify '{name}' — variable is locked")
            return
        if name in variables:
            variables[name] = variables[name] - 1
        else:
            error.print_error_msg(f"Undefined variable '{name}'")
        return

    if stripped.startswith('return'):
        parts = stripped.split(None, 1)
        if len(parts) == 1:
            return ('RETURN', None)
        try:
            return ('RETURN', eval_expression(parts[1], variables))
        except ValueError as exc:
            error.print_error(exc)
            return

    if stripped.startswith('throw '):
        try:
            val = eval_expression(stripped[6:].strip(), variables)
        except Exception:
            val = stripped[6:].strip()
        raise RuntimeError(str(val))

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
        except (AssertionError, RuntimeError):
            raise
        except ValueError as exc:
            error.print_error(exc)
        return
    

    if stripped.startswith('lazy '):
        rest = stripped[5:].strip()
        m = global_vars.ASSIGNMENT_RE.match(rest)
        if not m:
            error.print_error_msg("Invalid lazy syntax")
            return
        name = m.group('name')
        expr = m.group('expr').strip()
        # Just register — do NOT evaluate yet
        lazy_module.register_lazy(name, expr)
        return

    if stripped.startswith("forLoop"):
        # FIX: pass _read_line so block reader uses _source not raw input()
        body = read_block(readline=_read_line)
        execute_for_loop(line, body, variables, eval_expression, execute_line)
        return

    if stripped.startswith("whileLoop"):
        # FIX: same
        body = read_block(readline=_read_line)
        execute_while_loop(line, body, variables, eval_expression, execute_line)
        return
    
    if stripped.startswith("repeatUntil"):
        body = read_block(readline=_read_line)
        execute_repeatuntil_loop(line, body, variables, eval_expression, execute_line)
        return

    if stripped.startswith("forIn"):
        body = read_block(readline=_read_line)
        execute_forin_loop(line, body, variables, eval_expression, execute_line)
        return



    if is_try_header(stripped):
        try_body, catch_var, catch_body = read_try_catch(_read_line)
        execute_try_catch(try_body, catch_var, catch_body, variables, execute_line)
        return

    if SWITCH_RE.match(stripped):
        m = SWITCH_RE.match(stripped)
        expr_val = eval_expression(m.group('expr'), variables)
        cases, default_body = read_switch(_read_line)
        execute_switch(expr_val, cases, default_body, variables, execute_line, eval_expression)
        return

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
                error.print_error_msg(f"File not found: {imported}"); return
            dependency.load_vyn_file(resolved, execute_line, variables)
        return

    if stripped.startswith('react '):
        rest = stripped[6:].strip()
        m = global_vars.ASSIGNMENT_RE.match(rest)
        if not m:
            error.print_error_msg("Invalid react syntax")
            return
        name = m.group('name')
        expr = m.group('expr').strip()

        # Store the expression
        global_vars.reactive[name] = expr

        # Parse dependencies — any identifier in the expression
        import re
        deps = set(re.findall(r'\b[A-Za-z_]\w*\b', expr))
        # Remove keywords and the name itself
        skip = {'and', 'or', 'not', 'true', 'false', 'NIL', name}
        deps -= skip

        # Register this reactive var under each dependency
        for dep in deps:
            if dep not in global_vars.dependencies:
                global_vars.dependencies[dep] = set()
            global_vars.dependencies[dep].add(name)

        # Evaluate immediately for initial value
        try:
            variables[name] = eval_expression(expr, variables)
        except ValueError as exc:
            error.print_error(exc)
        return

    if stripped.startswith('proof '):
        rest = stripped[6:].strip()
        # strip quotes and 'do' from end
        if rest.endswith(' do'):
            rest = rest[:-3].strip()
        if (rest.startswith('"') and rest.endswith('"')) or \
        (rest.startswith("'") and rest.endswith("'")):
            proof_name = rest[1:-1]
        else:
            proof_name = rest

        # Read body until endProof
        body = []
        while True:
            line = _read_line()
            if not line:
                continue
            if line.strip() == 'endProof':
                break
            body.append(line)

        # Execute body tracking passes and failures
        passed = 0
        failed = 0
        errors = []

        for bl in body:
            s = bl.strip()
            if not s or s.startswith('#'):
                continue
            try:
                res = execute_line(bl, variables)
                passed += 1
            except AssertionError as exc:
                failed += 1
                errors.append(str(exc))
            except Exception as exc:
                failed += 1
                errors.append(str(exc))

        # Store result
        global_vars.proof_results.append({
            'name': proof_name,
            'passed': passed,
            'failed': failed,
            'errors': errors
        })

        # Print result
        total = passed + failed
        status = 'PASSED' if failed == 0 else 'FAILED'
        print(f"[PROOF] {proof_name} — {status} ({passed}/{total})")
        for err in errors:
            print(f"  ✗ {err}")
        return

    if stripped == 'proofReport' or stripped == 'proof_report':
        if not global_vars.proof_results:
            print("No proofs run")
            return
        total_passed = sum(p['passed'] for p in global_vars.proof_results)
        total_failed = sum(p['failed'] for p in global_vars.proof_results)
        total = total_passed + total_failed
        print(f"=== Proof Report ===")
        for p in global_vars.proof_results:
            status = 'PASSED' if p['failed'] == 0 else 'FAILED'
            print(f"  [{status}] {p['name']} ({p['passed']}/{p['passed']+p['failed']})")
            for err in p['errors']:
                print(f"    ✗ {err}")
        print(f"  Total: {total_passed}/{total} passed")
        return

    if stripped == 'lazyList':
        names = lazy_module.list_lazy()
        if not names:
            print("No lazy variables")
        else:
            for n in names:
                status = "evaluated" if n in lazy_module._lazy_evaluated else "pending"
                print(f"  {n} -> {status}")
        return
    
    
    if stripped.startswith('watch '):
        rest = stripped[6:].strip()
        # strip 'do' from end
        if rest.endswith(' do'):
            var_name = rest[:-3].strip()
        else:
            error.print_error_msg("Invalid watch syntax, expected: watch x do")
            return

        # Read body until endWatch
        body = []
        while True:
            line = _read_line()
            if not line:
                continue
            if line.strip() == 'endWatch':
                break
            body.append(line)

        # Register the watcher
        if var_name not in global_vars.watchers:
            global_vars.watchers[var_name] = []
        global_vars.watchers[var_name].append(body)
        return

    if stripped.startswith("IF"):
        # FIX: use _read_conditional_block which passes _read_line directly
        # Old _patched version set builtins.input=_read_line which caused
        # infinite recursion since _read_line itself calls input()
        blocks = _read_conditional_block(line)
        execute_conditional(blocks, variables, eval_expression, execute_line, condition_truth)
        return

    if stripped.lower().startswith('function'):
        parsed = parse_function_header(stripped)
        if not parsed:
            error.print_error_msg("Invalid function header"); return
        fname, params = parsed
        body = read_function_body()
        if not fname:
            error.print_error_msg("unnamed standalone function must be assigned to a variable"); return
        variables[fname] = make_fn(params, body, variables)
        return

    # const before assignment so 'const x = 5' isn't caught by ASSIGNMENT_RE
    if handle_const(stripped, variables, eval_expression, parse_in_call):
        return

    if stripped.startswith('lock ') and stripped.endswith(' do'):
        # Extract variable names between 'lock' and 'do'
        # Supports: lock x do  OR  lock x, y, z do
        rest = stripped[5:-3].strip()
        names = [n.strip() for n in rest.split(',') if n.strip()]

        # Lock all variables
        for name in names:
            lock_module.lock(name)

        # Read body until endLock
        body = []
        while True:
            line = _read_line()
            if not line:
                continue
            if line.strip() == 'endLock':
                break
            body.append(line)

        # Execute body with locks active
        try:
            for bl in body:
                res = execute_line(bl, variables)
                if isinstance(res, tuple) and res[0] == 'RETURN':
                    return res
                if res in ('BREAK', 'CONTINUE'):
                    return res
        finally:
            # Always unlock after block exits
            for name in names:
                lock_module.unlock(name)
                return

        if stripped.startswith('lockGroup '):
            # lockGroup myGroup x, y, z
            rest = stripped[10:].strip()
            parts = rest.split(None, 1)
            if len(parts) < 2:
                error.print_error_msg("Invalid lockGroup syntax")
                return
            group_name = parts[0]
            names = [n.strip() for n in parts[1].split(',') if n.strip()]
            lock_module.lock_group(group_name, names)
            return

        if stripped.startswith('unlockGroup '):
            group_name = stripped[12:].strip()
            lock_module.unlock_group(group_name)
            return

        if stripped == 'lockList':
            locked = lock_module.list_locked()
            if not locked:
                print("No locked variables")
            else:
                for name in locked:
                    print(f"  locked: {name}")
            return

        if stripped == 'unlockAll':
            lock_module.clear_all()
            return

    if stripped.startswith('ghost '):
        rest = stripped[6:].strip()
        m = global_vars.ASSIGNMENT_RE.match(rest)
        if not m:
            error.print_error_msg("Invalid ghost syntax")
            return
        name = m.group('name')
        expr = m.group('expr').strip()
        try:
            value = eval_expression(expr, variables)
            ghost_module.register_ghost(name, value)
            # Store in variables so expressions can find it
            variables[name] = value
        except ValueError as exc:
            error.print_error(exc)
        return

    if stripped == 'ghostList':
        ghosts = ghost_module.list_ghosts()
        if not ghosts:
            print("No ghost variables")
        else:
            for name, status in ghosts.items():
                print(f"  {name} -> {status}")
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
                for p in parts:
                    evaluated.append(eval_expression(p, variables))
            except ValueError as exc:
                error.print_error(exc); return
            try:
                result = variables[fname](*evaluated)
                if result is not None and _source.at_top_level():
                    print(result)
            except Exception as exc:
                error.print_function_call_error(exc)
            return

    if stripped.startswith("typeof(") and stripped.endswith(")"):
        try:
            val = eval_expression(stripped[7:-1].strip(), variables)
            mapping = {'list': 'list', 'dict': 'dict', 'tuple': 'tuple',
                       'bool': 'bool', 'int': 'int', 'float': 'float', 'str': 'str'}
            t = mapping.get(type(val).__name__, 'unknown')
            if _source.at_top_level():
                print(t)
            else:
                variables['__typeof__'] = t
        except ValueError as exc:
            error.print_error(exc)
        return
    
    if stripped.startswith('snapshot '):
        snap_name = stripped[9:].strip()
        # Deep copy current variables excluding callables and private keys
        import copy
        global_vars.snapshots[snap_name] = {
            k: copy.deepcopy(v)
            for k, v in variables.items()
            if not callable(v) and not k.startswith('__')
        }
        return

    if stripped.startswith('rollback '):
        snap_name = stripped[9:].strip()
        if snap_name not in global_vars.snapshots:
            error.print_error_msg(f"Snapshot '{snap_name}' not found")
            return
        # Restore all snapshotted values
        snap = global_vars.snapshots[snap_name]
        for k, v in snap.items():
            variables[k] = v
        # Remove any variables that didn't exist at snapshot time
        to_delete = [
            k for k in list(variables.keys())
            if k not in snap
            and not callable(variables[k])
            and not k.startswith('__')
        ]
        for k in to_delete:
            del variables[k]
        return

    if stripped == 'snapshots':
        if not global_vars.snapshots:
            print("No snapshots")
        else:
            for name in global_vars.snapshots:
                print(name)
        return

    if stripped.startswith('dropsnap '):
        snap_name = stripped[9:].strip()
        if snap_name in global_vars.snapshots:
            del global_vars.snapshots[snap_name]
        else:
            error.print_error_msg(f"Snapshot '{snap_name}' not found")
        return

    if stripped.startswith("print"):
        content = stripped[len("print"):].strip()
        if content.startswith("(") and content.endswith(")"):
            content = content[1:-1].strip()
        if content.startswith('f"') or content.startswith("f'"):
            inner = content[2:-1]
            print(interpolate(inner, variables, eval_expression))
            return
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
# REPL
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