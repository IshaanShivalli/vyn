import re
import builtins
import library
import os

IMPORT_RE = re.compile(r'^import\s+(?P<module>[\w./\\-]+?)(?:\.vyn)?\s*$')

# Global stack to hold file lines during nested imports/executions
_file_stack = []


def _file_input_wrapper(prompt=""):
    global _file_stack
    if not _file_stack:
        return builtins.input(prompt)

    queue, index_ref = _file_stack[-1]
    if index_ref[0] >= len(queue):
        raise EOFError()

    line = queue[index_ref[0]]
    index_ref[0] += 1
    return line


def parse_import(line):
    m = IMPORT_RE.match(line.strip())
    if not m:
        return None
    return m.group('module')


def is_stdlib_import(module_name):
    """Check if this is a standard library (from lib/ folder)"""
    # Remove lib/ prefix if present
    name = module_name
    if name.startswith('lib/'):
        name = name[4:]

    # Check if corresponding file exists in lib/
    base = os.path.dirname(__file__) if "__file__" in globals() else "."
    lib_path = os.path.join(base, "lib", f"{name}.py")
    
    return os.path.exists(lib_path)


def get_stdlib_name(module_name):
    """Extract clean name from lib/name or bare name"""
    if module_name.startswith('lib/'):
        return module_name[4:]
    return module_name


def resolve_vyn_filename(name):
    base, ext = os.path.splitext(name)
    if ext:
        if ext.lower() != '.vyn':
            return None
        return name
    return f"{name}.vyn"


def file_exists_vyn(name):
    filename = resolve_vyn_filename(name)
    return filename is not None and os.path.exists(filename)


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
    global _file_stack

    with open(path, 'r', encoding='utf-8-sig') as handle:
        all_lines = [line.rstrip('\n') for line in handle.readlines()]

    queue = [line for line in all_lines if line.strip() and not line.strip().startswith('#')]
    index_ref = [0]

    _file_stack.append((queue, index_ref))

    original_input = builtins.input
    builtins.input = _file_input_wrapper

    try:
        while True:
            if index_ref[0] >= len(queue):
                break
            line = queue[index_ref[0]]
            index_ref[0] += 1
            if line.strip():
                execute_line(line, variables)
    except EOFError:
        pass
    finally:
        if _file_stack:
            _file_stack.pop()
        if not _file_stack:
            builtins.input = original_input


def register_io_functions(variables):
    variables['open_file'] = open_file
    variables['read_file'] = read_file
    variables['read_line'] = read_line
    variables['write_file'] = write_file
    variables['close_file'] = close_file
    variables['list_dir'] = list_dir
    variables['exists'] = exists