import re
import json
import error
import go_interpreter

go_interpreter.load_all()

DEFER_RE = re.compile(r'^defer\s+(?P<expr>.+)$')
MULTIRET_ASSIGN_RE = re.compile(r'^(?P<names>[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)+)\s*=\s*(?P<expr>.+)$')
GO_RE = re.compile(r'^go\s+(?P<expr>.+)$')
CHAN_NEW_RE = re.compile(r'^(?P<name>[A-Za-z_]\w*)\s*=\s*makeChan\s*\(\s*(?P<buf>\d+)\s*\)$')
CHAN_SEND_RE = re.compile(r'^(?P<chan>[A-Za-z_]\w*)\s*<-\s*(?P<expr>.+)$')
CHAN_RECV_RE = re.compile(r'^(?P<var>[A-Za-z_]\w*)\s*=\s*<-(?P<chan>[A-Za-z_]\w*)$')
CHAN_CLOSE_RE = re.compile(r'^closeChan\s*\(\s*(?P<chan>[A-Za-z_]\w*)\s*\)$')
SELECT_RE = re.compile(r'^select\s+do$')

_defer_stacks = {}
_goroutine_id_map = {}
_goroutine_next_id = [0]


def _push_defer_stack(fn_id, scope_id):
    go_interpreter.call('vyn_defer_new_stack') if scope_id not in _defer_stacks else None
    if scope_id not in _defer_stacks:
        _defer_stacks[scope_id] = go_interpreter.call('vyn_defer_new_stack')
    stack_id = _defer_stacks[scope_id]
    go_interpreter.call('vyn_defer_push', stack_id, fn_id)


def flush_defers(scope_id, variables, execute_line):
    if scope_id not in _defer_stacks:
        return
    stack_id = _defer_stacks[scope_id]
    go_interpreter.call('vyn_defer_run', stack_id)
    while True:
        fn_id = go_interpreter.call('vyn_defer_pop_call')
        if fn_id == -1:
            break
        fn = _goroutine_id_map.get(fn_id)
        if fn and callable(fn):
            try:
                fn()
            except Exception as exc:
                error.print_error(exc)
    go_interpreter.call('vyn_defer_drop_stack', stack_id)
    del _defer_stacks[scope_id]


def _register_callable(fn):
    _goroutine_next_id[0] += 1
    fid = _goroutine_next_id[0]
    _goroutine_id_map[fid] = fn
    return fid


def handle_defer(line, variables, eval_expression, execute_line, scope_id):
    m = DEFER_RE.match(line.strip())
    if not m:
        return False
    expr = m.group('expr').strip()
    if scope_id not in _defer_stacks:
        _defer_stacks[scope_id] = go_interpreter.call('vyn_defer_new_stack')
    stack_id = _defer_stacks[scope_id]
    captured = dict(variables)
    def deferred():
        execute_line(expr, captured)
    fid = _register_callable(deferred)
    go_interpreter.call('vyn_defer_push', stack_id, fid)
    return True


def handle_multi_assign(line, variables, eval_expression):
    m = MULTIRET_ASSIGN_RE.match(line.strip())
    if not m:
        return False
    names = [n.strip() for n in m.group('names').split(',')]
    expr = m.group('expr').strip()
    try:
        result = eval_expression(expr, variables)
    except ValueError as exc:
        error.print_error(exc)
        return True
    if isinstance(result, int) and go_interpreter.is_loaded('vyn_ret_get_json'):
        values = go_interpreter.call('vyn_ret_unpack', result)
    elif isinstance(result, (list, tuple)):
        values = list(result)
    else:
        values = [result]
    for i, name in enumerate(names):
        variables[name] = values[i] if i < len(values) else 'NIL'
    return True


def handle_go_spawn(line, variables, eval_expression):
    m = GO_RE.match(line.strip())
    if not m:
        return False
    expr = m.group('expr').strip()
    captured = dict(variables)
    def _task():
        try:
            return eval_expression(expr, captured)
        except Exception as exc:
            error.print_error(exc)
    go_interpreter.call('vyn_goroutine_spawn', _task, [])
    return True


