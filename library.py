"""
Standard library loader for Vyn.
Automatically loads ALL .py files from the lib/ folder.
No need to manually add module names anymore.
"""
import importlib.util
import os as _os


def _load_lib_module(name):
    """Try to load a module from lib/ folder"""
    import sys
    import importlib

    # Try direct import first (for root-level packages like rust, errExpr)
    try:
        if name in sys.modules:
            return sys.modules[name]
        return importlib.import_module(name)
    except (ImportError, ModuleNotFoundError):
        pass

    # Try as package import first
    try:
        return importlib.import_module(f".lib.{name}", package="attachments")
    except (ImportError, ModuleNotFoundError):
        pass

    # Fallback: load directly from file
    base = _os.path.dirname(__file__) if "__file__" in globals() else "."
    path = _os.path.join(base, "lib", f"{name}.py")

    if not _os.path.exists(path):
        package_path = _os.path.join(base, name, "__init__.py")
        if _os.path.exists(package_path):
            path = package_path
            spec = importlib.util.spec_from_file_location(name, path)
        else:
            raise ImportError(f"Stdlib not found: {path}")
    else:
        spec = importlib.util.spec_from_file_location(f"lib.{name}", path)

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_stdlib_functions():
    """Automatically discover and load all modules from lib/ folder"""
    libs = {}
    
    base = _os.path.dirname(__file__) if "__file__" in globals() else "."
    lib_dir = _os.path.join(base, "lib")

    if not _os.path.exists(lib_dir):
        return libs

    # Scan all .py files in lib/ folder
    for filename in _os.listdir(lib_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]  # remove .py extension
            
            try:
                mod = _load_lib_module(module_name)
                # Get only public functions/variables
                public = {
                    k: v for k, v in mod.__dict__.items()
                    if not k.startswith("_") and not k.startswith("__")
                }
                libs[module_name] = public
            except Exception as e:
                # Skip modules that fail to load
                print(f"Warning: Could not load {module_name} -> {e}")
                libs[module_name] = {}

    return libs


def register_library(lib_name, variables):
    """Register a standard library module and expose its public symbols."""
    try:
        module = _load_lib_module(lib_name)
    except ImportError:
        return False

    variables[lib_name] = module
    public = {
        k: v for k, v in module.__dict__.items()
        if not k.startswith("_") and not k.startswith("__")
    }
    variables.update(public)
    return True