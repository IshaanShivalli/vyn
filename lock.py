# lock.py - Variable locking implementation
# Locked variables cannot be modified within a lock block

# Set of currently locked variable names
_locked = set()

# Lock groups: group_name -> set of variables
_lock_groups = {}


def lock(name):
    """Lock a single variable."""
    _locked.add(name)


def unlock(name):
    """Unlock a single variable."""
    _locked.discard(name)


def is_locked(name):
    """Returns True if variable is currently locked."""
    return name in _locked


def lock_group(group_name, names):
    """Lock multiple variables under a group name."""
    _lock_groups[group_name] = set(names)
    for name in names:
        _locked.add(name)


def unlock_group(group_name):
    """Unlock all variables in a group."""
    names = _lock_groups.pop(group_name, set())
    for name in names:
        # Only unlock if not locked by another group
        still_locked = any(name in g for g in _lock_groups.values())
        if not still_locked:
            _locked.discard(name)


def list_locked():
    """Return all currently locked variable names."""
    return list(_locked)


def clear_all():
    """Unlock everything."""
    _locked.clear()
    _lock_groups.clear()