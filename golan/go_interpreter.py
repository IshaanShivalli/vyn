import os
import re
import go_runtime

EXPORT_RE = re.compile(r'//export\s+(\w+)')
FUNC_RE = re.compile(r'^func\s+(\w+)\s*\(', re.MULTILINE)

_go_dir = os.path.dirname(os.path.abspath(__file__))

_loaded_files = {}
_export_map = {}

_RUNTIME_MAP = {
    'vyn_defer_new_stack':  go_runtime.vyn_defer_new_stack,
    'vyn_defer_push':       go_runtime.vyn_defer_push,
    'vyn_defer_run':        go_runtime.vyn_defer_run,
    'vyn_defer_pop_call':   go_runtime.vyn_defer_pop_call,
    'vyn_defer_drop_stack': go_runtime.vyn_defer_drop_stack,
    'vyn_ret_new':          go_runtime.vyn_ret_new,
    'vyn_ret_push_int':     go_runtime.vyn_ret_push_int,
    'vyn_ret_push_float':   go_runtime.vyn_ret_push_float,
    'vyn_ret_push_str':     go_runtime.vyn_ret_push_str,
    'vyn_ret_push_bool':    go_runtime.vyn_ret_push_bool,
    'vyn_ret_count':        go_runtime.vyn_ret_count,
    'vyn_ret_get_json':     go_runtime.vyn_ret_get_json,
    'vyn_ret_free':         go_runtime.vyn_ret_free,
    'vyn_ret_unpack':       go_runtime.vyn_ret_unpack,
    'vyn_chan_new':          go_runtime.vyn_chan_new,
    'vyn_chan_send_int':     go_runtime.vyn_chan_send_int,
    'vyn_chan_send_float':   go_runtime.vyn_chan_send_float,
    'vyn_chan_send_str':     go_runtime.vyn_chan_send_str,
    'vyn_chan_recv':         go_runtime.vyn_chan_recv,
    'vyn_chan_recv_json':    go_runtime.vyn_chan_recv_json,
    'vyn_chan_close':        go_runtime.vyn_chan_close,
    'vyn_chan_drop':         go_runtime.vyn_chan_drop,
    'vyn_goroutine_spawn':   go_runtime.vyn_goroutine_spawn,
    'vyn_goroutine_poll':    go_runtime.vyn_goroutine_poll,
    'vyn_select':            go_runtime.vyn_select,
}


def load_go_file(filename):
    path = os.path.join(_go_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Go file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()

    lines = source.splitlines()
    exports = []
    for i, line in enumerate(lines):
        m = EXPORT_RE.match(line.strip())
        if m:
            exports.append(m.group(1))

    bound = {}
    for name in exports:
        if name in _RUNTIME_MAP:
            bound[name] = _RUNTIME_MAP[name]
        else:
            bound[name] = _make_stub(name)

    _loaded_files[filename] = {
        'source': source,
        'exports': exports,
        'bound': bound
    }

    for name, fn in bound.items():
        _export_map[name] = fn

    return bound


def _make_stub(name):
    def stub(*args, **kwargs):
        raise NotImplementedError(f"Go export '{name}' has no Python implementation")
    stub.__name__ = name
    return stub


def call(fn_name, *args):
    if fn_name not in _export_map:
        raise ValueError(f"Unknown Go export: '{fn_name}'")
    return _export_map[fn_name](*args)


def get(fn_name):
    if fn_name not in _export_map:
        raise ValueError(f"Unknown Go export: '{fn_name}'")
    return _export_map[fn_name]


def load_all():
    for fname in ('vyn_defer.go', 'vyn_returns.go', 'vyn_concurrency.go'):
        load_go_file(fname)


def list_exports():
    return list(_export_map.keys())


def is_loaded(fn_name):
    return fn_name in _export_map