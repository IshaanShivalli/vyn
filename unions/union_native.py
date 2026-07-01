import ctypes
import os
import sys

TYPE_CODES = {
    "int": 0,
    "float": 1,
    "char": 2,
    "bool": 3,
    "ptr": 4,
}

_struct_field_types = {}
_struct_union_store = {}

_lib = None


def _load_lib():
    global _lib
    if _lib is not None:
        return _lib

    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    if sys.platform.startswith("win"):
        candidates.extend(["libvynunion.dll", "libvynunion.so"])
    else:
        candidates.extend(["libvynunion.so", "libvynunion.dylib"])

    for name in candidates:
        path = os.path.join(base_dir, name)
        if not os.path.exists(path):
            continue
        try:
            lib = ctypes.CDLL(path)
            lib.vyn_union_define.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
            lib.vyn_union_define.restype = ctypes.c_int
            lib.vyn_union_exists.argtypes = [ctypes.c_char_p]
            lib.vyn_union_exists.restype = ctypes.c_int
            lib.vyn_union_sizeof.argtypes = [ctypes.c_char_p]
            lib.vyn_union_sizeof.restype = ctypes.c_int
            lib.vyn_union_alloc.argtypes = [ctypes.c_char_p]
            lib.vyn_union_alloc.restype = ctypes.c_int
            lib.vyn_union_free.argtypes = [ctypes.c_int]
            lib.vyn_union_free.restype = ctypes.c_int
            lib.vyn_union_instance_type.argtypes = [ctypes.c_int]
            lib.vyn_union_instance_type.restype = ctypes.c_char_p
            lib.vyn_union_get_field.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p]
            lib.vyn_union_get_field.restype = ctypes.c_int
            lib.vyn_union_set_field.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p]
            lib.vyn_union_set_field.restype = ctypes.c_int
            _lib = lib
            return lib
        except OSError:
            continue
    return None


def _native_available():
    return _load_lib() is not None


def define_union(name, fields):
    if name in _struct_field_types:
        raise ValueError(f"Union '{name}' is already defined")
    for fname, ftype in fields:
        if ftype not in TYPE_CODES:
            raise ValueError(f"Unknown field type '{ftype}' for field '{fname}'")
    if _native_available():
        lib = _load_lib()
        field_names = (ctypes.c_char_p * len(fields))()
        field_types = (ctypes.c_int * len(fields))()
        for idx, (fname, ftype) in enumerate(fields):
            field_names[idx] = fname.encode("utf-8")
            field_types[idx] = TYPE_CODES[ftype]
        rc = lib.vyn_union_define(name.encode("utf-8"), field_names, field_types, len(fields))
        if rc != 0:
            raise ValueError(f"Native union definition failed for '{name}'")
    _struct_field_types[name] = {fname: ftype for fname, ftype in fields}
    _struct_union_store[name] = {}
    return True


def union_exists(name):
    if _native_available():
        return bool(_load_lib().vyn_union_exists(name.encode("utf-8")))
    return name in _struct_field_types


def union_sizeof(name):
    if name not in _struct_field_types:
        raise ValueError(f"Unknown union '{name}'")
    if _native_available():
        return _load_lib().vyn_union_sizeof(name.encode("utf-8"))
    return max(1, len(_struct_field_types[name]))


def new_instance(union_name):
    if union_name not in _struct_field_types:
        raise ValueError(f"Union '{union_name}' is not defined")
    if _native_available():
        handle = _load_lib().vyn_union_alloc(union_name.encode("utf-8"))
        if handle <= 0:
            raise ValueError(f"Could not allocate native union '{union_name}'")
        return {"type": union_name, "values": {}, "handle": handle, "native": True}
    return {"type": union_name, "values": {}}


def free_instance(handle):
    if isinstance(handle, dict) and handle.get("native"):
        lib = _load_lib()
        if lib and handle.get("handle"):
            lib.vyn_union_free(handle["handle"])
    return None


def instance_type(handle):
    if isinstance(handle, dict) and handle.get("native"):
        lib = _load_lib()
        if lib and handle.get("handle"):
            value = lib.vyn_union_instance_type(handle["handle"])
            if value:
                return value.decode("utf-8")
    return handle["type"]


def _field_type(handle, field_name):
    type_name = instance_type(handle)
    types = _struct_field_types.get(type_name, {})
    if field_name not in types:
        raise ValueError(f"Union '{type_name}' has no field '{field_name}'")
    return types[field_name]


def get_field(handle, field_name):
    ftype = _field_type(handle, field_name)
    if field_name in handle["values"]:
        return handle["values"][field_name]
    if isinstance(handle, dict) and handle.get("native"):
        lib = _load_lib()
        if lib and handle.get("handle"):
            if ftype in ("int", "bool"):
                value = ctypes.c_long()
                if lib.vyn_union_get_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(value)) > 0:
                    return bool(value.value) if ftype == "bool" else int(value.value)
            elif ftype == "float":
                value = ctypes.c_double()
                if lib.vyn_union_get_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(value)) > 0:
                    return float(value.value)
            elif ftype == "char":
                value = ctypes.c_char()
                if lib.vyn_union_get_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(value)) > 0:
                    return value.value.decode("utf-8") if isinstance(value.value, bytes) else value.value
            elif ftype == "ptr":
                value = ctypes.c_void_p()
                if lib.vyn_union_get_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(value)) > 0:
                    return value.value
    if ftype in ("int", "bool"):
        return 0
    if ftype == "float":
        return 0.0
    return ""


def set_field(handle, field_name, value):
    ftype = _field_type(handle, field_name)
    if ftype == "int":
        value = int(value)
    elif ftype == "bool":
        value = bool(value)
    elif ftype == "float":
        value = float(value)
    handle["values"][field_name] = value
    if isinstance(handle, dict) and handle.get("native"):
        lib = _load_lib()
        if lib and handle.get("handle"):
            if ftype in ("int", "bool"):
                cast_value = ctypes.c_long(int(bool(value)) if ftype == "bool" else int(value))
                if lib.vyn_union_set_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(cast_value)) == 0:
                    return int(cast_value.value) if ftype == "int" else bool(cast_value.value)
            elif ftype == "float":
                cast_value = ctypes.c_double(float(value))
                if lib.vyn_union_set_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(cast_value)) == 0:
                    return float(cast_value.value)
            elif ftype == "char":
                cast_value = ctypes.c_char(str(value).encode("utf-8")[0])
                if lib.vyn_union_set_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(cast_value)) == 0:
                    return cast_value.value.decode("utf-8") if isinstance(cast_value.value, bytes) else cast_value.value
            elif ftype == "ptr":
                cast_value = ctypes.c_void_p(int(value))
                if lib.vyn_union_set_field(handle["handle"], field_name.encode("utf-8"), ctypes.byref(cast_value)) == 0:
                    return cast_value.value
    return value


def list_fields(union_name):
    if union_name not in _struct_field_types:
        raise ValueError(f"Union '{union_name}' is not defined")
    return dict(_struct_field_types[union_name])
