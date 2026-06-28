# ghost.py - Ghost variable implementation
# Ghost variables expire after being accessed once

# Stores ghost variable names and their values
_ghost_store = {}
_ghost_accessed = set()


def register_ghost(name, value):
    """Register a ghost variable with its value."""
    _ghost_store[name] = value
    _ghost_accessed.discard(name)


def is_ghost(name):
    """Returns True if name is a registered ghost variable."""
    return name in _ghost_store


def resolve_ghost(name):
    """
    Return the ghost variable value.
    Marks it as accessed — next access raises an error.
    """
    if name in _ghost_accessed:
        raise ValueError(f"Ghost variable '{name}' has expired")
    value = _ghost_store[name]
    _ghost_accessed.add(name)
    return value


def drop_ghost(name):
    """Manually expire a ghost variable."""
    _ghost_store.pop(name, None)
    _ghost_accessed.discard(name)


def is_expired(name):
    """Returns True if ghost has been accessed and expired."""
    return name in _ghost_accessed


def list_ghosts():
    """Return all ghost variable names and their status."""
    result = {}
    for name in _ghost_store:
        result[name] = 'expired' if name in _ghost_accessed else 'alive'
    return result


def clear_all():
    """Remove all ghost variables."""
    _ghost_store.clear()
    _ghost_accessed.clear()