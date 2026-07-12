"""
json - Python's json module exposed flatly.
After `import json`:
    json_str = dumps(obj)
    obj = loads(json_str)
"""
import json as _json

def dumps(obj, indent=None):
    if indent is None:
        return _json.dumps(obj)
    return _json.dumps(obj, indent=int(indent))

def loads(s):
    return _json.loads(s)

def dump(obj, filename):
    with open(filename, "w", encoding="utf-8") as f:
        _json.dump(obj, f)
    return filename

def load(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return _json.load(f)