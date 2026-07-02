import re
import builtins
import library
import os

IMPORT_RE = re.compile(r'^import\s+(?P<module>[\w./\\-]+?)(?:\.(?:vyn|go))?\s*$')

# Search path for .vyn files. Current directory is always checked first,
# then each entry in VYN_PATH in order.
VYN_PATH = ['packages']

_file_lines_queue = None
_file_lines_index = [0]


def _file_input_wrapper(prompt=""):
    global _file_lines_queue, _file_lines_index
    if _file_lines_queue is None:
        return builtins.input(prompt)
    if _file_lines_index[0] >= len(_file_lines_queue):
        raise EOFError()
    line = _file_lines_queue[_file_lines_index[0]]
    _file_lines_index[0] += 1
    return line


def parse_import(line):
    m = IMPORT_RE.match(line.strip())
    if not m:
        return None
    return m.group('module')


def is_stdlib_import(module_name):
    """Return True if module_name resolves to a stdlib file or package."""
    name = get_stdlib_name(module_name)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lib_dir = os.path.join(base_dir, "lib")
    if os.path.exists(os.path.join(lib_dir, f"{name}.py")):
        return True
    return os.path.exists(os.path.join(base_dir, name, "__init__.py"))


def get_stdlib_name(module_name):
    """Strip lib/ prefix if present."""
    if module_name.startswith('lib/'):
        return module_name[4:]
    return module_name


def resolve_vyn_filename(name):
    """
    Resolve a module name to an existing .vyn or .go file path.
    Search order:
      1. As-is (absolute path or relative to cwd)
      2. Each directory in VYN_PATH
    Returns the resolved path string, or None if not found.
    """
    # Determine the bare filename to look for
    base, ext = os.path.splitext(name)
    if ext:
        if ext.lower() not in ('.vyn', '.go'):
            return None
        filename = name
    else:
        # try .vyn first, then .go
        if os.path.exists(f"{name}.vyn"):
            return f"{name}.vyn"
        if os.path.exists(f"{name}.go"):
            return f"{name}.go"
        filename = f"{name}.vyn"

    # 1. Current directory / absolute
    if os.path.exists(filename):
        return filename

    # 2. VYN_PATH entries
    for folder in VYN_PATH:
        candidate = os.path.join(folder, filename)
        if os.path.exists(candidate):
            return candidate
        if ext == '':
            if os.path.exists(os.path.join(folder, f"{name}.go")):
                return os.path.join(folder, f"{name}.go")

    return None


def file_exists_vyn(name):
    return resolve_vyn_filename(name) is not None


def open_file(path, mode='r'):
    return open(path, mode)


def read_file(handle, size=-1):
    return handle.read(size)


def read_line(handle):
    return handle.readline()


def write_file(handle, data):
    text = str(data)
    written = handle.write(text)
    handle.flush()
    return written


def close_file(handle):
    handle.close()
    return None


def list_dir(path='.'):
    return os.listdir(path)


def exists(path):
    return os.path.exists(path)


def load_vyn_file(path, execute_line, variables):
    global _file_lines_queue, _file_lines_index

    with open(path, 'r', encoding='utf-8-sig') as handle:
        all_lines = [line.rstrip('\n') for line in handle.readlines()]

    if path.lower().endswith('.go'):
        import importlib.util as _ilu
        go_syntax_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'golan', 'syntax.py')
        spec = _ilu.spec_from_file_location('golan_syntax', go_syntax_path)
        go_syntax = _ilu.module_from_spec(spec)
        spec.loader.exec_module(go_syntax)
        all_lines = go_syntax.preprocess_go_source(all_lines)
        # Expose small file/regex helpers to .go files without using a package import.
        variables.setdefault('glob', go_syntax.glob)
        variables.setdefault('recursive_glob', go_syntax.recursive_glob)
        variables.setdefault('filepath_match', go_syntax.filepath_match)
        variables.setdefault('filepathMatch', go_syntax.filepath_match)
        variables.setdefault('regex_match', go_syntax.regex_match)
        variables.setdefault('regexMatch', go_syntax.regex_match)
        variables.setdefault('regex_search', go_syntax.regex_search)
        variables.setdefault('regexSearch', go_syntax.regex_search)
        variables.setdefault('regex_findall', go_syntax.regex_findall)
        variables.setdefault('regexFindAll', go_syntax.regex_findall)

    previous_queue = _file_lines_queue
    previous_index = _file_lines_index[0]
    _file_lines_queue = [
        line for line in all_lines
        if line.strip() and not line.strip().startswith('#')
    ]
    _file_lines_index[0] = 0

    original_input = builtins.input
    builtins.input = _file_input_wrapper

    try:
        while True:
            if _file_lines_index[0] >= len(_file_lines_queue):
                break
            line = _file_lines_queue[_file_lines_index[0]]
            _file_lines_index[0] += 1
            if line.strip():
                execute_line(line, variables)
    except EOFError:
        pass
    finally:
        builtins.input = original_input
        _file_lines_queue = previous_queue
        _file_lines_index[0] = previous_index


def register_io_functions(variables):
    variables['open_file'] = open_file
    variables['read_file'] = read_file
    variables['read_line'] = read_line
    variables['write_file'] = write_file
    variables['close_file'] = close_file
    variables['list_dir'] = list_dir
    variables['exists'] = exists
