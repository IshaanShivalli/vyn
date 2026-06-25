from importlib import import_module

global_vars = import_module(f"{__package__}.global")
from . import local

__all__ = ['global_vars', 'local']
