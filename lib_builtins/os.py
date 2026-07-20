"""
os library for Vyn -- filesystem/OS helpers beyond what dependency.py
already registers unconditionally (open_file/read_file/read_line/
write_file/close_file/list_dir/exists). Gated behind `import os` since
these are more powerful (delete, move, env vars) and shouldn't be
available without an explicit opt-in.

import os
"""

import os as _os
import shutil as _shutil


def mkdir(path):
    _os.makedirs(path, exist_ok=True)
    return None


def rmdir(path):
    _shutil.rmtree(path)
    return None


def remove_file(path):
    _os.remove(path)
    return None


def copy_file(src, dst):
    _shutil.copy2(src, dst)
    return None


def move_file(src, dst):
    _shutil.move(src, dst)
    return None


def path_join(*parts):
    return _os.path.join(*parts)


def path_basename(path):
    return _os.path.basename(path)


def path_dirname(path):
    return _os.path.dirname(path)


def path_extension(path):
    return _os.path.splitext(path)[1]


def is_file(path):
    return _os.path.isfile(path)


def is_dir(path):
    return _os.path.isdir(path)


def file_size(path):
    return _os.path.getsize(path)


def cwd():
    return _os.getcwd()


def chdir(path):
    _os.chdir(path)
    return None


def env_get(name, default=None):
    return _os.environ.get(name, default)


def env_set(name, value):
    _os.environ[name] = str(value)
    return None


def walk(path):
    """List of every file path under `path`, recursively."""
    found = []
    for root, _dirs, files in _os.walk(path):
        for f in files:
            found.append(_os.path.join(root, f))
    return found