def handle_chan_new(line, variables):
    m = CHAN_NEW_RE.match(line.strip())
    if not m:
        return False
    name = m.group('name')
    buf = int(m.group('buf'))
    cid = go_interpreter.call('vyn_chan_new', buf)
    variables[name] = cid
    return True


def handle_chan_send(line, variables, eval_expression):
    m = CHAN_SEND_RE.match(line.strip())
    if not m:
        return False
    chan_name = m.group('chan')
    expr = m.group('expr').strip()
    if chan_name not in variables:
        return False
    cid = variables[chan_name]
    if not isinstance(cid, int):
        return False
    try:
        val = eval_expression(expr, variables)
    except ValueError as exc:
        error.print_error(exc)
        return True
    if isinstance(val, bool):
        go_interpreter.call('vyn_chan_send_int', cid, int(val))
    elif isinstance(val, int):
        go_interpreter.call('vyn_chan_send_int', cid, val)
    elif isinstance(val, float):
        go_interpreter.call('vyn_chan_send_float', cid, val)
    elif isinstance(val, str):
        go_interpreter.call('vyn_chan_send_str', cid, val)
    else:
        error.print_error_msg(f"Cannot send type '{type(val).__name__}' on channel")
    return True


def handle_chan_recv(line, variables):
    m = CHAN_RECV_RE.match(line.strip())
    if not m:
        return False
    var_name = m.group('var')
    chan_name = m.group('chan')
    if chan_name not in variables:
        return False
    cid = variables[chan_name]
    if not isinstance(cid, int):
        return False
    val, status = go_interpreter.call('vyn_chan_recv', cid, timeout=5)
    if status != 0:
        variables[var_name] = 'NIL'
    else:
        variables[var_name] = val
    return True


def handle_chan_close(line, variables):
    m = CHAN_CLOSE_RE.match(line.strip())
    if not m:
        return False
    chan_name = m.group('chan')
    if chan_name not in variables:
        error.print_error_msg(f"Undefined channel '{chan_name}'")
        return True
    go_interpreter.call('vyn_chan_close', variables[chan_name])
    return True


def handle_select(line, variables, readline, execute_line):
    if not SELECT_RE.match(line.strip()):
        return False
    cases = []
    default_body = None
    while True:
        l = readline()
        if not l:
            continue
        s = l.strip()
        if s == 'endSelect':
            break
        m = re.match(r'^case\s+<-(?P<chan>[A-Za-z_]\w*)\s+as\s+(?P<var>[A-Za-z_]\w*)\s+do$', s)
        if m:
            body = []
            while True:
                bl = readline()
                if not bl:
                    continue
                if bl.strip() in ('endCase', 'endSelect'):
                    break
                body.append(bl)
            cases.append((m.group('chan'), m.group('var'), body))
            continue
        if s == 'default do':
            default_body = []
            while True:
                bl = readline()
                if not bl:
                    continue
                if bl.strip() in ('endCase', 'endSelect'):
                    break
                default_body.append(bl)
    if not cases:
        return True
    chan_ids = []
    chan_meta = []
    for chan_name, var_name, body in cases:
        if chan_name in variables and isinstance(variables[chan_name], int):
            chan_ids.append(variables[chan_name])
            chan_meta.append((variables[chan_name], var_name, body))
    if not chan_ids:
        if default_body:
            for bl in default_body:
                execute_line(bl, variables)
        return True
    ready_cid, val = go_interpreter.call('vyn_select', chan_ids, timeout=5)
    if ready_cid is None:
        if default_body:
            for bl in default_body:
                execute_line(bl, variables)
        return True
    for cid, var_name, body in chan_meta:
        if cid == ready_cid:
            variables[var_name] = val
            for bl in body:
                execute_line(bl, variables)
            break
    return True


def poll_goroutines():
    result = go_interpreter.call('vyn_goroutine_poll')
    if result is None:
        return
    status, fn, value = result
    if status == 'error':
        error.print_error_msg(f"Goroutine error: {value}")