# memory.py - Memory management system for Vyn
# Uses ctypes for real memory operations
import ctypes
import sys

# Memory pool: id -> (ctypes array, size)
_pool = {}
_next_id = [0]


def _new_id():
    _next_id[0] += 1
    return _next_id[0]


def alloc(size):
    """Allocate a block of `size` bytes. Returns a memory ID."""
    size = int(size)
    block = (ctypes.c_uint8 * size)()
    mid = _new_id()
    _pool[mid] = (block, size)
    return mid


def free(mid):
    """Free a memory block by ID."""
    mid = int(mid)
    if mid not in _pool:
        raise ValueError(f"Invalid memory ID: {mid}")
    del _pool[mid]
    return None


def read_byte(mid, index):
    """Read a byte from block at index."""
    mid = int(mid)
    index = int(index)
    if mid not in _pool:
        raise ValueError(f"Invalid memory ID: {mid}")
    block, size = _pool[mid]
    if index < 0 or index >= size:
        raise IndexError(f"Memory index {index} out of bounds (size={size})")
    return block[index]


def write_byte(mid, index, value):
    """Write a byte to block at index."""
    mid = int(mid)
    index = int(index)
    value = int(value) & 0xFF
    if mid not in _pool:
        raise ValueError(f"Invalid memory ID: {mid}")
    block, size = _pool[mid]
    if index < 0 or index >= size:
        raise IndexError(f"Memory index {index} out of bounds (size={size})")
    block[index] = value
    return value


def memsize(mid):
    """Return size of a memory block."""
    mid = int(mid)
    if mid not in _pool:
        raise ValueError(f"Invalid memory ID: {mid}")
    return _pool[mid][1]


def memzero(mid):
    """Zero out all bytes in a block."""
    mid = int(mid)
    if mid not in _pool:
        raise ValueError(f"Invalid memory ID: {mid}")
    block, size = _pool[mid]
    for i in range(size):
        block[i] = 0
    return None


def memcopy(src_id, dest_id, size):
    """Copy `size` bytes from src to dest."""
    src_id, dest_id, size = int(src_id), int(dest_id), int(size)
    if src_id not in _pool:
        raise ValueError(f"Invalid source memory ID: {src_id}")
    if dest_id not in _pool:
        raise ValueError(f"Invalid dest memory ID: {dest_id}")
    src_block, src_size = _pool[src_id]
    dest_block, dest_size = _pool[dest_id]
    copy_size = min(size, src_size, dest_size)
    for i in range(copy_size):
        dest_block[i] = src_block[i]
    return copy_size


def memdump(mid):
    """Print all bytes in a block as hex."""
    mid = int(mid)
    if mid not in _pool:
        raise ValueError(f"Invalid memory ID: {mid}")
    block, size = _pool[mid]
    row = []
    lines = []
    for i in range(size):
        row.append(f"{block[i]:02X}")
        if len(row) == 8:
            lines.append(" ".join(row))
            row = []
    if row:
        lines.append(" ".join(row))
    for i, l in enumerate(lines):
        print(f"  {i*8:04d}: {l}")
    return None


def sizeof(val):
    """Return size of a Python value in bytes."""
    return sys.getsizeof(val)


def memlist():
    """List all allocated blocks."""
    if not _pool:
        return "No allocations"
    result = []
    for mid, (_, size) in _pool.items():
        result.append(f"  mem#{mid} -> {size} bytes")
    return "\n".join(result)