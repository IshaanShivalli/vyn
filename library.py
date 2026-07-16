"""
Standard library loader for Vyn.
Loads built-ins from PL/lib_builtins and external libraries from ../vyn-lib/lib.
"""
import importlib.util
import os as _os


def _module_file_candidates(name):
    base = _os.path.dirname(__file__) if "__file__" in globals() else "."
    parent = _os.path.dirname(base)
    return [
        _os.path.join(parent, "vyn-lib", "lib", f"{name}.py"),
        _os.path.join(base, "lib", f"{name}.py"),
        _os.path.join(base, "lib_builtins", f"{name}.py"),
    ]


def _load_lib_module(name):
    """Try to load a module from lib/ folder"""
    import sys
    import importlib

    path = None
    for candidate in _module_file_candidates(name):
        if _os.path.exists(candidate):
            path = candidate
            break

    if path is None:
        base = _os.path.dirname(__file__) if "__file__" in globals() else "."
        package_path = _os.path.join(base, name, "__init__.py")
        if _os.path.exists(package_path):
            path = package_path
            spec = importlib.util.spec_from_file_location(name, path)
        else:
            try:
                if name in sys.modules:
                    return sys.modules[name]
                return importlib.import_module(name)
            except (ImportError, ModuleNotFoundError):
                raise ImportError(f"Stdlib not found: {name}")
    else:
        spec = importlib.util.spec_from_file_location(f"lib.{name}", path)

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _CallableModuleProxy:
    def __init__(self, module, call_name):
        self._module = module
        self._call = getattr(module, call_name)
        self.__file__ = getattr(module, "__file__", None)

    def __call__(self, *args):
        return self._call(*args)

    def __getattr__(self, name):
        return getattr(self._module, name)


def get_stdlib_functions():
    """Automatically discover and load all modules from lib/ folder"""
    libs = {}
    
    base = _os.path.dirname(__file__) if "__file__" in globals() else "."
    parent = _os.path.dirname(base)
    lib_dirs = [
        _os.path.join(parent, "vyn-lib", "lib"),
        _os.path.join(base, "lib"),
        _os.path.join(base, "lib_builtins"),
    ]

    for lib_dir in lib_dirs:
        if not _os.path.exists(lib_dir):
            continue
        for filename in _os.listdir(lib_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                if module_name in libs:
                    continue
                try:
                    mod = _load_lib_module(module_name)
                    public = {
                        k: v for k, v in mod.__dict__.items()
                        if not k.startswith("_") and not k.startswith("__")
                    }
                    libs[module_name] = public
                except Exception as e:
                    print(f"Warning: Could not load {module_name} -> {e}")
                    libs[module_name] = {}

    return libs


def register_library(lib_name, variables):
    """Register a standard library module and expose its public symbols."""
    try:
        module = _load_lib_module(lib_name)
    except ImportError:
        return False

    public = {
        k: v for k, v in module.__dict__.items()
        if not k.startswith("_") and not k.startswith("__")
    }
    variables.update(public)
    if lib_name in public and callable(public[lib_name]):
        module_value = _CallableModuleProxy(module, lib_name)
    else:
        module_value = module
    variables[lib_name] = module_value
    variables[lib_name[:1].upper() + lib_name[1:]] = module_value
    return True
