# struct_native.py - ctypes bridge to libvynstruct.so
# Loads the C struct/union engine and exposes clean Python functions

import ctypes
import os

_LIB_NAME = "libvynstruct.so"
_lib = None

TYPE_CODES = {
    "int": 0,
    "float": 1,
    "char": 2,
    "bool": 3,
    "ptr": 4,
}

# Tracks field types per struct name so we know how to pack/unpack values
# without needing to ask C every time. name -> {field_name: type_str}
_struct_field_types = {}
_struct_is_union = {}


def _find_lib(lib_name=_LIB_NAME):
    """Look for the .so next to this file first, then on the system path."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, lib_name)
    if os.path.exists(candidate):
        return candidate
    return lib_name  # fall back to ctypes' normal search


def _load_lib():
    global _lib
    if _lib is not None:
        return _lib

    path = _find_lib()
    try:
        lib = ctypes.CDLL(path)
    except OSError as exc:
        raise RuntimeError(
            f"Could not load {_LIB_NAME}: {exc}. "
            f"Did you compile it with `gcc -shared -fPIC -O2 -o {_LIB_NAME} vyn_struct.c`?"
        )

    # --- set argtypes/restype for every exported function ---
    lib.vyn_struct_define.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
    ]
    lib.vyn_struct_define.restype = ctypes.c_int

    lib.vyn_struct_alloc.argtypes = [ctypes.c_char_p]
    lib.vyn_struct_alloc.restype = ctypes.c_int

    lib.vyn_struct_free.argtypes = [ctypes.c_int]
    lib.vyn_struct_free.restype = ctypes.c_int

    lib.vyn_struct_get_int.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_long)]
    lib.vyn_struct_get_int.restype = ctypes.c_int

    lib.vyn_struct_set_int.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_long]
    lib.vyn_struct_set_int.restype = ctypes.c_int

    lib.vyn_struct_get_float.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_double)]
    lib.vyn_struct_get_float.restype = ctypes.c_int

    lib.vyn_struct_set_float.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_double]
    lib.vyn_struct_set_float.restype = ctypes.c_int

    lib.vyn_struct_instance_type.argtypes = [ctypes.c_int]
    lib.vyn_struct_instance_type.restype = ctypes.c_char_p

    lib.vyn_struct_exists.argtypes = [ctypes.c_char_p]
    lib.vyn_struct_exists.restype = ctypes.c_int

    lib.vyn_struct_sizeof.argtypes = [ctypes.c_char_p]
    lib.vyn_struct_sizeof.restype = ctypes.c_int

    _lib = lib
    return _lib


def define_struct(name, fields, is_union=False):
    """
    fields: list of (field_name, type_str) tuples, e.g. [("x", "int"), ("y", "float")]
    Returns True on success, raises ValueError on failure.
    """
    lib = _load_lib()

    if name in _struct_field_types:
        raise ValueError(f"Struct '{name}' is already defined")

    for fname, ftype in fields:
        if ftype not in TYPE_CODES:
            raise ValueError(f"Unknown field type '{ftype}' for field '{fname}'")

    count = len(fields)
    name_array = (ctypes.c_char_p * count)(*[f[0].encode("utf-8") for f in fields])
    type_array = (ctypes.c_int * count)(*[TYPE_CODES[f[1]] for f in fields])

    result = lib.vyn_struct_define(
        name.encode("utf-8"), name_array, type_array, count, 1 if is_union else 0
    )
    if result != 0:
        raise ValueError(f"Failed to define struct '{name}' (registry full or bad params)")

    _struct_field_types[name] = {fname: ftype for fname, ftype in fields}
    _struct_is_union[name] = is_union
    return True


def struct_exists(name):
    lib = _load_lib()
    return bool(lib.vyn_struct_exists(name.encode("utf-8")))


def struct_sizeof(name):
    lib = _load_lib()
    size = lib.vyn_struct_sizeof(name.encode("utf-8"))
    if size == -1:
        raise ValueError(f"Unknown struct '{name}'")
    return size


def new_instance(struct_name):
    """Allocate a new instance. Returns an integer handle."""
    lib = _load_lib()
    if struct_name not in _struct_field_types:
        raise ValueError(f"Struct '{struct_name}' is not defined")
    handle = lib.vyn_struct_alloc(struct_name.encode("utf-8"))
    if handle == -1:
        raise ValueError(f"Failed to allocate instance of '{struct_name}'")
    return handle


def free_instance(handle):
    lib = _load_lib()
    result = lib.vyn_struct_free(handle)
    if result != 0:
        raise ValueError(f"Invalid struct handle: {handle}")
    return None


def instance_type(handle):
    lib = _load_lib()
    name = lib.vyn_struct_instance_type(handle)
    if name is None:
        raise ValueError(f"Invalid struct handle: {handle}")
    return name.decode("utf-8")


def _field_type(handle, field_name):
    type_name = instance_type(handle)
    types = _struct_field_types.get(type_name, {})
    if field_name not in types:
        raise ValueError(f"Struct '{type_name}' has no field '{field_name}'")
    return types[field_name]


def get_field(handle, field_name):
    """Read a field's value, auto-converted to the right Python type."""
    lib = _load_lib()
    ftype = _field_type(handle, field_name)
    name_bytes = field_name.encode("utf-8")

    if ftype == "int" or ftype == "bool":
        out = ctypes.c_long()
        result = lib.vyn_struct_get_int(handle, name_bytes, ctypes.byref(out))
        if result != 0:
            raise ValueError(f"Failed to read field '{field_name}'")
        return bool(out.value) if ftype == "bool" else out.value
    elif ftype == "float":
        out = ctypes.c_double()
        result = lib.vyn_struct_get_float(handle, name_bytes, ctypes.byref(out))
        if result != 0:
            raise ValueError(f"Failed to read field '{field_name}'")
        return out.value
    else:
        raise ValueError(f"Unsupported field type '{ftype}' for read")


def set_field(handle, field_name, value):
    """Write a value to a field, auto-converted from the Python type."""
    lib = _load_lib()
    ftype = _field_type(handle, field_name)
    name_bytes = field_name.encode("utf-8")

    if ftype == "int":
        result = lib.vyn_struct_set_int(handle, name_bytes, int(value))
    elif ftype == "bool":
        result = lib.vyn_struct_set_int(handle, name_bytes, 1 if value else 0)
    elif ftype == "float":
        result = lib.vyn_struct_set_float(handle, name_bytes, float(value))
    else:
        raise ValueError(f"Unsupported field type '{ftype}' for write")

    if result != 0:
        raise ValueError(f"Failed to write field '{field_name}'")
    return value


def list_fields(struct_name):
    """Return field names + types for a struct, for debugging/printing."""
    if struct_name not in _struct_field_types:
        raise ValueError(f"Struct '{struct_name}' is not defined")
    return dict(_struct_field_types[struct_name])