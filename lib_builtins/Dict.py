def create(**kwargs):
    return dict(kwargs)

def get(dct, key, default=None):
    return dct.get(key, default)

def set_item(dct, key, value):
    dct[key] = value
    return dct

def remove(dct, key):
    if key in dct: del dct[key]
    return dct

def keys(dct): return list(dct.keys())
def values(dct): return list(dct.values())
def has_key(dct, key): return key in dct
def length(dct): return len(dct)
def clear(dct): dct.clear(); return dct
def copy(dct): return dct.copy()