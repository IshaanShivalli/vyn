# lazy.py - Lazy variable implementation
# Lazy variables are only evaluated when first accessed

import re

# Stores unevaluated expressions: name -> expr string
_lazy_store = {}
_lazy_evaluated = set()  # tracks which have been computed


def register_lazy(name, expr):
    """Register a lazy variable with its expression."""
    _lazy_store[name] = expr
    if name in _lazy_evaluated:
        _lazy_evaluated.discard(name)


def is_lazy(name):
    """Returns True if name is a registered lazy variable."""
    return name in _lazy_store


def resolve_lazy(name, variables, eval_expression):
    """
    Evaluate the lazy variable for the first time and cache it.
    Subsequent accesses return the cached value.
    """
    if name in _lazy_evaluated:
        return variables[name]

    expr = _lazy_store[name]
    try:
        value = eval_expression(expr, variables)
        variables[name] = value
        _lazy_evaluated.add(name)
        return value
    except Exception as exc:
        raise ValueError(f"Lazy variable '{name}' failed to evaluate: {exc}")


def drop_lazy(name):
    """Remove a lazy variable — forces re-evaluation next access."""
    _lazy_store.pop(name, None)
    _lazy_evaluated.discard(name)


def reset_lazy(name):
    """Force re-evaluation next time the lazy var is accessed."""
    _lazy_evaluated.discard(name)


def list_lazy():
    """Return all registered lazy variable names."""
    return list(_lazy_store.keys())